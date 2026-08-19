import argparse
import asyncio
import logging
import sys

from pancake_liquidity_bot.config import Config
from pancake_liquidity_bot.rpc import RpcClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("pancake_liquidity_bot")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PancakeSwap pair liquidity watcher")
    parser.add_argument("--rpc", help="BSC RPC endpoint URL")
    parser.add_argument("--pairs", help="Comma-separated pair addresses")
    parser.add_argument("--threshold", type=float, help="Drop percentage threshold")
    parser.add_argument("--interval", type=float, help="Polling interval in seconds")
    return parser.parse_args()


async def main_async():
    args = parse_args()
    cfg = Config.from_env()

    if args.rpc:
        cfg.rpc_url = args.rpc
    if args.pairs:
        cfg.pairs = [p.strip() for p in args.pairs.split(",") if p.strip()]
    if args.threshold is not None:
        cfg.drop_threshold_pct = args.threshold
    if args.interval is not None:
        cfg.poll_interval = args.interval

    if not cfg.pairs:
        logger.error("no pair addresses provided via env or --pairs")
        sys.exit(1)

    logger.info("watching %d pairs on %s", len(cfg.pairs), cfg.rpc_url)
    rpc = RpcClient(cfg.rpc_url)
    await rpc.start()

    try:
        while True:
            # FIXME: implement pool state comparison and alerting
            await asyncio.sleep(cfg.poll_interval)
    finally:
        await rpc.close()


def main():
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        logger.info("stopped by user")


if __name__ == "__main__":
    main()
