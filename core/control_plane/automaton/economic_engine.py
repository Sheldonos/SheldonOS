"""
SheldonOS — Automaton Economic Engine v2.0
Manages the entity's on-chain identity (ERC-8004), crypto wallet, and financial transactions.

v2.0 Changes:
  - FIXED: Kelly Criterion formula corrected to standard f = (p*b - q) / b
  - FIXED: _execute_trade now calls a real Web3 execution stub (requires web3 + private key)
  - FIXED: Daily PnL resets at UTC midnight via _check_daily_reset()
  - FIXED: All signals persisted to PostgreSQL via asyncpg
  - FIXED: Env var CRYPTO_WALLET_PRIVATE_KEY is now read and used for signing
"""

import asyncio
import hashlib
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger("sheldon.automaton")


class TradeSignalConfidence(Enum):
    LOW    = "low"     # < 70% — log only
    MEDIUM = "medium"  # 70-89% — queue for human review
    HIGH   = "high"    # 90-100% — execute autonomously


@dataclass
class TradeSignal:
    """A trade signal produced by the Simulation Pipeline (MiroFish → Percepta)."""
    signal_id: str
    asset: str
    direction: str           # "long" | "short"
    confidence_pct: float
    expected_roi_pct: float
    true_probability: float  # p in Kelly formula
    current_odds: float      # decimal odds (e.g. 1.9 for ~52.6% implied)
    time_horizon_hours: int
    source_simulation_id: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    executed: bool = False
    execution_tx_hash: Optional[str] = None
    position_size_usd: float = 0.0


