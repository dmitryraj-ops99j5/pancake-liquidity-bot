# pancake-liquidity-bot

Tracks PancakeSwap pair reserves directly via raw BSC JSON-RPC calls without pulling heavy web3 dependencies. When pool reserves drop past a configurable threshold between polling cycles, it shoots an alert to Telegram.

## Requirements

- Python 3.10+
- Working BSC JSON-RPC endpoint
- Telegram Bot token & chat ID (optional if running in dry-run mode)

## Install

```bash
git clone https://github.com/username/pancake-liquidity-bot.git
cd pancake-liquidity-bot
pip install -e .
```

## Configuration

Set environment variables or drop them in a `.env` file:

```env
BSC_RPC_URL=https://bsc-dataseed.binance.org/
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_CHAT_ID=-1001234567890
POLL_INTERVAL=6.0
DROP_THRESHOLD_PCT=15.0
```

## Running

Watch a single pair (e.g. WBNB/BUSD):

```bash
python -m pancake_liquidity_bot --pair 0x58F876857a02D6762E0101bb5C46A8c1ED44Dc16
```

Or pass multiple pairs and custom threshold:

```bash
pancake-watcher --pair 0x... --pair 0x... --drop-threshold 20.0 --interval 3.0
```

<!-- generated: 2026-09-08 -->
