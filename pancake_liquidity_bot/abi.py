# Uniswap V2 / PancakeSwap pair selectors
GET_RESERVES_SIG = "0x0902f1ac"
TOKEN0_SIG = "0x0dfe1681"
TOKEN1_SIG = "0xd21220a7"
DECIMALS_SIG = "0x313ce567"
SYMBOL_SIG = "0x95d89b41"


def decode_reserves(hex_str: str) -> tuple[int, int, int]:
    raw = hex_str[2:] if hex_str.startswith("0x") else hex_str
    if len(raw) < 192:
        raise ValueError(f"unexpected getReserves return length: {len(raw)}")
    
    # uint112 reserve0, uint112 reserve1, uint32 blockTimestampLast
    r0 = int(raw[0:64], 16)
    r1 = int(raw[64:128], 16)
    ts = int(raw[128:192], 16)
    return r0, r1, ts


def decode_address(hex_str: str) -> str:
    raw = hex_str[2:] if hex_str.startswith("0x") else hex_str
    if len(raw) < 40:
        raise ValueError("invalid address hex length")
    addr = raw[-40:]
    return f"0x{addr.lower()}"


def decode_uint256(hex_str: str) -> int:
    raw = hex_str[2:] if hex_str.startswith("0x") else hex_str
    return int(raw, 16) if raw else 0


def decode_symbol(hex_str: str) -> str:
    raw = hex_str[2:] if hex_str.startswith("0x") else hex_str
    if not raw:
        return "UNKNOWN"

    # Old/broken BSC tokens sometimes return bytes32 instead of ABI string
    if len(raw) == 64:
        try:
            raw_bytes = bytes.fromhex(raw)
            return raw_bytes.rstrip(b"\x00").decode("utf-8", errors="replace").strip()
        except Exception:
            return "UNKNOWN"

    try:
        # Standard string: offset (32 bytes) + length (32 bytes) + data
        length = int(raw[64:128], 16)
        data_hex = raw[128 : 128 + length * 2]
        return bytes.fromhex(data_hex).decode("utf-8", errors="replace").strip()
    except Exception:
        return "UNKNOWN"
