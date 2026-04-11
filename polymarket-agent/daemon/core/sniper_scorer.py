"""
Sniper Opportunity Scorer
=========================
The core intelligence engine of the autonomous daemon. Continuously scans all
active Polymarket markets and scores each one using a multi-factor model that
combines:

  1. Price Mispricing Score  — gap between model probability and market price
  2. Liquidity Score         — depth of order book relative to desired position size
  3. Velocity Score          — rate of price change (momentum signal)
  4. Whale Signal Score      — large wallet accumulation detected via polyterm
  5. Kronos Forecast Score   — time-series model confidence from Kronos
  6. Sniper Pattern Score    — match against known winning whale archetypes
     (reachingthesky, KeyTransporter, HorizonSplendidView patterns)

Each market receives a composite SNIPER_SCORE (0-100). Only markets scoring
above the configured threshold are queued for execution.
"""
from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger("daemon.sniper_scorer")

# ---------------------------------------------------------------------------
# Sniper Archetypes (reverse-engineered from whale case studies)
# ---------------------------------------------------------------------------

SNIPER_ARCHETYPES = {
    "reachingthesky": {
        "description": "Contrarian underdog bet — market prices opponent as 60%+ favorite",
        "entry_price_range": (0.25, 0.45),   # buy at 25-45¢ (underdog)
        "min_liquidity": 50_000,
        "market_types": ["soccer", "sports"],
        "position_multiplier": 1.4,           # boost score for contrarian plays
    },
    "keytransporter": {
        "description": "Conviction favorite bet — load heavy size on 65-80¢ favorite",
        "entry_price_range": (0.60, 0.82),   # buy at 60-82¢ (heavy favorite)
        "min_liquidity": 100_000,
        "market_types": ["soccer", "sports"],
        "position_multiplier": 1.2,
    },
    "horizonsplendidview": {
        "description": "Contrarian No-win bet — fade heavy favorite at 65¢+",
        "entry_price_range": (0.25, 0.40),   # buy NO at 25-40¢
        "min_liquidity": 200_000,
        "market_types": ["soccer", "sports"],
        "position_multiplier": 1.3,
    },
    "geopolitical_insider": {
        "description": "Low-probability geopolitical event priced at <15¢",
        "entry_price_range": (0.03, 0.15),   # buy at 3-15¢ (long shot)
        "min_liquidity": 10_000,
        "market_types": ["politics", "geopolitics", "world"],
        "position_multiplier": 1.6,           # highest multiplier — asymmetric upside
    },
    "tech_insider": {
        "description": "Niche tech/product market priced at extreme mispricing",
        "entry_price_range": (0.02, 0.20),
        "min_liquidity": 5_000,
        "market_types": ["tech", "science", "crypto"],
        "position_multiplier": 1.5,
    },
}


# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------

@dataclass
class SniperOpportunity:
    """A scored market opportunity ready for execution review."""
    market_id: str
    market_title: str
    category: str
    current_price: float          # YES price in USDC (0-1)
    model_probability: float      # model's estimated true probability
    edge: float                   # model_probability - current_price
    edge_pct: float               # edge as % of current_price
    sniper_score: float           # composite score 0-100
    confidence: float             # model confidence 0-1
    liquidity_usdc: float
    volume_24h: float
    archetype_match: Optional[str]
    archetype_multiplier: float
    kelly_fraction: float         # recommended Kelly bet fraction
    recommended_side: str         # "YES" or "NO"
    recommended_size_usdc: float  # absolute USDC amount given current bankroll
    price_velocity: float         # rate of price change per hour
    whale_signal: bool            # whale accumulation detected
    resolution_date: Optional[str]
    hours_to_resolution: Optional[float]
    scored_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    raw_signals: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_actionable(self) -> bool:
        return self.sniper_score >= 60.0 and self.confidence >= 0.65 and self.edge >= 0.04

    def to_dict(self) -> Dict[str, Any]:
        return {
            "market_id": self.market_id,
            "market_title": self.market_title,
            "category": self.category,
            "current_price": round(self.current_price, 4),
            "model_probability": round(self.model_probability, 4),
            "edge": round(self.edge, 4),
            "edge_pct": round(self.edge_pct, 2),
            "sniper_score": round(self.sniper_score, 1),
            "confidence": round(self.confidence, 3),
            "liquidity_usdc": round(self.liquidity_usdc, 2),
            "volume_24h": round(self.volume_24h, 2),
            "archetype_match": self.archetype_match,
            "archetype_multiplier": self.archetype_multiplier,
            "kelly_fraction": round(self.kelly_fraction, 4),
            "recommended_side": self.recommended_side,
            "recommended_size_usdc": round(self.recommended_size_usdc, 2),
            "price_velocity": round(self.price_velocity, 6),
            "whale_signal": self.whale_signal,
            "resolution_date": self.resolution_date,
            "hours_to_resolution": self.hours_to_resolution,
            "scored_at": self.scored_at,
            "is_actionable": self.is_actionable,
        }


