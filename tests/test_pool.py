from pancake_liquidity_bot.pool import PoolState, PairTracker


def test_pool_state_drop_calculation():
    prev = PoolState(reserve0=1000 * 10**18, reserve1=300000 * 10**18, block_number=100)
    curr = PoolState(reserve0=700 * 10**18, reserve1=210000 * 10**18, block_number=101)

    drop0 = prev.drop_pct_token0(curr)
    drop1 = prev.drop_pct_token1(curr)

    # 30% drop
    assert round(drop0, 2) == 30.0
    assert round(drop1, 2) == 30.0


