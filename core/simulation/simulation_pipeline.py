"""
SheldonOS — Simulation Pipeline
The core profit engine: MiroFish social simulation → Percepta economic math → Trade Signal.
This pipeline is the primary mechanism for generating alpha in prediction markets.
"""

import asyncio
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger("sheldon.simulation")


@dataclass
class SimulationInput:
    """Input data for a simulation run."""
    simulation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_description: str = ""
    event_category: str = ""   # politics | technology | economics | sports | crypto
    time_horizon_days: int = 7
    population_size: int = 10_000
    raw_data: Dict[str, Any] = field(default_factory=dict)
    market_question: str = ""  # The Polymarket/Kalshi question being evaluated
    current_market_odds: float = 0.5  # Current implied probability on the market


@dataclass
class MiroFishResult:
    """Output from a MiroFish social simulation."""
    simulation_id: str
    social_sentiment_score: float       # -1.0 to 1.0
    adoption_probability: float         # 0.0 to 1.0
    viral_coefficient: float            # Expected spread rate
    resistance_index: float             # 0.0 to 1.0 (higher = more resistance)
    dominant_narrative: str
    minority_narratives: List[str]
    confidence: float                   # 0.0 to 1.0
    simulation_steps: int
    completed_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class PerceptaResult:
    """Output from Percepta economic modeling."""
    simulation_id: str
    true_probability: float             # Percepta's estimated true probability
    expected_value: float               # EV of a $1 bet at current market odds
    kelly_fraction: float               # Optimal position size (Kelly Criterion)
    confidence_interval_low: float
    confidence_interval_high: float
    model_used: str
    key_drivers: List[str]
    completed_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class MiroFishClient:
    """
    Client for the MiroFish multi-agent social simulation engine.
    Constructs parallel digital worlds to model human reactions to events.
    """

    BASE_URL = os.getenv("MIROFISH_API_URL", "http://localhost:8768")

    async def run_simulation(self, sim_input: SimulationInput) -> Optional[MiroFishResult]:
        """Submit a simulation job to MiroFish and wait for results."""
        logger.info(
            f"[MiroFish] Starting simulation {sim_input.simulation_id[:8]} | "
            f"event='{sim_input.event_description[:50]}' | pop={sim_input.population_size:,}"
        )

        payload = {
            "simulation_id": sim_input.simulation_id,
            "event_description": sim_input.event_description,
            "event_category": sim_input.event_category,
            "time_horizon_days": sim_input.time_horizon_days,
            "population_size": sim_input.population_size,
            "raw_data": sim_input.raw_data,
        }

        try:
            import httpx
            async with httpx.AsyncClient() as client:
                # Submit job
                resp = await client.post(
                    f"{self.BASE_URL}/api/simulation/submit",
                    json=payload,
                    timeout=10.0,
                )
                if resp.status_code != 200:
                    raise ValueError(f"MiroFish submission failed: {resp.status_code}")

                job_id = resp.json().get("job_id")

                # Poll for completion
                for _ in range(60):  # Max 5 minutes
                    await asyncio.sleep(5)
                    status_resp = await client.get(
                        f"{self.BASE_URL}/api/simulation/status/{job_id}",
                        timeout=10.0,
                    )
                    status = status_resp.json()
                    if status.get("status") == "complete":
                        result = status.get("result", {})
                        return MiroFishResult(
                            simulation_id=sim_input.simulation_id,
                            social_sentiment_score=result.get("sentiment_score", 0.0),
                            adoption_probability=result.get("adoption_probability", 0.5),
                            viral_coefficient=result.get("viral_coefficient", 1.0),
                            resistance_index=result.get("resistance_index", 0.5),
                            dominant_narrative=result.get("dominant_narrative", ""),
                            minority_narratives=result.get("minority_narratives", []),
                            confidence=result.get("confidence", 0.5),
                            simulation_steps=result.get("steps", 0),
                        )
                    elif status.get("status") == "failed":
                        raise ValueError(f"MiroFish simulation failed: {status.get('error')}")

        except Exception as e:
            logger.error(f"[MiroFish] Simulation error: {e}")
            # Return a conservative fallback result
            return MiroFishResult(
                simulation_id=sim_input.simulation_id,
                social_sentiment_score=0.0,
                adoption_probability=0.5,
                viral_coefficient=1.0,
                resistance_index=0.5,
                dominant_narrative="Simulation unavailable — using neutral priors",
                minority_narratives=[],
                confidence=0.1,
                simulation_steps=0,
            )


