from pancake_liquidity_bot.pool import PoolState, PairTracker


def test_pool_state_drop_calculation():
    prev = PoolState(reserve0=1000 * 10**18, reserve1=300000 * 10**18, block_number=100)
    curr = PoolState(reserve0=700 * 10**18, reserve1=210000 * 10**18, block_number=101)

    drop0 = prev.drop_pct_token0(curr)
    drop1 = prev.drop_pct_token1(curr)

    # 30% drop
    assert round(drop0, 2) == 30.0
    assert round(drop1, 2) == 30.0


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
    assert alert is not None
    assert alert.drop_pct >= 25.0
    assert alert.token_symbol == "CAKE" or alert.token_symbol == "WBNB"
