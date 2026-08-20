import pytest
from pancake_liquidity_bot.abi import (
    decode_reserves,
    decode_uint256,
    decode_sync_log,
    encode_method,
    SYNC_TOPIC,
)


def test_encode_method():
    # getReserves() signature is 0x0902f1ac
    assert encode_method("getReserves()") == "0x0902f1ac"
    assert encode_method("token0()") == "0x0dfe1681"
    assert encode_method("token1()") == "0xd21220a7"


def test_decode_uint256():
    raw = "0x0000000000000000000000000000000000000000000000000de0b6b3a7640000"
    assert decode_uint256(raw) == 1000000000000000000


def test_decode_reserves_valid():
    # 100 WBNB (18 decimals) and 30,000 BUSD (18 decimals), block timestamp 1700000000
    # 100 * 10^18 = 0x56bc75e2d63100000
    # 30000 * 10^18 = 0x64bf25b6a05440000
    r0_hex = "0000000000000000000000000000000000000000000000056bc75e2d63100000"
    r1_hex = "000000000000000000000000000000000000000000000064bf25b6a054400000"
    ts_hex = "000000000000000000000000000000000000000000000000000000006553f100"
    raw = "0x" + r0_hex + r1_hex + ts_hex

    r0, r1, ts = decode_reserves(raw)
    assert r0 == 100 * 10**18
    assert r1 == 30000 * 10**18
    assert ts == 1700000000


def test_decode_reserves_short_payload():
    with pytest.raises(ValueError, match="invalid hex length"):
        decode_reserves("0x1234")


def test_decode_sync_log():
    # Sync(uint112 reserve0, uint112 reserve1) has 2 values in data field
    r0_hex = f"{500 * 10**18:064x}"
    r1_hex = f"{150000 * 10**18:064x}"
    data = "0x" + r0_hex + r1_hex

    r0, r1 = decode_sync_log(data)
    assert r0 == 500 * 10**18
    assert r1 == 150000 * 10**18


def test_sync_topic_constant():
    # keccak256('Sync(uint112,uint112)')
    expected = "0x1c411e9a96e071241c2f21f7726b17ae89e3cab4c78be50e062b03a9fffbbad1"
    assert SYNC_TOPIC.lower() == expected
