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

    async def start(self):
        if not self._client:
            self._client = httpx.AsyncClient(timeout=self.timeout)

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    def _next_id(self) -> int:
        self._req_id += 1
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
                if resp.status_code == 429:
                    # Ankr / QuickNode rate limits need a bit more time to cool off
                    await asyncio.sleep(1.2 * (attempt + 1))
                    continue
                resp.raise_for_status()
                items = resp.json()
                
                if not isinstance(items, list):
                    logger.warning("rpc returned non-list for batch call: %s", items)
                    return [None] * len(calls)

                # Batch responses aren't guaranteed to be in request order
                by_id = {}
                for item in items:
                    if "error" in item:
                        continue
                    by_id[item.get("id")] = item.get("result")

                return [by_id.get(p["id"]) for p in payloads]
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                if attempt == 3:
                    logger.error("batch call failed after 4 tries: %s", e)
                    return [None] * len(calls)
                await asyncio.sleep(0.4 * (2**attempt))

        return [None] * len(calls)
