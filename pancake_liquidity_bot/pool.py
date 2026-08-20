import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class PoolSnapshot:
    reserve0: int
    reserve1: int
    block_number: int
    timestamp: float


class PairWatcher:
    """Tracks reserve history for one pair and detects sudden liquidity drains."""

    def __init__(
        self,
        pair_address: str,
        symbol0: str,
        symbol1: str,
        drop_threshold_pct: float = 20.0,
        token0_decimals: int = 18,
        token1_decimals: int = 18,
    ):
        self.pair_address = pair_address.lower()
        self.symbol0 = symbol0
        self.symbol1 = symbol1
        self.decimals0 = token0_decimals
        self.decimals1 = token1_decimals
        self.drop_threshold_pct = drop_threshold_pct

        self.last_snapshot: Optional[PoolSnapshot] = None
        self.peak_reserve0: int = 0
        self.peak_reserve1: int = 0

    def update(self, r0: int, r1: int, block_number: int) -> Optional[dict]:
        now = time.time()
        current = PoolSnapshot(reserve0=r0, reserve1=r1, block_number=block_number, timestamp=now)

        if self.last_snapshot is None:
            self.last_snapshot = current
            self.peak_reserve0 = r0
            self.peak_reserve1 = r1
            return None

        # skip duplicate block updates if we poll faster than bsc 3s slot
        if block_number <= self.last_snapshot.block_number:
            return None

        # update high water marks if pool grew
        if r0 > self.peak_reserve0:
            self.peak_reserve0 = r0
        if r1 > self.peak_reserve1:
            self.peak_reserve1 = r1

        drop0 = self._calc_drop(self.last_snapshot.reserve0, r0)
        drop1 = self._calc_drop(self.last_snapshot.reserve1, r1)
        peak_drop0 = self._calc_drop(self.peak_reserve0, r0)
        peak_drop1 = self._calc_drop(self.peak_reserve1, r1)

        # print(f"DEBUG: {self.pair_address} drop0={drop0:.2f}% drop1={drop1:.2f}%")

        max_step_drop = max(drop0, drop1)
        max_peak_drop = max(peak_drop0, peak_drop1)

        alert = None
        # trigger if single-step or cumulative peak drop exceeds threshold
        if max_step_drop >= self.drop_threshold_pct or max_peak_drop >= self.drop_threshold_pct:
            alert = {
                "pair": self.pair_address,
                "symbol0": self.symbol0,
                "symbol1": self.symbol1,
                "prev_r0": self.last_snapshot.reserve0,
                "prev_r1": self.last_snapshot.reserve1,
                "new_r0": r0,
                "new_r1": r1,
                "drop0_pct": drop0,
                "drop1_pct": drop1,
                "peak_drop0_pct": peak_drop0,
                "peak_drop1_pct": peak_drop1,
                "block": block_number,
                "is_drained": (r0 == 0 or r1 == 0),
            }

            # reset peak after alert so we don't keep firing if pool stays dead
            if r0 == 0 or r1 == 0:
                self.peak_reserve0 = r0
                self.peak_reserve1 = r1

        self.last_snapshot = current
        return alert

    def _calc_drop(self, before: int, after: int) -> float:
        if before <= 0:
            return 0.0
        if after >= before:
            return 0.0
        return ((before - after) / before) * 100.0

    # FIXME: format_amount should probably live in an helpers module
    def format_reserves(self, r0: int, r1: int) -> tuple[str, str]:
        val0 = f"{r0 / (10 ** self.decimals0):,.4f} {self.symbol0}"
        val1 = f"{r1 / (10 ** self.decimals1):,.4f} {self.symbol1}"
        return val0, val1
