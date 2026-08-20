import asyncio
import logging
import time
from typing import Dict
import httpx

logger = logging.getLogger("pancake_liquidity_bot.notifier")


class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str, cooldown_seconds: int = 120):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.cooldown_seconds = cooldown_seconds
        self.api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        self._client = httpx.AsyncClient(timeout=10.0)
        # pair_address -> last_alert_timestamp
        self._last_alert_time: Dict[str, float] = {}

    def should_alert(self, pair: str) -> bool:
        pair_key = pair.lower()
        last = self._last_alert_time.get(pair_key, 0.0)
        now = time.time()
        if now - last < self.cooldown_seconds:
            return False
        return True

    def mark_alerted(self, pair: str):
        self._last_alert_time[pair.lower()] = time.time()

    async def send_message(self, text: str) -> bool:
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }

        # retry once on 429 rate limit
        for attempt in range(2):
            try:
                resp = await self._client.post(self.api_url, json=payload)
                if resp.status_code == 429:
                    retry_after = 3
                    try:
                        data = resp.json()
                        retry_after = data.get("parameters", {}).get("retry_after", 3)
                    except Exception:
                        pass
                    logger.warning("tg 429 rate limited, sleeping %ds", retry_after)
                    await asyncio.sleep(retry_after)
                    continue

                if resp.status_code != 200:
                    logger.error("tg send failed: %d %s", resp.status_code, resp.text)
                    return False
                return True
            except httpx.RequestError as e:
                logger.error("tg network error: %s", e)
                return False
            except Exception as e:
                logger.error("tg unexpected error: %s", e)
                return False
        return False

    async def send_pool_alert(self, alert_data: dict) -> bool:
        pair = alert_data["pair"]
        if not self.should_alert(pair):
            logger.debug("skipping alert for %s due to cooldown", pair)
            return False

        s0 = alert_data.get("symbol0", "TOKEN0")
        s1 = alert_data.get("symbol1", "TOKEN1")
        d0 = alert_data.get("drop0_pct", 0.0)
        d1 = alert_data.get("drop1_pct", 0.0)
        block = alert_data.get("block", 0)
        is_drained = alert_data.get("is_drained", False)

        status_header = "🚨 <b>POOL DRAINED</b>" if is_drained else "⚠️ <b>LIQUIDITY DROP DETECTED</b>"

        lines = [
            status_header,
            f"<b>Pair:</b> {s0} / {s1}",
            f"<b>Address:</b> <code>{pair}</code>",
            f"<b>Block:</b> {block}",
            "",
            f"<b>{s0} Drop:</b> -{d0:.2f}%",
            f"<b>{s1} Drop:</b> -{d1:.2f}%",
            f"<b>Peak Drop:</b> -{max(alert_data.get('peak_drop0_pct', 0.0), alert_data.get('peak_drop1_pct', 0.0)):.2f}%",
            "",
            f"<a href=\"https://bscscan.com/address/{pair}\">View on BscScan</a>",
        ]

        msg = "\n".join(lines)
        sent = await self.send_message(msg)
        if sent:
            self.mark_alerted(pair)
        return sent

    async def close(self):
        await self._client.aclose()
