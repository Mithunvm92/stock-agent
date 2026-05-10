import sys

from agents.trading_agent import TradingAgent
from utils.metrics import start_metrics_server

from config.settings import PRIMARY_TICKER


# =========================================
# START METRICS SERVER ONLY ONCE
# =========================================
try:

    start_metrics_server(port=8000)

    print(
        "📊 Prometheus metrics running "
        "on port 8000"
    )

except OSError:

    print(
        "⚠️ Metrics server already running"
    )


# =========================================
# HELPERS
# =========================================
def get_ticker_from_args():

    if "--ticker" in sys.argv:

        idx = sys.argv.index("--ticker")

        if idx + 1 < len(sys.argv):

            return sys.argv[idx + 1]

    return PRIMARY_TICKER


def get_interval_from_args(default=300):

    for arg in sys.argv:

        if arg.isdigit():

            return int(arg)

    return default


# =========================================
# MAIN
# =========================================
def main():

    ticker = get_ticker_from_args()

    print("\n═══════════════════════════════════════")
    print("     STOCK TRADING AGENT — CLI")
    print("═══════════════════════════════════════\n")

    # =====================================
    # TEST
    # =====================================
    if "--test" in sys.argv:

        print("🧪 Running tests...\n")

        agent = TradingAgent(ticker)

        agent.initialize()

    # =====================================
    # TRAIN
    # =====================================
    elif "--train" in sys.argv:

        print("🧠 Training model...\n")

        agent = TradingAgent(ticker)

        agent.initialize()

    # =====================================
    # SIGNAL
    # =====================================
    elif "--signal" in sys.argv:

        print("📡 Generating signal...\n")

        agent = TradingAgent(ticker)

        signal = agent.get_signal()

        print(signal)

    # =====================================
    # SCAN
    # =====================================
    elif "--scan" in sys.argv:

        print("🔍 Scanning stocks...\n")

        from config.settings import TICKERS

        for ticker_name in TICKERS:

            try:

                print(
                    f"\n📈 Scanning {ticker_name}"
                )

                agent = TradingAgent(ticker_name)

                result = agent.get_signal()

                print(result)

            except Exception as e:

                print(
                    f"❌ {ticker_name} | Error: {e}"
                )

    # =====================================
    # BACKTEST
    # =====================================
    elif "--backtest" in sys.argv:

        print("📊 Running backtest...\n")

        agent = TradingAgent(ticker)

        agent.initialize()

    # =====================================
    # PAPER TRADING
    # =====================================
    elif "--paper" in sys.argv:

        print("📝 Starting paper trading...\n")

        interval = get_interval_from_args(300)

        agent = TradingAgent(ticker)

        agent.run_live_loop(
            interval_seconds=interval
        )

    # =====================================
    # LIVE TRADING
    # =====================================
    elif "--live" in sys.argv:

        print("🔴 Starting LIVE trading...\n")

        interval = get_interval_from_args(300)

        agent = TradingAgent(ticker)

        agent.run_live_loop(
            interval_seconds=interval
        )

    # =====================================
    # STATS
    # =====================================
    elif "--stats" in sys.argv:

        print("📊 Portfolio stats...\n")

        agent = TradingAgent(ticker)

        agent.risk_mgr.get_status()

    # =====================================
    # DEFAULT
    # =====================================
    else:

        print("🚀 Running default pipeline...\n")

        agent = TradingAgent(ticker)

        agent.run_live_loop(
            interval_seconds=300
        )


# =========================================
# ENTRY
# =========================================
if __name__ == "__main__":

    main()