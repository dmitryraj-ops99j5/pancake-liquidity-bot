import asyncio
import logging
import random
import httpx

logger = logging.getLogger(__name__)


class RpcClient:
    """Minimal JSON-RPC client optimized for batched pair reserve polling."""

    def __init__(self, endpoint: str, timeout: float = 10.0):
        self.endpoint = endpoint
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None
        self._req_id = 0

    async def start(self):
        if not self._client:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                limits=httpx.Limits(max_keepalive_connections=20, max_connections=40),
            )

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    def _next_id(self) -> int:
        self._req_id = (self._req_id + 1) % 10_000_000
        return self._req_id

    async def call(self, to: str, data: str, block: str = "latest") -> str | None:
        res = await self.batch_call([(to, data)], block=block)
        return res[0] if res else None

    async def batch_call(
        self, calls: list[tuple[str, str]], block: str = "latest"
    ) -> list[str | None]:
        if not calls:
            return []

        if not self._client:
            await self.start()

        payloads = [
            {
                "jsonrpc": "2.0",
                "id": self._next_id(),
                "method": "eth_call",
                "params": [{"to": target, "data": call_data}, block],
            }
            for target, call_data in calls
        ]

        for attempt in range(4):
            try:
                assert self._client is not None
                resp = await self._client.post(self.endpoint, json=payloads)
                # print(f"batch response raw: {resp.text}")
                
                if resp.status_code == 429:
                    jitter = random.uniform(0.1, 0.4)
                    await asyncio.sleep(1.0 * (attempt + 1) + jitter)
                    continue
                
                resp.raise_for_status()
                items = resp.json()

                # Some nodes wrap an error object even if HTTP status was 200
                if isinstance(items, dict) and "error" in items:
                    logger.debug("node returned batch level error: %s", items["error"])
                    return [None] * len(calls)

                if not isinstance(items, list):
                    return [None] * len(calls)

                by_id = {}
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    if "result" in item and item["result"] not in (None, "0x"):
                        by_id[item.get("id")] = item["result"]

                return [by_id.get(p["id"]) for p in payloads]
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                if attempt == 3:
                    logger.error("batch call failed after 4 retries: %s", e)
                    return [None] * len(calls)
                jitter = random.uniform(0.05, 0.2)
                await asyncio.sleep(0.3 * (2**attempt) + jitter)
            except Exception as e:
                # Catch parsing hiccups without killing the monitor loop
                logger.warning("unexpected rpc response decode error: %s", e)
                return [None] * len(calls)

        return [None] * len(calls)
