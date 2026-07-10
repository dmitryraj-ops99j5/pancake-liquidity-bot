import os
from dataclasses import dataclass, field


def _split_csv(val: str) -> list[str]:
    if not val:
        return []
    return [item.strip() for item in val.split(",") if item.strip()]


@dataclass
class Config:
    rpc_url: str
    telegram_token: str
    telegram_chat_id: str
    pairs: list[str] = field(default_factory=list)
    poll_interval: float = 3.0
    drop_threshold_pct: float = 15.0

    @classmethod
    def from_env(cls) -> "Config":
        rpc = os.getenv("BSC_RPC_URL", "https://bsc-dataseed.binance.org/")
        token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        pairs_raw = os.getenv("WATCH_PAIRS", "")
        
        interval_raw = os.getenv("POLL_INTERVAL", "3.0")
        threshold_raw = os.getenv("DROP_THRESHOLD_PCT", "15.0")

        return cls(
            rpc_url=rpc,
            telegram_token=token,
            telegram_chat_id=chat_id,
            pairs=_split_csv(pairs_raw),
            poll_interval=float(interval_raw),
            drop_threshold_pct=float(threshold_raw),
        )
