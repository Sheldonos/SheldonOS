"""Configuration loader for the Polymarket trading agent."""
import os
import yaml
from typing import Any, Dict


def load_config(config_path: str = "config/config.yaml") -> Dict[str, Any]:
    """Load YAML configuration file, with environment variable overrides."""
    if not os.path.exists(config_path):
        # Try relative to this file's directory
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(base, config_path)

    with open(config_path, "r", encoding="utf-8") as fh:
        config = yaml.safe_load(fh) or {}

    # Environment variable overrides
    _apply_env_overrides(config)
    return config


def _apply_env_overrides(config: Dict[str, Any]) -> None:
    """Apply environment variable overrides to config."""
    env_map = {
        "OPENAI_API_KEY": ("llm", "api_key"),
        "ANTHROPIC_API_KEY": ("llm", "api_key"),
        "LLM_API_KEY": ("llm", "api_key"),
        "LLM_MODEL": ("llm", "model"),
        "LLM_BASE_URL": ("llm", "base_url"),
        "POLYMARKET_API_KEY": ("polymarket", "api_key"),
        "SIMULATION_MODE": ("agent", "simulation_mode"),
    }
    for env_var, (section, key) in env_map.items():
        val = os.environ.get(env_var)
        if val is not None:
            if section not in config:
                config[section] = {}
            # Type coercion
            if key == "simulation_mode":
                config[section][key] = val.lower() in ("true", "1", "yes")
            else:
                config[section][key] = val
