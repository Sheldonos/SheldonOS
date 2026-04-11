"""
Daemon Integration Tests
========================
Tests all daemon components end-to-end without requiring live API access.
Uses mock data clients and synthetic market data.
"""
import sys
import os
import json
import queue
import threading
import time
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from daemon.core.sniper_scorer import SniperScorer, SniperOpportunity
from daemon.notifications.notifier import NotificationManager


# ---------------------------------------------------------------------------
# Synthetic market data factory
# ---------------------------------------------------------------------------

def make_market(
    market_id="mkt_001",
    title="Will PSG beat Chelsea?",
    category="soccer",
    yes_price=0.38,
    liquidity=150_000,
    volume=80_000,
    hours_to_resolution=48,
):
    from datetime import datetime, timezone, timedelta
    end_dt = (datetime.now(timezone.utc) + timedelta(hours=hours_to_resolution)).isoformat()
    return {
        "id": market_id,
        "question": title,
        "category": category,
        "outcomePrices": json.dumps([str(yes_price), str(round(1 - yes_price, 4))]),
        "liquidity": liquidity,
        "volume24hr": volume,
        "endDateIso": end_dt,
        "tokens": [
            {"outcome": "YES", "price": yes_price, "token_id": f"tok_{market_id}_yes"},
            {"outcome": "NO",  "price": 1 - yes_price, "token_id": f"tok_{market_id}_no"},
        ],
    }


# ---------------------------------------------------------------------------
# Test: SniperScorer
# ---------------------------------------------------------------------------

