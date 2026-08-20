import argparse
import asyncio
import logging
import signal
import sys
from pathlib import Path

from pancake_liquidity_bot.config import Config
from pancake_liquidity_bot.notifier import TelegramNotifier
from pancake_liquidity_bot.pool import PoolWatcher
from pancake_liquidity_bot.rpc import RpcClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("pancake_liquidity_bot")


def load_pairs_file(path_str: str) -> list[str]:
    p = Path(path_str)
    if not p.exists():
        raise FileNotFoundError(f"pair list file not found: {path_str}")
    
    pairs = []
    for line in p.read_text().splitlines():
        clean = line.strip()
        if clean and not clean.startswith("#"):
            pairs.append(clean.lower())
    return pairs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PancakeSwap pair liquidity watcher")
    parser.add_argument("--rpc", help="BSC RPC endpoint URL")
    parser.add_argument("--pairs", help="Comma-separated pair addresses")
    parser.add_argument("--pairs-file", help="Path to file with pair addresses (one per line)")
    parser.add_argument("--threshold", type=float, help="Drop percentage threshold for alert")
    parser.add_argument("--interval", type=float, help="Polling interval in seconds")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")
    return parser


async def main_async():
    parser = build_parser()
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    cfg = Config.from_env()

    if args.rpc:
        cfg.rpc_url = args.rpc
    if args.pairs:
        cfg.pairs = [p.strip().lower() for p in args.pairs.split(",") if p.strip()]
    elif args.pairs_file:
        cfg.pairs = load_pairs_file(args.pairs_file)

    if args.threshold is not None:
        cfg.drop_threshold_pct = args.threshold
    if args.interval is not None:
        cfg.poll_interval = args.interval

    if not cfg.pairs:
        logger.error("no pairs to watch, pass --pairs or --pairs-file or set WATCH_PAIRS")
        sys.exit(1)

    rpc = RpcClient(cfg.rpc_url, timeout=cfg.http_timeout)
    notifier = TelegramNotifier(
        token=cfg.telegram_token,
        chat_id=cfg.telegram_chat_id,
        cooldown_sec=cfg.min_alert_interval_sec,
    )
    watcher = PoolWatcher(rpc=rpc, notifier=notifier, config=cfg)

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop_event.set)
        except NotImplementedError:
            # Windows doesn't support add_signal_handler
            pass

    logger.info("starting watcher for %d pairs (interval: %.1fs)", len(cfg.pairs), cfg.poll_interval)
    
    await rpc.start()
    await notifier.start()

    try:
        # Pre-fetch token metadata on startup so alerts have human readable symbols
        await watcher.initialize_pairs(cfg.pairs)
        
        while not stop_event.is_set():
            try:
                await watcher.poll_once()
            except Exception as e:
                logger.error("error during poll cycle: %s", e, exc_info=args.verbose)

            try:
                await asyncio.wait_for(stop_event.wait(), timeout=cfg.poll_interval)
            except asyncio.TimeoutError:
                pass
    finally:
        logger.info("shutting down...")
        await watcher.close()
        await notifier.close()
        await rpc.close()


def main():
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