class PerceptaClient:
    """
    Client for the Percepta economic simulation framework.
    Translates MiroFish social dynamics into rigorous financial probability distributions.
    """

    BASE_URL = os.getenv("PERCEPTA_API_URL", "http://localhost:8767")

    async def compute_probability(self, sim_input: SimulationInput,
                                   mirofish_result: MiroFishResult) -> Optional[PerceptaResult]:
        """Run Percepta's economic model on a MiroFish simulation result."""
        logger.info(f"[Percepta] Computing probability for simulation {sim_input.simulation_id[:8]}")

        payload = {
            "simulation_id": sim_input.simulation_id,
            "market_question": sim_input.market_question,
            "current_market_odds": sim_input.current_market_odds,
            "time_horizon_days": sim_input.time_horizon_days,
            "social_sentiment_score": mirofish_result.social_sentiment_score,
            "adoption_probability": mirofish_result.adoption_probability,
            "viral_coefficient": mirofish_result.viral_coefficient,
            "resistance_index": mirofish_result.resistance_index,
            "mirofish_confidence": mirofish_result.confidence,
        }

        try:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.BASE_URL}/api/compute",
                    json=payload,
                    timeout=60.0,
                )
                if resp.status_code == 200:
                    result = resp.json()
                    true_prob = result.get("true_probability", 0.5)
                    current_odds = sim_input.current_market_odds
                    ev = (true_prob * (1 / current_odds - 1)) - (1 - true_prob)

                    return PerceptaResult(
                        simulation_id=sim_input.simulation_id,
                        true_probability=true_prob,
                        expected_value=ev,
                        kelly_fraction=max(0, (true_prob - current_odds) / (1 - current_odds)),
                        confidence_interval_low=result.get("ci_low", true_prob - 0.1),
                        confidence_interval_high=result.get("ci_high", true_prob + 0.1),
                        model_used=result.get("model", "percepta-v1"),
                        key_drivers=result.get("key_drivers", []),
                    )
        except Exception as e:
            logger.error(f"[Percepta] Computation error: {e}")
        return None


class SimulationPipeline:
    """
    The complete simulation pipeline: Data → MiroFish → Percepta → Trade Signal.
    This is the primary profit engine of SheldonOS.
    """

    def __init__(self):
        self.mirofish = MiroFishClient()
        self.percepta = PerceptaClient()

    async def run(self, sim_input: SimulationInput) -> Dict[str, Any]:
        """Execute the full simulation pipeline and return a trade recommendation."""
        logger.info(f"[Pipeline] Starting full simulation for: {sim_input.market_question[:60]}")

        # Step 1: MiroFish social simulation
        mirofish_result = await self.mirofish.run_simulation(sim_input)
        if not mirofish_result:
            return {"status": "failed", "stage": "mirofish", "simulation_id": sim_input.simulation_id}

        logger.info(
            f"[MiroFish] Result: sentiment={mirofish_result.social_sentiment_score:.2f} | "
            f"adoption={mirofish_result.adoption_probability:.2f} | "
            f"confidence={mirofish_result.confidence:.2f}"
        )

        # Step 2: Percepta economic modeling
        percepta_result = await self.percepta.compute_probability(sim_input, mirofish_result)
        if not percepta_result:
            return {"status": "failed", "stage": "percepta", "simulation_id": sim_input.simulation_id}

        logger.info(
            f"[Percepta] Result: true_prob={percepta_result.true_probability:.3f} | "
            f"EV={percepta_result.expected_value:.3f} | "
            f"kelly={percepta_result.kelly_fraction:.3f}"
        )

        # Step 3: Generate trade recommendation
        edge = percepta_result.true_probability - sim_input.current_market_odds
        confidence_pct = mirofish_result.confidence * 100

        recommendation = {
            "simulation_id": sim_input.simulation_id,
            "market_question": sim_input.market_question,
            "current_market_odds": sim_input.current_market_odds,
            "true_probability": percepta_result.true_probability,
            "edge": edge,
            "expected_value": percepta_result.expected_value,
            "kelly_fraction": percepta_result.kelly_fraction,
            "confidence_pct": confidence_pct,
            "direction": "long" if edge > 0 else "short",
            "dominant_narrative": mirofish_result.dominant_narrative,
            "key_drivers": percepta_result.key_drivers,
            "recommendation": "EXECUTE" if confidence_pct >= 90 and abs(edge) > 0.10 else
                              "REVIEW" if confidence_pct >= 70 else "PASS",
        }

        logger.info(
            f"[Pipeline] Recommendation: {recommendation['recommendation']} | "
            f"edge={edge:.3f} | confidence={confidence_pct:.1f}%"
        )

        return {"status": "complete", "recommendation": recommendation}
