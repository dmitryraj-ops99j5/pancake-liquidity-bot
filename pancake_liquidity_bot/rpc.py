import asyncio
import logging
import httpx

logger = logging.getLogger(__name__)


class RpcClient:
    def __init__(self, endpoint: str, timeout: float = 10.0):
        self.endpoint = endpoint
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None
        self._req_id = 0

    async def __aenter__(self):
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()

    def _next_id(self) -> int:
        self._req_id += 1
        return self._req_id

    async def call(self, to: str, data: str, block: str = "latest") -> str | None:
        payload = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "eth_call",
            "params": [{"to": to, "data": data}, block],
        }
        for attempt in range(3):
            try:
                assert self._client is not None
                resp = await self._client.post(self.endpoint, json=payload)
                resp.raise_for_status()
                data_json = resp.json()
                if "error" in data_json:
                    logger.warning("rpc error on %s: %s", to, data_json["error"])
                    return None
                return data_json.get("result")
            except Exception as e:
                if attempt == 2:
                    logger.error("failed eth_call after 3 attempts: %s", e)
                    return None
                await asyncio.sleep(0.5 * (attempt + 1))
        return None
