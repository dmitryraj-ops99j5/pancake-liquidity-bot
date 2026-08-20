from pancake_liquidity_bot.pool import PoolState, PairTracker


def test_pool_state_drop_calculation():
    prev = PoolState(reserve0=1000 * 10**18, reserve1=300000 * 10**18, block_number=100)
    curr = PoolState(reserve0=700 * 10**18, reserve1=210000 * 10**18, block_number=101)

    drop0 = prev.drop_pct_token0(curr)
    drop1 = prev.drop_pct_token1(curr)

    # 30% drop
    assert round(drop0, 2) == 30.0
    assert round(drop1, 2) == 30.0


def test_pool_state_zero_reserves_drain():
    prev = PoolState(reserve0=500 * 10**18, reserve1=100 * 10**18, block_number=500)
    # total pool drain
    curr = PoolState(reserve0=0, reserve1=0, block_number=501)

    assert prev.drop_pct_token0(curr) == 100.0
    assert prev.drop_pct_token1(curr) == 100.0


def test_pool_state_initial_zero_no_crash():
    # edge case: newly created empty pair
    prev = PoolState(reserve0=0, reserve1=0, block_number=1)
    curr = PoolState(reserve0=100 * 10**18, reserve1=10 * 10**18, block_number=2)

    assert prev.drop_pct_token0(curr) == 0.0
    assert prev.drop_pct_token1(curr) == 0.0


def test_tracker_trigger_threshold():
    tracker = PairTracker(
        pair_address="0x0eD7e52944161450477ee4070dA623002f1B7E20",
        token0_symbol="CAKE",
        token1_symbol="WBNB",
        token0_decimals=18,
        token1_decimals=18,
        drop_threshold_pct=15.0,
    )

    # initial block
    tracker.update(reserve0=1000 * 10**18, reserve1=50 * 10**18, block_number=1000)
    assert tracker.last_alert_block is None

    # small trade, 5% drop - no trigger
    alert = tracker.update(reserve0=950 * 10**18, reserve1=475 * 10**17, block_number=1001)
    assert alert is None

    # big rug/dump, 25% drop
    alert = tracker.update(reserve0=700 * 10**18, reserve1=35 * 10**18, block_number=1002)
    # print(f"debug alert: {alert}")
    assert alert is not None
    assert alert.drop_pct >= 25.0
    assert tracker.last_alert_block == 1002

    # same block or immediate next block should respect debounce if configured
    alert_next = tracker.update(reserve0=690 * 10**18, reserve1=34 * 10**18, block_number=1003)
    assert alert_next is None