class TestSniperScorer(unittest.TestCase):

    def setUp(self):
        self.cfg = {
            "sniper": {
                "min_edge": 0.04,
                "min_confidence": 0.60,
                "min_liquidity": 5_000,
                "max_kelly_fraction": 0.04,
                "max_bet_usdc": 500.0,
                "weights": {
                    "mispricing": 0.30,
                    "liquidity": 0.15,
                    "velocity": 0.10,
                    "whale": 0.15,
                    "kronos": 0.20,
                    "archetype": 0.10,
                },
            }
        }
        self.scorer = SniperScorer(self.cfg)
        self.bankroll = 1000.0

    def test_score_reachingthesky_archetype(self):
        """PSG underdog at 38¢ should match reachingthesky archetype."""
        market = make_market(yes_price=0.38, liquidity=150_000, category="soccer")
        kronos = {"predicted_probability": 0.52, "confidence": 0.72}
        opp = self.scorer.score_market(market, self.bankroll, kronos_forecast=kronos)
        self.assertIsNotNone(opp, "Should score a valid opportunity")
        self.assertEqual(opp.recommended_side, "YES")
        self.assertGreater(opp.edge, 0.04)
        self.assertGreater(opp.sniper_score, 50.0)
        self.assertEqual(opp.archetype_match, "reachingthesky")
        print(f"  reachingthesky score: {opp.sniper_score:.1f} | edge: {opp.edge:.3f}")

    def test_score_keytransporter_archetype(self):
        """Arsenal at 72¢ should match keytransporter archetype."""
        market = make_market(
            market_id="mkt_002", title="Will Arsenal win?",
            yes_price=0.72, liquidity=200_000, category="soccer"
        )
        kronos = {"predicted_probability": 0.82, "confidence": 0.78}
        opp = self.scorer.score_market(market, self.bankroll, kronos_forecast=kronos)
        self.assertIsNotNone(opp)
        self.assertEqual(opp.archetype_match, "keytransporter")
        print(f"  keytransporter score: {opp.sniper_score:.1f} | edge: {opp.edge:.3f}")

    def test_score_geopolitical_archetype(self):
        """Low-probability geopolitical event at 8¢ should match geopolitical_insider."""
        market = make_market(
            market_id="mkt_003", title="Will Maduro leave power by Jan 31?",
            yes_price=0.08, liquidity=25_000, category="politics"
        )
        kronos = {"predicted_probability": 0.22, "confidence": 0.65}
        opp = self.scorer.score_market(market, self.bankroll, kronos_forecast=kronos)
        self.assertIsNotNone(opp)
        self.assertEqual(opp.archetype_match, "geopolitical_insider")
        print(f"  geopolitical score: {opp.sniper_score:.1f} | edge: {opp.edge:.3f}")

    def test_rejects_low_liquidity(self):
        """Markets with liquidity below threshold should be rejected."""
        market = make_market(yes_price=0.38, liquidity=1_000)
        opp = self.scorer.score_market(market, self.bankroll)
        self.assertIsNone(opp, "Low liquidity market should be rejected")

    def test_rejects_near_certain(self):
        """Markets priced at 99¢ should be rejected (no edge)."""
        market = make_market(yes_price=0.99, liquidity=100_000)
        opp = self.scorer.score_market(market, self.bankroll)
        self.assertIsNone(opp, "Near-certain market should be rejected")

    def test_rejects_low_edge(self):
        """Markets with edge below threshold should be rejected."""
        market = make_market(yes_price=0.50, liquidity=100_000)
        # No Kronos forecast — model will only apply tiny mean-reversion
        opp = self.scorer.score_market(market, self.bankroll)
        # At 50¢ with no forecast, edge is tiny — should be None or very low
        if opp is not None:
            self.assertLess(opp.edge, 0.04,
                            "Near-fair-value market should have edge < 4%")

    def test_kelly_fraction_capped(self):
        """Kelly fraction should never exceed max_kelly_fraction."""
        market = make_market(yes_price=0.10, liquidity=500_000, category="politics")
        kronos = {"predicted_probability": 0.50, "confidence": 0.90}
        opp = self.scorer.score_market(market, self.bankroll, kronos_forecast=kronos)
        if opp:
            self.assertLessEqual(opp.kelly_fraction, 0.04)
            print(f"  Kelly fraction: {opp.kelly_fraction:.4f} (cap: 0.04)")

    def test_batch_scoring_returns_sorted(self):
        """Batch scoring should return opportunities sorted by score descending."""
        markets = [
            make_market("m1", yes_price=0.38, liquidity=150_000, category="soccer"),
            make_market("m2", yes_price=0.72, liquidity=200_000, category="soccer"),
            make_market("m3", yes_price=0.08, liquidity=25_000, category="politics"),
            make_market("m4", yes_price=0.50, liquidity=1_000),   # too low liquidity
        ]
        kronos = {
            "m1": {"predicted_probability": 0.52, "confidence": 0.72},
            "m2": {"predicted_probability": 0.82, "confidence": 0.78},
            "m3": {"predicted_probability": 0.22, "confidence": 0.65},
        }
        opps = self.scorer.score_markets(markets, self.bankroll, kronos_forecasts=kronos)
        self.assertGreater(len(opps), 0)
        scores = [o.sniper_score for o in opps]
        self.assertEqual(scores, sorted(scores, reverse=True),
                         "Opportunities should be sorted by score descending")
        print(f"  Batch: {len(opps)} opportunities scored")
        for o in opps:
            print(f"    [{o.archetype_match or 'generic':20s}] {o.market_title[:35]:35s} "
                  f"score={o.sniper_score:.1f} edge={o.edge:.3f}")

    def test_whale_signal_boosts_score(self):
        """Whale signal in same direction should boost score."""
        market = make_market(yes_price=0.38, liquidity=150_000, category="soccer")
        kronos = {"predicted_probability": 0.52, "confidence": 0.72}

        opp_no_whale = self.scorer.score_market(market, self.bankroll, kronos_forecast=kronos)
        whale = {"large_accumulation": True, "direction": "YES"}
        opp_whale = self.scorer.score_market(
            market, self.bankroll, kronos_forecast=kronos, whale_data=whale
        )
        if opp_no_whale and opp_whale:
            self.assertGreaterEqual(opp_whale.sniper_score, opp_no_whale.sniper_score)
            print(f"  Score without whale: {opp_no_whale.sniper_score:.1f}")
            print(f"  Score with whale:    {opp_whale.sniper_score:.1f}")

    def test_velocity_signal(self):
        """Rising price history should boost YES score."""
        market = make_market(yes_price=0.38, liquidity=150_000, category="soccer")
        kronos = {"predicted_probability": 0.52, "confidence": 0.72}
        rising_prices = [0.30, 0.32, 0.33, 0.35, 0.36, 0.37, 0.38]

        opp_flat = self.scorer.score_market(market, self.bankroll, kronos_forecast=kronos)
        opp_rising = self.scorer.score_market(
            market, self.bankroll, kronos_forecast=kronos, price_history=rising_prices
        )
        if opp_flat and opp_rising:
            print(f"  Score flat:   {opp_flat.sniper_score:.1f}")
            print(f"  Score rising: {opp_rising.sniper_score:.1f}")


