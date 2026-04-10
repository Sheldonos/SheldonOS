"""
LLM Reasoning Client
Provides user-configurable LLM integration following hermes-agent patterns.
Supports OpenAI, Anthropic, Ollama, and OpenRouter providers.
"""
import os
import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Flexible LLM client that supports multiple providers.
    Users configure their preferred LLM via config.yaml and environment variables.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        llm_cfg = config.get("llm", {})
        self.provider = llm_cfg.get("provider", "openai")
        self.model = llm_cfg.get("model", "gpt-4.1-mini")
        self.max_tokens = llm_cfg.get("max_tokens", 4096)
        self.temperature = llm_cfg.get("temperature", 0.1)

        # Resolve API key
        api_key_env = llm_cfg.get("api_key_env", "OPENAI_API_KEY")
        self.api_key = os.environ.get(api_key_env, os.environ.get("OPENAI_API_KEY", ""))

        # Resolve base URL
        base_url = llm_cfg.get("base_url")
        if base_url is None:
            base_url = self._default_base_url()
        self.base_url = base_url

        self._client = None
        logger.info(f"LLMClient configured: provider={self.provider}, model={self.model}")

    def _default_base_url(self) -> Optional[str]:
        """Return default base URL for the configured provider."""
        provider_urls = {
            "openai": None,  # Use OpenAI default
            "anthropic": None,
            "ollama": "http://localhost:11434/v1",
            "openrouter": "https://openrouter.ai/api/v1",
        }
        return provider_urls.get(self.provider)

    def _get_client(self):
        """Lazily initialize the OpenAI-compatible client."""
        if self._client is None:
            from openai import OpenAI
            kwargs = {"api_key": self.api_key or "dummy"}
            if self.base_url:
                kwargs["base_url"] = self.base_url
            self._client = OpenAI(**kwargs)
        return self._client

    def reason(
        self,
        system_prompt: str,
        user_message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Send a reasoning request to the LLM.
        Returns the model's text response.
        """
        messages = [{"role": "system", "content": system_prompt}]
        if context:
            messages.append({
                "role": "user",
                "content": f"Context:\n{json.dumps(context, indent=2, default=str)}\n\n{user_message}",
            })
        else:
            messages.append({"role": "user", "content": user_message})

        try:
            client = self._get_client()
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"LLM reasoning error: {e}")
            return ""

    def analyze_trade_opportunity(
        self,
        market: Dict[str, Any],
        forecast: Dict[str, Any],
        signals: Optional[Dict[str, Any]],
        risk_assessment: Dict[str, Any],
        portfolio_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Use the LLM to analyze a potential trade opportunity and provide
        a structured recommendation.
        """
        system_prompt = """You are an expert quantitative analyst specializing in prediction markets.
Your role is to analyze trading opportunities on Polymarket and provide structured recommendations.
You must be conservative, data-driven, and always prioritize capital preservation.

Respond ONLY with a valid JSON object matching this exact schema:
{
  "recommendation": "BUY_YES" | "BUY_NO" | "SKIP",
  "confidence": <float 0-1>,
  "reasoning": "<concise explanation>",
  "key_risks": ["<risk1>", "<risk2>"],
  "suggested_position_pct": <float 0-0.05>,
  "edge_estimate": <float -1 to 1>
}"""

        context = {
            "market_title": market.get("question", ""),
            "market_id": market.get("id", ""),
            "current_yes_price": forecast.get("current_price", 0.5),
            "predicted_yes_price": forecast.get("predicted_price", 0.5),
            "model_direction": forecast.get("direction", "neutral"),
            "model_confidence": forecast.get("confidence", 0.5),
            "model_uncertainty": forecast.get("uncertainty_std", 0.1),
            "polyterm_signals": signals,
            "risk_grade": risk_assessment.get("overall_grade", "C"),
            "risk_score": risk_assessment.get("overall_score", 50),
            "market_liquidity": market.get("liquidity", 0),
            "market_volume_24h": market.get("volume24hr", 0),
            "days_to_resolution": market.get("days_to_resolution", 30),
            "open_positions": portfolio_context.get("open_positions", 0),
            "available_bankroll": portfolio_context.get("available_bankroll", 0),
        }

        response = self.reason(system_prompt, "Analyze this trade opportunity:", context)

        try:
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}")

        # Fallback: conservative skip
        return {
            "recommendation": "SKIP",
            "confidence": 0.0,
            "reasoning": "LLM analysis failed",
            "key_risks": ["analysis_error"],
            "suggested_position_pct": 0.0,
            "edge_estimate": 0.0,
        }

    def generate_market_narrative(
        self,
        market: Dict[str, Any],
        signals: Dict[str, Any],
        forecast: Dict[str, Any],
    ) -> str:
        """Generate a human-readable narrative about a market opportunity."""
        system_prompt = """You are a concise prediction market analyst. 
Write a 2-3 sentence narrative explaining why this market is or is not an interesting trading opportunity.
Focus on the key signals and the model's forecast."""

        context = {
            "market": market.get("question", ""),
            "current_price": forecast.get("current_price", 0.5),
            "forecast": forecast.get("predicted_price", 0.5),
            "direction": forecast.get("direction", "neutral"),
            "signals": signals,
        }
        return self.reason(system_prompt, "Write the market narrative:", context)
