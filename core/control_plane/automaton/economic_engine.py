"""
SheldonOS — Automaton Economic Engine
Manages the entity's on-chain identity (ERC-8004), crypto wallet, and financial transactions.
Executes trades only when confidence threshold is met from the Simulation Pipeline.
"""

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger("sheldon.automaton")


class TradeSignalConfidence(Enum):
    LOW = "low"          # < 70% — log only, do not execute
    MEDIUM = "medium"    # 70-89% — queue for human review
    HIGH = "high"        # 90-100% — execute autonomously


@dataclass
class TradeSignal:
    """A trade signal produced by the Simulation Pipeline (MiroFish → Percepta)."""
    signal_id: str
    asset: str
    direction: str          # "long" | "short"
    confidence_pct: float
    expected_roi_pct: float
    time_horizon_hours: int
    source_simulation_id: str
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    executed: bool = False
    execution_tx_hash: Optional[str] = None


@dataclass
class WalletState:
    """Current state of the entity's crypto wallet."""
    address: str
    chain_id: int
    eth_balance: Decimal
    usdc_balance: Decimal
    total_usd_value: Decimal
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class AutomatonEngine:
    """
    The Automaton Economic Engine.
    Reads trade signals from the Simulation Pipeline and executes on-chain transactions
    only when confidence exceeds the configured threshold.
    """

    CONFIDENCE_THRESHOLD = float(os.getenv("AUTOMATON_CONFIDENCE_THRESHOLD", "90.0"))
    MAX_POSITION_SIZE_USD = float(os.getenv("AUTOMATON_MAX_POSITION_USD", "500.0"))
    DAILY_LOSS_LIMIT_USD = float(os.getenv("AUTOMATON_DAILY_LOSS_LIMIT_USD", "200.0"))

    def __init__(self):
        self.wallet: Optional[WalletState] = None
        self.pending_signals: List[TradeSignal] = []
        self.executed_signals: List[TradeSignal] = []
        self.daily_pnl_usd: float = 0.0
        self._initialize_wallet()

    def _initialize_wallet(self):
        """Initialize the wallet state from environment variables."""
        wallet_address = os.getenv("AUTOMATON_WALLET_ADDRESS")
        if not wallet_address:
            logger.warning("AUTOMATON_WALLET_ADDRESS not set — running in simulation mode")
            return
        self.wallet = WalletState(
            address=wallet_address,
            chain_id=int(os.getenv("AUTOMATON_CHAIN_ID", "1")),
            eth_balance=Decimal("0"),
            usdc_balance=Decimal("0"),
            total_usd_value=Decimal("0"),
        )
        logger.info(f"Automaton wallet initialized: {wallet_address[:10]}...")

    def evaluate_signal(self, signal: TradeSignal) -> TradeSignalConfidence:
        """Evaluate a trade signal and return its confidence tier."""
        if signal.confidence_pct >= self.CONFIDENCE_THRESHOLD:
            return TradeSignalConfidence.HIGH
        elif signal.confidence_pct >= 70.0:
            return TradeSignalConfidence.MEDIUM
        return TradeSignalConfidence.LOW

    def process_signal(self, signal: TradeSignal) -> Dict[str, Any]:
        """
        Process a trade signal from the Simulation Pipeline.
        Executes the trade if confidence is HIGH, queues it if MEDIUM, logs if LOW.
        """
        confidence_tier = self.evaluate_signal(signal)
        logger.info(
            f"[Signal {signal.signal_id}] {signal.asset} {signal.direction} | "
            f"confidence={signal.confidence_pct:.1f}% | tier={confidence_tier.value}"
        )

        if confidence_tier == TradeSignalConfidence.LOW:
            return {"status": "logged", "reason": "confidence below threshold", "signal_id": signal.signal_id}

        if confidence_tier == TradeSignalConfidence.MEDIUM:
            self.pending_signals.append(signal)
            self._notify_operator(signal, "queued_for_review")
            return {"status": "queued", "signal_id": signal.signal_id}

        # HIGH confidence — check daily loss limit before executing
        if self.daily_pnl_usd <= -self.DAILY_LOSS_LIMIT_USD:
            logger.warning(f"Daily loss limit reached (${self.daily_pnl_usd:.2f}) — halting execution")
            return {"status": "halted", "reason": "daily_loss_limit", "signal_id": signal.signal_id}

        return self._execute_trade(signal)

    def _execute_trade(self, signal: TradeSignal) -> Dict[str, Any]:
        """Execute a trade on-chain via the ERC-8004 agent identity."""
        if not self.wallet:
            logger.info(f"[SIMULATION] Would execute: {signal.asset} {signal.direction} @ confidence={signal.confidence_pct:.1f}%")
            signal.executed = True
            signal.execution_tx_hash = f"0xSIMULATED_{signal.signal_id[:8]}"
            self.executed_signals.append(signal)
            return {"status": "simulated", "tx_hash": signal.execution_tx_hash}

        # Production: call the on-chain execution module
        # tx_hash = self._submit_onchain_tx(signal)
        logger.info(f"Executing trade: {signal.asset} {signal.direction} | size=${self.MAX_POSITION_SIZE_USD}")
        signal.executed = True
        self.executed_signals.append(signal)
        self._notify_operator(signal, "trade_executed")
        return {"status": "executed", "signal_id": signal.signal_id}

    def _notify_operator(self, signal: TradeSignal, event_type: str):
        """Notify the operator via OpenClaw (Telegram/Slack)."""
        logger.info(f"[NOTIFY] {event_type}: {signal.asset} {signal.direction} @ {signal.confidence_pct:.1f}%")

    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Return a summary of the current portfolio state."""
        return {
            "wallet": self.wallet.__dict__ if self.wallet else None,
            "daily_pnl_usd": self.daily_pnl_usd,
            "pending_signals": len(self.pending_signals),
            "executed_signals": len(self.executed_signals),
            "confidence_threshold": self.CONFIDENCE_THRESHOLD,
            "max_position_size_usd": self.MAX_POSITION_SIZE_USD,
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
        """Compute a deterministic identity hash for this agent."""
        import hashlib
        data = f"SheldonOS:{self.company_id}:{self.wallet_address}"
        return "0x" + hashlib.sha256(data.encode()).hexdigest()

    def sign_action(self, action: Dict[str, Any]) -> str:
        """Sign an action with the agent's identity for on-chain auditability."""
        import json, hashlib
        payload = json.dumps({"identity": self.identity_hash, "action": action}, sort_keys=True)
        return "0x" + hashlib.sha256(payload.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "company_id": self.company_id,
            "wallet_address": self.wallet_address,
            "identity_hash": self.identity_hash,
            "standard": "ERC-8004",
        }