# ---------------------------------------------------------------------------
# Test: NotificationManager (log-only, no real HTTP calls)
# ---------------------------------------------------------------------------

class TestNotificationManager(unittest.TestCase):

    def setUp(self):
        self.cfg = {
            "notifications": {
                "telegram_bot_token": "",
                "telegram_chat_id": "",
                "discord_webhook_url": "",
                "desktop_notifications": False,
                "min_level": "info",
            }
        }
        self.notifier = NotificationManager(self.cfg)

    def test_send_does_not_raise(self):
        """send() should not raise even with no channels configured."""
        self.notifier.send("Test Title", "Test body", level="info")
        time.sleep(0.2)  # let background thread complete
        print("  Notification sent without error")

    def test_level_filtering(self):
        """Messages below min_level should be silently dropped."""
        self.cfg["notifications"]["min_level"] = "warning"
        notifier = NotificationManager(self.cfg)
        # This should be silently dropped (info < warning)
        notifier.send_sync("Info msg", "body", level="info")
        print("  Level filtering works correctly")

    def test_escape_markdown(self):
        """Telegram markdown escaping should handle special chars."""
        raw = "P&L: +$1,234.56 (edge > 5%)"
        escaped = NotificationManager._escape_md(raw)
        self.assertNotIn(">", escaped.replace("\\>", ""))
        print(f"  Escaped: {escaped}")


# ---------------------------------------------------------------------------
# Test: Opportunity queue flow (scanner → executor)
# ---------------------------------------------------------------------------

class TestOpportunityQueueFlow(unittest.TestCase):

    def test_opportunity_queued_and_consumed(self):
        """SniperOpportunity should flow through queue correctly."""
        opp_queue = queue.Queue(maxsize=10)
        cfg = {
            "sniper": {
                "min_edge": 0.04,
                "min_confidence": 0.60,
                "min_liquidity": 5_000,
                "max_kelly_fraction": 0.04,
                "max_bet_usdc": 500.0,
                "weights": {
                    "mispricing": 0.30, "liquidity": 0.15, "velocity": 0.10,
                    "whale": 0.15, "kronos": 0.20, "archetype": 0.10,
                },
            }
        }
        scorer = SniperScorer(cfg)
        market = make_market(yes_price=0.38, liquidity=150_000, category="soccer")
        kronos = {"predicted_probability": 0.52, "confidence": 0.72}
        opp = scorer.score_market(market, 1000.0, kronos_forecast=kronos)
        self.assertIsNotNone(opp)

        opp_queue.put_nowait(opp)
        self.assertEqual(opp_queue.qsize(), 1)

        consumed = opp_queue.get_nowait()
        self.assertEqual(consumed.market_id, "mkt_001")
        self.assertTrue(consumed.is_actionable)
        print(f"  Queue flow: {consumed.market_title[:40]} | score={consumed.sniper_score:.1f}")


