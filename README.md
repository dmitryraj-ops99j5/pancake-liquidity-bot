# pancake-liquidity-bot

Small tool to watch PancakeSwap V2 pool reserves directly over BSC JSON-RPC and ping a Telegram channel when someone pulls liquidity or a major dump happens.

## Setup

```bash
pip install -e .
```

Needs a BSC RPC node URL (public or private like QuickNode/Ankr) and a Telegram bot token if you want alerts.
