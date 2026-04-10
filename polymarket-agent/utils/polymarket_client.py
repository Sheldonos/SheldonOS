"""
Polymarket Data Client
Wraps the polyterm API modules to provide a unified interface for market data,
order book analysis, whale tracking, and arbitrage detection.
"""
import sys
import time
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

# Add polyterm to path
sys.path.insert(0, "/home/ubuntu/polyterm")

from polyterm.api.gamma import GammaClient
from polyterm.api.clob import CLOBClient
from polyterm.core.analytics import MarketAnalytics
from polyterm.core.risk_score import MarketRiskScorer
from polyterm.core.predictions import MarketPredictor, Direction
from polyterm.core.arbitrage import ArbitrageScanner
from polyterm.core.whale_tracker import WhaleTracker
from polyterm.core.scanner import MarketScanner

logger = logging.getLogger(__name__)


class PolymarketDataClient:
    """
    Unified Polymarket data client integrating polyterm modules.
    Provides market data, analytics, risk scoring, and signal generation.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        pm_cfg = config.get("polymarket", {})

        self.gamma = GammaClient(
            base_url=pm_cfg.get("gamma_api_url", "https://gamma-api.polymarket.com")
        )
        self.clob = CLOBClient(
            base_url=pm_cfg.get("clob_api_url", "https://clob.polymarket.com")
        )
        self.risk_scorer = MarketRiskScorer()
        self.predictor = MarketPredictor(
            gamma_client=self.gamma,
            clob_client=self.clob,
        )
        self.arb_scanner = ArbitrageScanner(
            gamma_client=self.gamma,
            clob_client=self.clob,
        )
        logger.info("PolymarketDataClient initialized")

    # ------------------------------------------------------------------
    # Market Discovery
    # ------------------------------------------------------------------

    def get_active_markets(
        self,
        limit: int = 200,
        categories: Optional[List[str]] = None,
        min_liquidity: float = 1000.0,
        min_volume_24h: float = 500.0,
    ) -> List[Dict[str, Any]]:
        """Fetch active markets with optional filtering."""
        try:
            markets = self.gamma.get_markets(
                limit=limit,
                active=True,
                closed=False,
            )
            filtered = []
            for m in markets:
                liquidity = float(m.get("liquidity", 0) or 0)
                volume = float(m.get("volume24hr", m.get("volume", 0)) or 0)
                if liquidity < min_liquidity:
                    continue
                if volume < min_volume_24h:
                    continue
                if categories:
                    tags = [t.get("label", "").lower() for t in (m.get("tags") or [])]
                    if not any(cat.lower() in tags for cat in categories):
                        continue
                filtered.append(m)
            logger.info(f"Fetched {len(filtered)} markets after filtering (from {len(markets)})")
            return filtered
        except Exception as e:
            logger.error(f"Error fetching markets: {e}")
            return []

    def get_market_detail(self, market_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed market information."""
        try:
            return self.gamma.get_market(market_id)
        except Exception as e:
            logger.error(f"Error fetching market {market_id}: {e}")
            return None

    # ------------------------------------------------------------------
    # Price History
    # ------------------------------------------------------------------

    def get_price_history(
        self,
        token_id: str,
        interval: str = "1d",
        fidelity: int = 3600,
        start_ts: Optional[int] = None,
        end_ts: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch historical price data for a market token.
        Returns list of {t: timestamp, p: price} dicts.
        """
        try:
            return self.clob.get_price_history(
                token_id=token_id,
                interval=interval,
                fidelity=fidelity,
                start_ts=start_ts,
                end_ts=end_ts,
            )
        except Exception as e:
            logger.warning(f"Error fetching price history for {token_id}: {e}")
            return []

    # ------------------------------------------------------------------
    # Order Book
    # ------------------------------------------------------------------

    def get_order_book(self, token_id: str) -> Dict[str, Any]:
        """Get current order book for a market."""
        try:
            return self.clob.get_order_book(token_id)
        except Exception as e:
            logger.warning(f"Error fetching order book for {token_id}: {e}")
            return {}

    def calculate_spread(self, order_book: Dict[str, Any]) -> float:
        """Calculate bid-ask spread from order book."""
        try:
            return self.clob.calculate_spread(order_book)
        except Exception:
            return 1.0  # Max spread if unavailable

    # ------------------------------------------------------------------
    # Risk Scoring
    # ------------------------------------------------------------------

    def score_market_risk(self, market: Dict[str, Any]) -> Dict[str, Any]:
        """Score a market's risk level using polyterm's risk scorer."""
        try:
            end_date = None
            end_date_str = market.get("endDate") or market.get("end_date_iso")
            if end_date_str:
                try:
                    end_date = datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))
                except Exception:
                    pass

            assessment = self.risk_scorer.score_market(
                market_id=market.get("id", ""),
                title=market.get("question", market.get("title", "")),
                description=market.get("description", ""),
                end_date=end_date,
                volume_24h=float(market.get("volume24hr", 0) or 0),
                liquidity=float(market.get("liquidity", 0) or 0),
                spread=0.0,
                category=", ".join(
                    [t.get("label", "") for t in (market.get("tags") or [])]
                ),
            )
            return assessment.to_dict()
        except Exception as e:
            logger.warning(f"Error scoring market risk: {e}")
            return {"overall_grade": "C", "overall_score": 50}

    # ------------------------------------------------------------------
    # Signal Generation (polyterm predictions)
    # ------------------------------------------------------------------

    def get_market_signals(self, market_id: str) -> Optional[Dict[str, Any]]:
        """
        Generate multi-factor trading signals using polyterm's predictor.
        Returns prediction dict with direction, confidence, and signals.
        """
        try:
            prediction = self.predictor.predict_market(market_id)
            if prediction is None:
                return None
            return {
                "market_id": market_id,
                "direction": prediction.direction.value,
                "confidence": prediction.confidence,
                "probability_change": prediction.probability_change,
                "horizon_hours": prediction.horizon_hours,
                "signals": [
                    {
                        "type": s.signal_type.value,
                        "direction": s.direction.value,
                        "strength": s.strength,
                        "confidence": s.confidence,
                        "description": s.description,
                    }
                    for s in prediction.signals
                ],
                "signal_summary": prediction.signal_summary,
            }
        except Exception as e:
            logger.warning(f"Error generating signals for {market_id}: {e}")
            return None

    # ------------------------------------------------------------------
    # Arbitrage Detection
    # ------------------------------------------------------------------

    def scan_arbitrage(
        self,
        min_spread: float = 0.025,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Scan for arbitrage opportunities across markets."""
        try:
            return self.arb_scanner.scan(min_spread=min_spread, limit=limit)
        except Exception as e:
            logger.warning(f"Error scanning arbitrage: {e}")
            return []

    # ------------------------------------------------------------------
    # Market Metadata Helpers
    # ------------------------------------------------------------------

    def extract_yes_price(self, market: Dict[str, Any]) -> float:
        """Extract the YES token price from a market dict."""
        # Try outcomePrices first
        outcome_prices = market.get("outcomePrices")
        if isinstance(outcome_prices, str):
            import json
            try:
                outcome_prices = json.loads(outcome_prices)
            except Exception:
                outcome_prices = None
        if outcome_prices and len(outcome_prices) > 0:
            try:
                return float(outcome_prices[0])
            except (ValueError, TypeError):
                pass
        # Fallback to lastTradePrice
        return float(market.get("lastTradePrice", 0.5) or 0.5)

    def get_token_ids(self, market: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
        """Extract YES and NO token IDs from a market dict."""
        clob_token_ids = market.get("clobTokenIds")
        if isinstance(clob_token_ids, str):
            import json
            try:
                clob_token_ids = json.loads(clob_token_ids)
            except Exception:
                clob_token_ids = None
        if clob_token_ids and len(clob_token_ids) >= 2:
            return str(clob_token_ids[0]), str(clob_token_ids[1])
        # Try nested markets
        nested = market.get("markets", [])
        if nested:
            yes_id = nested[0].get("clobTokenId") if len(nested) > 0 else None
            no_id = nested[1].get("clobTokenId") if len(nested) > 1 else None
            return yes_id, no_id
        return None, None
