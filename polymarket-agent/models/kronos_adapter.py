"""
Kronos Forecasting Adapter
Wraps the Kronos time-series transformer model to generate price forecasts
for Polymarket binary prediction markets.

Kronos was designed for OHLCV financial data. For binary prediction markets,
we map the YES price as the "close" price and derive synthetic OHLV features
from the price history.
"""
import sys
import logging
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

# Add Kronos to path
sys.path.insert(0, "/home/ubuntu/Kronos")

logger = logging.getLogger(__name__)

# Lazy imports to avoid loading heavy torch models at startup
_kronos_loaded = False
_tokenizer = None
_model = None
_predictor = None


def _load_kronos(config: Dict[str, Any]) -> bool:
    """Lazily load Kronos model and tokenizer."""
    global _kronos_loaded, _tokenizer, _model, _predictor
    if _kronos_loaded:
        return True
    try:
        from model import Kronos, KronosTokenizer, KronosPredictor
        kronos_cfg = config.get("kronos", {})
        tokenizer_model = kronos_cfg.get("tokenizer_model", "NeoQuasar/Kronos-Tokenizer-base")
        predictor_model = kronos_cfg.get("predictor_model", "NeoQuasar/Kronos-small")
        max_context = kronos_cfg.get("max_context", 512)

        logger.info(f"Loading Kronos tokenizer: {tokenizer_model}")
        _tokenizer = KronosTokenizer.from_pretrained(tokenizer_model)
        logger.info(f"Loading Kronos model: {predictor_model}")
        _model = Kronos.from_pretrained(predictor_model)
        _predictor = KronosPredictor(_model, _tokenizer, max_context=max_context)
        _kronos_loaded = True
        logger.info("Kronos model loaded successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to load Kronos model: {e}")
        return False


def price_history_to_ohlcv(
    price_history: List[Dict[str, Any]],
    resample_minutes: int = 60,
) -> pd.DataFrame:
    """
    Convert Polymarket price history (list of {t, p} dicts) to OHLCV DataFrame.

    Since prediction markets only have a single price (YES probability),
    we synthesize OHLCV features:
    - open: first price in period
    - high: max price in period
    - low: min price in period
    - close: last price in period (= YES probability)
    - volume: synthetic (set to 1.0, overridden if volume data available)
    - amount: synthetic (= close * volume)
    """
    if not price_history:
        return pd.DataFrame()

    records = []
    for item in price_history:
        ts = item.get("t")
        price = item.get("p")
        if ts is None or price is None:
            continue
        try:
            ts_dt = datetime.utcfromtimestamp(float(ts))
            price_f = float(price)
            records.append({"timestamps": ts_dt, "price": price_f})
        except (ValueError, TypeError):
            continue

    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records).sort_values("timestamps").reset_index(drop=True)
    df = df.set_index("timestamps")

    # Resample to desired frequency
    freq = f"{resample_minutes}min"
    ohlcv = df["price"].resample(freq).ohlc()
    ohlcv.columns = ["open", "high", "low", "close"]
    ohlcv["volume"] = 1.0  # Synthetic volume
    ohlcv["amount"] = ohlcv["close"] * ohlcv["volume"]
    ohlcv = ohlcv.dropna().reset_index()
    ohlcv = ohlcv.rename(columns={"timestamps": "timestamps"})

    return ohlcv