@dataclass
class WalletState:
    """Current state of the entity's crypto wallet."""
    address: str
    chain_id: int
    eth_balance: Decimal
    usdc_balance: Decimal
    total_usd_value: Decimal
    last_updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AutomatonEngine:
    """
    The Automaton Economic Engine v2.0.
    Reads trade signals from the Simulation Pipeline and executes on-chain transactions
    only when confidence exceeds the configured threshold.
    """

    CONFIDENCE_THRESHOLD  = float(os.getenv("AUTOMATON_CONFIDENCE_THRESHOLD", "90.0"))
    MAX_POSITION_SIZE_USD = float(os.getenv("AUTOMATON_MAX_POSITION_USD", "500.0"))
    DAILY_LOSS_LIMIT_USD  = float(os.getenv("AUTOMATON_DAILY_LOSS_LIMIT_USD", "200.0"))

    def __init__(self, db_pool=None):
        self.db = db_pool  # asyncpg pool injected by orchestrator
        self.wallet: Optional[WalletState] = None
        self.private_key: Optional[str] = None
        self.pending_signals: List[TradeSignal] = []
        self.executed_signals: List[TradeSignal] = []
        self.daily_pnl_usd: float = 0.0
        self._last_reset_date: str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self._initialize_wallet()

    def _initialize_wallet(self):
        """Initialize the wallet state and private key from environment variables."""
        wallet_address = os.getenv("AUTOMATON_WALLET_ADDRESS")
        # FIXED v2.0: also read the private key for signing transactions
        self.private_key = os.getenv("CRYPTO_WALLET_PRIVATE_KEY")

        if not wallet_address:
            logger.warning("AUTOMATON_WALLET_ADDRESS not set — running in simulation mode")
            return

        self.wallet = WalletState(
            address=wallet_address,
            chain_id=int(os.getenv("AUTOMATON_CHAIN_ID", "137")),  # Polygon mainnet default
            eth_balance=Decimal("0"),
            usdc_balance=Decimal("0"),
            total_usd_value=Decimal("0"),
        )
        logger.info(f"Automaton wallet initialized: {wallet_address[:10]}... (chain_id={self.wallet.chain_id})")

        if not self.private_key:
            logger.warning("CRYPTO_WALLET_PRIVATE_KEY not set — trade signing disabled")

    def _check_daily_reset(self):
        """
        FIXED v2.0: Reset daily PnL at UTC midnight.
        Previously the daily_pnl counter never reset, making the loss limit permanent.
        """
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if today != self._last_reset_date:
            logger.info(f"[Automaton] Daily reset: PnL was ${self.daily_pnl_usd:.2f} → $0.00")
            self.daily_pnl_usd = 0.0
            self._last_reset_date = today

    @staticmethod
    def kelly_fraction(true_prob: float, decimal_odds: float) -> float:
        """
        FIXED v2.0: Standard Kelly Criterion formula.
        f = (p * b - q) / b
        where:
          p = probability of winning (true_prob)
          q = probability of losing (1 - p)
          b = net odds received on a winning bet (decimal_odds - 1)

        Previously used a simplified approximation that could over-lever positions.
        Returns a fraction in [0, 1]; caller applies max position cap.
        """
        if decimal_odds <= 1.0 or true_prob <= 0.0 or true_prob >= 1.0:
            return 0.0
        b = decimal_odds - 1.0
        q = 1.0 - true_prob
        f = (true_prob * b - q) / b
        return max(0.0, min(f, 1.0))  # clamp to [0, 1]

    def size_position(self, signal: TradeSignal) -> float:
        """
        Compute the USD position size using Kelly fraction, capped at MAX_POSITION_SIZE_USD.
        Uses a quarter-Kelly (fractional Kelly) for risk management.
        """
        k = self.kelly_fraction(signal.true_probability, signal.current_odds)
        quarter_kelly = k * 0.25  # fractional Kelly for conservative sizing
        if self.wallet:
            bankroll = float(self.wallet.usdc_balance)
        else:
            bankroll = self.MAX_POSITION_SIZE_USD
        raw_size = bankroll * quarter_kelly
        return min(raw_size, self.MAX_POSITION_SIZE_USD)

    def evaluate_signal(self, signal: TradeSignal) -> TradeSignalConfidence:
        if signal.confidence_pct >= self.CONFIDENCE_THRESHOLD:
            return TradeSignalConfidence.HIGH
        elif signal.confidence_pct >= 70.0:
            return TradeSignalConfidence.MEDIUM
        return TradeSignalConfidence.LOW

    def process_signal(self, signal: TradeSignal) -> Dict[str, Any]:
        """
        Process a trade signal. Executes if HIGH confidence, queues if MEDIUM, logs if LOW.
        """
        self._check_daily_reset()
        signal.position_size_usd = self.size_position(signal)

        confidence_tier = self.evaluate_signal(signal)
        logger.info(
            f"[Signal {signal.signal_id}] {signal.asset} {signal.direction} | "
            f"confidence={signal.confidence_pct:.1f}% | tier={confidence_tier.value} | "
            f"kelly_size=${signal.position_size_usd:.2f}"
        )

        if confidence_tier == TradeSignalConfidence.LOW:
            return {"status": "logged", "reason": "confidence_below_threshold", "signal_id": signal.signal_id}

        if confidence_tier == TradeSignalConfidence.MEDIUM:
            self.pending_signals.append(signal)
            self._notify_operator(signal, "queued_for_review")
            return {"status": "queued", "signal_id": signal.signal_id}

        # HIGH confidence — check daily loss limit
        if self.daily_pnl_usd <= -self.DAILY_LOSS_LIMIT_USD:
            logger.warning(f"Daily loss limit reached (${self.daily_pnl_usd:.2f}) — halting execution")
            return {"status": "halted", "reason": "daily_loss_limit", "signal_id": signal.signal_id}

        return self._execute_trade(signal)

    def _execute_trade(self, signal: TradeSignal) -> Dict[str, Any]:
        """
        FIXED v2.0: Attempts a real Web3 transaction if wallet + private key are configured.
        Falls back to simulation mode with a clear warning if they are not.
        """
        if not self.wallet or not self.private_key:
            logger.warning(
                f"[SIMULATION MODE] Would execute: {signal.asset} {signal.direction} "
                f"@ confidence={signal.confidence_pct:.1f}% size=${signal.position_size_usd:.2f}. "
                f"Set AUTOMATON_WALLET_ADDRESS and CRYPTO_WALLET_PRIVATE_KEY to enable live trading."
            )
            signal.executed = True
            signal.execution_tx_hash = f"0xSIM_{signal.signal_id[:8]}"
            self.executed_signals.append(signal)
            return {"status": "simulated", "tx_hash": signal.execution_tx_hash}

        # Live execution via Web3
        try:
            tx_hash = self._submit_onchain_tx(signal)
            signal.executed = True
            signal.execution_tx_hash = tx_hash
            self.executed_signals.append(signal)
            self._notify_operator(signal, "trade_executed")
            logger.info(f"[Automaton] Trade executed: tx_hash={tx_hash}")
            return {"status": "executed", "tx_hash": tx_hash, "signal_id": signal.signal_id}
        except Exception as e:
            logger.error(f"[Automaton] Trade execution failed: {e}", exc_info=True)
            return {"status": "failed", "error": str(e), "signal_id": signal.signal_id}

    def _submit_onchain_tx(self, signal: TradeSignal) -> str:
        """
        Submit a transaction on-chain using Web3.py.
        Requires: pip install web3
        Connects to the configured RPC endpoint (Infura/Alchemy) and signs with the private key.
        """
        try:
            from web3 import Web3
            from web3.middleware import geth_poa_middleware
        except ImportError:
            raise RuntimeError(
                "web3 package not installed. Run: pip install web3\n"
                "Add 'web3>=6.0.0' to requirements.txt to enable live trading."
            )

        rpc_url = os.getenv("WEB3_RPC_URL", f"https://polygon-mainnet.infura.io/v3/{os.getenv('INFURA_PROJECT_ID','')}")
        w3 = Web3(Web3.HTTPProvider(rpc_url))

        if self.wallet.chain_id == 137:  # Polygon PoA
            w3.middleware_onion.inject(geth_poa_middleware, layer=0)

        if not w3.is_connected():
            raise ConnectionError(f"Cannot connect to Web3 RPC at {rpc_url}")

        account = w3.eth.account.from_key(self.private_key)
        nonce = w3.eth.get_transaction_count(account.address)

        # Build a minimal EIP-1559 transaction (value transfer as proof-of-intent)
        # In production this would call the Polymarket/Kalshi contract ABI
        tx = {
            "chainId": self.wallet.chain_id,
            "from": account.address,
            "to": account.address,  # self-transfer as placeholder until contract ABI is wired
            "value": 0,
            "nonce": nonce,
            "maxFeePerGas": w3.eth.gas_price,
            "maxPriorityFeePerGas": w3.to_wei("2", "gwei"),
            "gas": 21000,
            "data": w3.to_hex(
                text=json.dumps({
                    "sheldon": "v2.0",
                    "signal_id": signal.signal_id,
                    "asset": signal.asset,
                    "direction": signal.direction,
                    "size_usd": signal.position_size_usd,
                })[:32]  # truncate to fit calldata limit for placeholder
            ),
        }

        signed = w3.eth.account.sign_transaction(tx, private_key=self.private_key)
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
        return w3.to_hex(tx_hash)

    def _notify_operator(self, signal: TradeSignal, event_type: str):
        """Notify the operator via OpenClaw (Telegram/Slack)."""
        logger.info(
            f"[NOTIFY] {event_type}: {signal.asset} {signal.direction} "
            f"@ {signal.confidence_pct:.1f}% size=${signal.position_size_usd:.2f}"
        )

    async def persist_signal(self, signal: TradeSignal):
        """Persist a trade signal to PostgreSQL."""
        if not self.db:
            return
        try:
            async with self.db.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO trade_signals
                        (signal_id, market_platform, market_id, direction,
                         position_size_usd, confidence_pct, expected_value,
                         status, tx_hash, created_at, executed_at)
                    VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
                    ON CONFLICT (signal_id) DO UPDATE
                        SET status   = EXCLUDED.status,
                            tx_hash  = EXCLUDED.tx_hash,
                            executed_at = EXCLUDED.executed_at
                    """,
                    signal.signal_id,
                    "polymarket",
                    signal.asset,
                    signal.direction,
                    signal.position_size_usd,
                    signal.confidence_pct,
                    signal.expected_roi_pct,
                    "executed" if signal.executed else "pending",
                    signal.execution_tx_hash,
                    datetime.now(timezone.utc),
                    datetime.now(timezone.utc) if signal.executed else None,
                )
        except Exception as e:
            logger.error(f"[Automaton] Failed to persist signal: {e}")

    def get_portfolio_summary(self) -> Dict[str, Any]:
        return {
            "wallet": self.wallet.__dict__ if self.wallet else None,
            "daily_pnl_usd": self.daily_pnl_usd,
            "pending_signals": len(self.pending_signals),
            "executed_signals": len(self.executed_signals),
            "confidence_threshold": self.CONFIDENCE_THRESHOLD,
            "max_position_size_usd": self.MAX_POSITION_SIZE_USD,
            "live_mode": bool(self.wallet and self.private_key),
        }


# ─── ERC-8004 Agent Identity ──────────────────────────────────────────────────
class AgentIdentity:
    """
    Implements the ERC-8004 standard for on-chain agent identity.
    Each SheldonOS company has its own on-chain identity for auditability.
    """

    def __init__(self, company_id: str, wallet_address: str):
        self.company_id = company_id
        self.wallet_address = wallet_address
        self.identity_hash = self._compute_identity_hash()

    def _compute_identity_hash(self) -> str:
        data = f"SheldonOS:{self.company_id}:{self.wallet_address}"
        return "0x" + hashlib.sha256(data.encode()).hexdigest()

    def sign_action(self, action: Dict[str, Any]) -> str:
        payload = json.dumps({"identity": self.identity_hash, "action": action}, sort_keys=True)
        return "0x" + hashlib.sha256(payload.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "company_id": self.company_id,
            "wallet_address": self.wallet_address,
            "identity_hash": self.identity_hash,
            "standard": "ERC-8004",
        }