# ---------------------------------------------------------------------------
# Sniper Scorer
# ---------------------------------------------------------------------------

class SniperScorer:
    """
    Multi-factor opportunity scorer. Runs on every market in the scan universe
    and returns a ranked list of SniperOpportunity objects.
    """

    def __init__(self, config: Dict[str, Any]):
        self.cfg = config
        self.scoring_cfg = config.get("sniper", {})

        # Thresholds
        self.min_edge = self.scoring_cfg.get("min_edge", 0.04)
        self.min_confidence = self.scoring_cfg.get("min_confidence", 0.65)
        self.min_liquidity = self.scoring_cfg.get("min_liquidity", 5_000)
        self.max_kelly_fraction = self.scoring_cfg.get("max_kelly_fraction", 0.04)
        self.max_bet_usdc = self.scoring_cfg.get("max_bet_usdc", 500.0)

        # Weights for composite score
        self.weights = self.scoring_cfg.get("weights", {
            "mispricing":  0.30,
            "liquidity":   0.15,
            "velocity":    0.10,
            "whale":       0.15,
            "kronos":      0.20,
            "archetype":   0.10,
        })

        logger.info("SniperScorer initialized with min_edge=%.2f, min_confidence=%.2f",
                    self.min_edge, self.min_confidence)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def score_market(
        self,
        market: Dict[str, Any],
        bankroll_usdc: float,
        kronos_forecast: Optional[Dict[str, Any]] = None,
        whale_data: Optional[Dict[str, Any]] = None,
        price_history: Optional[List[float]] = None,
    ) -> Optional[SniperOpportunity]:
        """
        Score a single market. Returns None if the market doesn't meet
        minimum criteria (liquidity, edge, confidence).
        """
        try:
            return self._score(market, bankroll_usdc, kronos_forecast,
                               whale_data, price_history)
        except Exception as exc:
            logger.debug("Scoring failed for %s: %s", market.get("id", "?"), exc)
            return None

    def score_markets(
        self,
        markets: List[Dict[str, Any]],
        bankroll_usdc: float,
        kronos_forecasts: Optional[Dict[str, Dict]] = None,
        whale_data: Optional[Dict[str, Dict]] = None,
        price_histories: Optional[Dict[str, List[float]]] = None,
    ) -> List[SniperOpportunity]:
        """
        Score a batch of markets. Returns ranked list (highest score first).
        """
        kronos_forecasts = kronos_forecasts or {}
        whale_data = whale_data or {}
        price_histories = price_histories or {}

        opportunities = []
        for market in markets:
            mid = market.get("id", market.get("conditionId", ""))
            opp = self.score_market(
                market=market,
                bankroll_usdc=bankroll_usdc,
                kronos_forecast=kronos_forecasts.get(mid),
                whale_data=whale_data.get(mid),
                price_history=price_histories.get(mid),
            )
            if opp is not None:
                opportunities.append(opp)

        # Sort by sniper_score descending
        opportunities.sort(key=lambda o: o.sniper_score, reverse=True)
        logger.info("Scored %d markets → %d opportunities (actionable: %d)",
                    len(markets), len(opportunities),
                    sum(1 for o in opportunities if o.is_actionable))
        return opportunities

    # ------------------------------------------------------------------
    # Internal scoring logic
    # ------------------------------------------------------------------

    def _score(
        self,
        market: Dict[str, Any],
        bankroll_usdc: float,
        kronos_forecast: Optional[Dict[str, Any]],
        whale_data: Optional[Dict[str, Any]],
        price_history: Optional[List[float]],
    ) -> Optional[SniperOpportunity]:

        # ── Extract market data ──────────────────────────────────────
        mid = market.get("id", market.get("conditionId", ""))
        title = market.get("question", market.get("title", "Unknown"))
        category = (market.get("category") or market.get("tags", ["unknown"])[0]
                    if market.get("tags") else "unknown").lower()

        # Best YES price from order book or market data
        yes_price = self._extract_yes_price(market)
        if yes_price is None or yes_price <= 0.01 or yes_price >= 0.99:
            return None  # Skip near-certain or near-impossible markets

        liquidity = float(market.get("liquidity", 0) or 0)
        volume_24h = float(market.get("volume24hr", market.get("volume", 0)) or 0)

        if liquidity < self.min_liquidity:
            return None

        # ── Resolution timing ────────────────────────────────────────
        resolution_date, hours_to_resolution = self._parse_resolution(market)
        if hours_to_resolution is not None and hours_to_resolution < 0.5:
            return None  # Too close to resolution — no time to enter

        # ── Factor 1: Mispricing score ───────────────────────────────
        model_prob, model_confidence = self._estimate_model_probability(
            yes_price, kronos_forecast, market
        )
        edge_yes = model_prob - yes_price
        edge_no = (1 - model_prob) - (1 - yes_price)

        # Choose best side
        if abs(edge_yes) >= abs(edge_no):
            edge = edge_yes
            recommended_side = "YES"
            entry_price = yes_price
        else:
            edge = edge_no
            recommended_side = "NO"
            entry_price = 1 - yes_price

        if edge < self.min_edge:
            return None

        mispricing_score = min(100.0, (edge / 0.20) * 100)  # 20¢ edge = 100 pts

        # ── Factor 2: Liquidity score ────────────────────────────────
        liq_score = min(100.0, math.log10(max(liquidity, 1)) / math.log10(1_000_000) * 100)

        # ── Factor 3: Price velocity (momentum) ─────────────────────
        velocity = 0.0
        velocity_score = 50.0  # neutral
        if price_history and len(price_history) >= 3:
            velocity = self._compute_velocity(price_history)
            # Positive velocity toward our side = good signal
            if recommended_side == "YES" and velocity > 0:
                velocity_score = min(100.0, 50 + velocity * 5000)
            elif recommended_side == "NO" and velocity < 0:
                velocity_score = min(100.0, 50 + abs(velocity) * 5000)
            else:
                velocity_score = max(0.0, 50 - abs(velocity) * 2500)

        # ── Factor 4: Whale signal ───────────────────────────────────
        whale_signal = False
        whale_score = 0.0
        if whale_data:
            whale_signal = whale_data.get("large_accumulation", False)
            whale_direction = whale_data.get("direction", "")
            if whale_signal and whale_direction == recommended_side:
                whale_score = 100.0
            elif whale_signal and whale_direction != recommended_side:
                whale_score = 0.0
            else:
                whale_score = 30.0

        # ── Factor 5: Kronos forecast ────────────────────────────────
        kronos_score = 50.0  # neutral if no forecast
        if kronos_forecast:
            kp = kronos_forecast.get("predicted_probability", model_prob)
            kc = kronos_forecast.get("confidence", 0.5)
            k_edge = abs(kp - yes_price)
            kronos_score = min(100.0, (k_edge / 0.15) * 100 * kc)
            # Boost model confidence if Kronos agrees
            if (recommended_side == "YES" and kp > yes_price) or \
               (recommended_side == "NO" and kp < yes_price):
                model_confidence = min(0.99, model_confidence * 1.1)

        # ── Factor 6: Archetype match ────────────────────────────────
        archetype_match, archetype_multiplier, archetype_score = \
            self._match_archetype(entry_price, category, liquidity)

        # ── Composite score ──────────────────────────────────────────
        w = self.weights
        raw_score = (
            mispricing_score * w["mispricing"] +
            liq_score        * w["liquidity"] +
            velocity_score   * w["velocity"] +
            whale_score      * w["whale"] +
            kronos_score     * w["kronos"] +
            archetype_score  * w["archetype"]
        )
        sniper_score = min(100.0, raw_score * archetype_multiplier)

        if model_confidence < self.min_confidence:
            return None

        # ── Kelly fraction ───────────────────────────────────────────
        kelly = self._kelly(model_prob if recommended_side == "YES" else 1 - model_prob,
                            entry_price)
        kelly = min(kelly, self.max_kelly_fraction)
        recommended_size = min(bankroll_usdc * kelly, self.max_bet_usdc)

        return SniperOpportunity(
            market_id=mid,
            market_title=title,
            category=category,
            current_price=yes_price,
            model_probability=model_prob,
            edge=edge,
            edge_pct=round(edge / entry_price * 100, 2),
            sniper_score=sniper_score,
            confidence=model_confidence,
            liquidity_usdc=liquidity,
            volume_24h=volume_24h,
            archetype_match=archetype_match,
            archetype_multiplier=archetype_multiplier,
            kelly_fraction=kelly,
            recommended_side=recommended_side,
            recommended_size_usdc=recommended_size,
            price_velocity=velocity,
            whale_signal=whale_signal,
            resolution_date=resolution_date,
            hours_to_resolution=hours_to_resolution,
            raw_signals={
                "mispricing_score": mispricing_score,
                "liq_score": liq_score,
                "velocity_score": velocity_score,
                "whale_score": whale_score,
                "kronos_score": kronos_score,
                "archetype_score": archetype_score,
            },
        )

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------

    def _extract_yes_price(self, market: Dict[str, Any]) -> Optional[float]:
        """Extract the best YES price from market data."""
        # Try direct price fields
        for key in ("bestBid", "lastTradePrice", "price", "outcomePrices"):
            val = market.get(key)
            if val is None:
                continue
            if isinstance(val, (int, float)):
                p = float(val)
                if 0 < p < 1:
                    return p
            if isinstance(val, str):
                try:
                    # outcomePrices is often "[\"0.65\", \"0.35\"]"
                    import json
                    prices = json.loads(val)
                    if isinstance(prices, list) and len(prices) >= 1:
                        p = float(prices[0])
                        if 0 < p < 1:
                            return p
                except Exception:
                    try:
                        p = float(val)
                        if 0 < p < 1:
                            return p
                    except Exception:
                        pass
        # Try tokens
        tokens = market.get("tokens", [])
        if tokens and isinstance(tokens, list):
            for tok in tokens:
                if isinstance(tok, dict):
                    outcome = tok.get("outcome", "").upper()
                    price = tok.get("price")
                    if outcome == "YES" and price is not None:
                        try:
                            p = float(price)
                            if 0 < p < 1:
                                return p
                        except Exception:
                            pass
        return None

    def _estimate_model_probability(
        self,
        yes_price: float,
        kronos_forecast: Optional[Dict[str, Any]],
        market: Dict[str, Any],
    ) -> Tuple[float, float]:
        """
        Estimate the true probability using available signals.
        Returns (probability, confidence).
        """
        estimates = []
        confidences = []

        # Kronos time-series forecast
        if kronos_forecast:
            kp = kronos_forecast.get("predicted_probability")
            kc = kronos_forecast.get("confidence", 0.5)
            if kp is not None:
                estimates.append((float(kp), float(kc)))
                confidences.append(float(kc))

        # Polymarket's own analytics signals
        for key in ("analyticsScore", "predictionScore", "modelScore"):
            val = market.get(key)
            if val is not None:
                try:
                    p = float(val)
                    if 0 < p < 1:
                        estimates.append((p, 0.6))
                        confidences.append(0.6)
                except Exception:
                    pass

        # Fallback: apply a mean-reversion adjustment to market price
        # (markets tend to be overconfident at extremes)
        if not estimates:
            # Shrink toward 0.5 by 5% — captures systematic mispricing
            adjusted = yes_price * 0.95 + 0.5 * 0.05
            estimates.append((adjusted, 0.45))
            confidences.append(0.45)

        # Weighted average
        total_weight = sum(c for _, c in estimates)
        prob = sum(p * c for p, c in estimates) / total_weight
        confidence = sum(confidences) / len(confidences)

        # Clip to valid range
        prob = max(0.01, min(0.99, prob))
        return prob, confidence

    def _compute_velocity(self, prices: List[float]) -> float:
        """Compute price velocity (change per hour) from recent price history."""
        if len(prices) < 2:
            return 0.0
        # Simple linear regression slope
        n = len(prices)
        x = list(range(n))
        x_mean = sum(x) / n
        y_mean = sum(prices) / n
        num = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, prices))
        den = sum((xi - x_mean) ** 2 for xi in x)
        if den == 0:
            return 0.0
        return num / den

    def _match_archetype(
        self,
        entry_price: float,
        category: str,
        liquidity: float,
    ) -> Tuple[Optional[str], float, float]:
        """
        Match the opportunity against known sniper archetypes.
        Returns (archetype_name, multiplier, archetype_score).
        """
        best_match = None
        best_score = 0.0
        best_multiplier = 1.0

        for name, arch in SNIPER_ARCHETYPES.items():
            lo, hi = arch["entry_price_range"]
            type_match = any(t in category for t in arch["market_types"])
            price_match = lo <= entry_price <= hi
            liq_ok = liquidity >= arch["min_liquidity"]

            if price_match and liq_ok:
                score = 80.0
                if type_match:
                    score = 100.0
                if score > best_score:
                    best_score = score
                    best_match = name
                    best_multiplier = arch["position_multiplier"] if type_match else 1.1

        return best_match, best_multiplier, best_score

    def _kelly(self, prob: float, price: float) -> float:
        """
        Full Kelly fraction: f = (prob * (1/price - 1) - (1-prob)) / (1/price - 1)
        Simplified: f = (prob - price) / (1 - price)
        """
        if price >= 1.0 or price <= 0.0:
            return 0.0
        odds = (1.0 / price) - 1.0
        if odds <= 0:
            return 0.0
        kelly = (prob * odds - (1 - prob)) / odds
        return max(0.0, kelly)

    def _parse_resolution(
        self, market: Dict[str, Any]
    ) -> Tuple[Optional[str], Optional[float]]:
        """Parse resolution date and compute hours to resolution."""
        for key in ("endDate", "endDateIso", "resolutionDate", "closeTime"):
            val = market.get(key)
            if val:
                try:
                    from dateutil import parser as dtparser
                    dt = dtparser.parse(str(val))
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    now = datetime.now(timezone.utc)
                    hours = (dt - now).total_seconds() / 3600
                    return val, hours
                except Exception:
                    pass
        return None, None