class KronosForecastAdapter:
    """
    Adapter that uses the Kronos model to forecast Polymarket price movements.
    Provides probabilistic forecasts with uncertainty estimates.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.kronos_cfg = config.get("kronos", {})
        self._loaded = False

    def ensure_loaded(self) -> bool:
        """Ensure Kronos model is loaded."""
        if not self._loaded:
            self._loaded = _load_kronos(self.config)
        return self._loaded

    def forecast(
        self,
        price_history: List[Dict[str, Any]],
        market_id: str = "",
        resample_minutes: int = 60,
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a price forecast for a Polymarket market.

        Args:
            price_history: List of {t: timestamp, p: price} dicts from CLOB API
            market_id: Market identifier for logging
            resample_minutes: Resampling frequency in minutes

        Returns:
            Forecast dict with predicted prices, direction, confidence, and
            uncertainty estimates, or None if insufficient data.
        """
        if not self.ensure_loaded():
            logger.warning("Kronos not loaded, using fallback forecaster")
            return self._fallback_forecast(price_history)

        ohlcv = price_history_to_ohlcv(price_history, resample_minutes)
        if len(ohlcv) < 50:
            logger.debug(f"Insufficient data for Kronos ({len(ohlcv)} periods), using fallback")
            return self._fallback_forecast(price_history)

        try:
            pred_len = self.kronos_cfg.get("pred_len", 60) // resample_minutes
            pred_len = max(1, min(pred_len, 24))
            lookback = min(len(ohlcv), self.kronos_cfg.get("lookback_periods", 400))

            x_df = ohlcv.iloc[-lookback:][["open", "high", "low", "close", "volume", "amount"]]
            x_timestamp = ohlcv.iloc[-lookback:]["timestamps"]

            # Generate future timestamps
            last_ts = ohlcv["timestamps"].iloc[-1]
            y_timestamps = pd.date_range(
                start=last_ts + pd.Timedelta(minutes=resample_minutes),
                periods=pred_len,
                freq=f"{resample_minutes}min",
            )
            y_timestamp = pd.Series(y_timestamps)

            sample_count = self.kronos_cfg.get("sample_count", 5)
            all_preds = []
            for _ in range(sample_count):
                pred_df = _predictor.predict(
                    df=x_df.reset_index(drop=True),
                    x_timestamp=x_timestamp.reset_index(drop=True),
                    y_timestamp=y_timestamp,
                    pred_len=pred_len,
                    T=self.kronos_cfg.get("temperature", 1.0),
                    top_p=self.kronos_cfg.get("top_p", 0.9),
                    sample_count=1,
                    verbose=False,
                )
                all_preds.append(pred_df["close"].values)

            preds_array = np.array(all_preds)  # (sample_count, pred_len)
            mean_pred = np.mean(preds_array, axis=0)
            std_pred = np.std(preds_array, axis=0)

            current_price = float(ohlcv["close"].iloc[-1])
            final_pred = float(np.clip(mean_pred[-1], 0.01, 0.99))
            final_std = float(std_pred[-1])

            direction = "bullish" if final_pred > current_price else "bearish"
            price_change = final_pred - current_price
            # Confidence: inversely proportional to uncertainty
            confidence = float(np.clip(1.0 - (final_std / 0.15), 0.1, 0.95))

            return {
                "market_id": market_id,
                "current_price": current_price,
                "predicted_price": final_pred,
                "price_change": price_change,
                "price_change_pct": price_change / max(current_price, 0.01) * 100,
                "direction": direction,
                "confidence": confidence,
                "uncertainty_std": final_std,
                "forecast_horizon_periods": pred_len,
                "forecast_horizon_minutes": pred_len * resample_minutes,
                "mean_trajectory": mean_pred.tolist(),
                "std_trajectory": std_pred.tolist(),
                "model": "kronos",
                "data_points_used": len(ohlcv),
            }

        except Exception as e:
            logger.error(f"Kronos forecast error for {market_id}: {e}")
            return self._fallback_forecast(price_history)

    def _fallback_forecast(
        self, price_history: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Statistical fallback forecaster when Kronos is unavailable.
        Uses momentum, mean reversion, and volatility signals.
        """
        if len(price_history) < 10:
            return None

        prices = []
        for item in price_history[-200:]:
            try:
                prices.append(float(item.get("p", 0)))
            except (ValueError, TypeError):
                pass

        if len(prices) < 10:
            return None

        prices = np.array(prices)
        current_price = prices[-1]

        # Short-term momentum (last 10 periods)
        momentum_10 = (prices[-1] - prices[-10]) / max(prices[-10], 0.01)
        # Medium-term momentum (last 30 periods)
        momentum_30 = (prices[-1] - prices[-30]) / max(prices[-30], 0.01) if len(prices) >= 30 else 0
        # Mean reversion signal
        mean_price = np.mean(prices[-50:]) if len(prices) >= 50 else np.mean(prices)
        mean_reversion = (mean_price - current_price) / max(current_price, 0.01)
        # Volatility
        returns = np.diff(prices[-50:]) / np.maximum(prices[-51:-1], 0.01) if len(prices) >= 51 else np.diff(prices) / np.maximum(prices[:-1], 0.01)
        volatility = float(np.std(returns)) if len(returns) > 0 else 0.02

        # Ensemble signal
        signal = 0.5 * momentum_10 + 0.2 * momentum_30 + 0.3 * mean_reversion
        predicted_change = signal * 0.5  # Dampened prediction
        predicted_price = float(np.clip(current_price + predicted_change, 0.01, 0.99))

        direction = "bullish" if predicted_price > current_price else "bearish"
        confidence = float(np.clip(0.5 + abs(signal) * 2, 0.3, 0.75))

        return {
            "market_id": "",
            "current_price": float(current_price),
            "predicted_price": predicted_price,
            "price_change": predicted_price - float(current_price),
            "price_change_pct": (predicted_price - float(current_price)) / max(float(current_price), 0.01) * 100,
            "direction": direction,
            "confidence": confidence,
            "uncertainty_std": volatility,
            "forecast_horizon_periods": 1,
            "forecast_horizon_minutes": 60,
            "mean_trajectory": [predicted_price],
            "std_trajectory": [volatility],
            "model": "statistical_fallback",
            "data_points_used": len(prices),
        }
