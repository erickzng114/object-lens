import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    # Model names live in config, not code (CLAUDE.md).
    query_model: str = os.environ.get("QUERY_MODEL", "claude-haiku-5-5")
    identify_model: str = os.environ.get("IDENTIFY_MODEL", "claude-sonnet-5-5")
    shop_timeout_seconds: float = float(os.environ.get("SHOP_TIMEOUT_SECONDS", "8"))
    results_per_shop: int = int(os.environ.get("RESULTS_PER_SHOP", "10"))


settings = Settings()
