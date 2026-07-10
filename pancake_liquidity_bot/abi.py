# Uniswap V2 / PancakeSwap pair selectors
GET_RESERVES_SIG = "0x0902f1ac"
TOKEN0_SIG = "0x0dfe1681"
TOKEN1_SIG = "0xd21220a7"


def decode_reserves(hex_str: str) -> tuple[int, int, int]:
    raw = hex_str[2:] if hex_str.startswith("0x") else hex_str
    if len(raw) < 192:
        raise ValueError(f"unexpected getReserves return length: {len(raw)}")
    
    # uint112 reserve0, uint112 reserve1, uint32 blockTimestampLast
    r0 = int(raw[0:64], 16)
    r1 = int(raw[64:128], 16)
    ts = int(raw[128:192], 16)
    return r0, r1, ts
