import sys
from pancake_liquidity_bot.cli import main

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        # clean exit on ctrl-c without noisy traceback
        sys.exit(130)