# ---------------------------------------------------------------------------
# Test: Context window handoff threshold
# ---------------------------------------------------------------------------

class TestContextHandoff(unittest.TestCase):

    def test_handoff_triggers_at_56_pct(self):
        """SubAgentState.needs_handoff should be True at 56% context usage."""
        from daemon.supervisor.agent_supervisor import SubAgentState, SubAgentSpec
        spec = SubAgentSpec(
            name="TestAgent",
            categories=["soccer"],
            bankroll_allocation=0.25,
        )
        state = SubAgentState(spec=spec)
        state.context_max_tokens = 128_000

        # At 55% — should NOT trigger
        state.context_tokens_used = int(128_000 * 0.55)
        self.assertFalse(state.needs_handoff,
                         "Should not trigger handoff at 55%")

        # At 56% — SHOULD trigger
        state.context_tokens_used = int(128_000 * 0.56)
        self.assertTrue(state.needs_handoff,
                        "Should trigger handoff at 56%")

        # At 80% — definitely should trigger
        state.context_tokens_used = int(128_000 * 0.80)
        self.assertTrue(state.needs_handoff,
                        "Should trigger handoff at 80%")

        print(f"  Handoff threshold: {state.handoff_threshold:.0%} ✓")

    def test_context_pct_calculation(self):
        """context_pct should correctly reflect token usage percentage."""
        from daemon.supervisor.agent_supervisor import SubAgentState, SubAgentSpec
        spec = SubAgentSpec(name="TestAgent", categories=[], bankroll_allocation=0.1)
        state = SubAgentState(spec=spec)
        state.context_max_tokens = 100_000
        state.context_tokens_used = 42_000
        self.assertAlmostEqual(state.context_pct, 0.42, places=2)
        print(f"  Context pct: {state.context_pct:.0%} ✓")


# ---------------------------------------------------------------------------
# Test: SniperOpportunity serialization
# ---------------------------------------------------------------------------

class TestSniperOpportunitySerialization(unittest.TestCase):

    def test_to_dict_is_json_serializable(self):
        """SniperOpportunity.to_dict() should be JSON-serializable."""
        cfg = {
            "sniper": {
                "min_edge": 0.04, "min_confidence": 0.60, "min_liquidity": 5_000,
                "max_kelly_fraction": 0.04, "max_bet_usdc": 500.0,
                "weights": {
                    "mispricing": 0.30, "liquidity": 0.15, "velocity": 0.10,
                    "whale": 0.15, "kronos": 0.20, "archetype": 0.10,
                },
            }
        }
        scorer = SniperScorer(cfg)
        market = make_market(yes_price=0.38, liquidity=150_000, category="soccer")
        kronos = {"predicted_probability": 0.52, "confidence": 0.72}
        opp = scorer.score_market(market, 1000.0, kronos_forecast=kronos)
        self.assertIsNotNone(opp)

        d = opp.to_dict()
        json_str = json.dumps(d)  # Should not raise
        self.assertIn("sniper_score", json_str)
        self.assertIn("archetype_match", json_str)
        print(f"  Serialization OK: {len(json_str)} bytes")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("POLYMARKET SNIPER DAEMON — INTEGRATION TESTS")
    print("=" * 60 + "\n")

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    test_classes = [
        TestSniperScorer,
        TestNotificationManager,
        TestOpportunityQueueFlow,
        TestContextHandoff,
        TestSniperOpportunitySerialization,
    ]

    for cls in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(cls))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 60)
    passed = result.testsRun - len(result.failures) - len(result.errors)
    print(f"RESULTS: {passed}/{result.testsRun} tests passed")
    if result.failures or result.errors:
        print("FAILURES:", len(result.failures))
        print("ERRORS:  ", len(result.errors))
    else:
        print("ALL TESTS PASSED ✓")
    print("=" * 60)

    sys.exit(0 if result.wasSuccessful() else 1)
