import logging
import httpx

logger = logging.getLogger("pancake_liquidity_bot.notifier")


class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        self._client = httpx.AsyncClient(timeout=10.0)

    async def send_message(self, text: str) -> bool:
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        try:
            resp = await self._client.post(self.api_url, json=payload)
            if resp.status_code != 200:
                logger.error("tg send failed: %d %s", resp.status_code, resp.text)
                return False
            return True
        except Exception as e:
            logger.error("tg request error: %s", e)
            return False

    async def close(self):
        await self._client.aclose()
