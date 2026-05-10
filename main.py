from dotenv import load_dotenv

load_dotenv()

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

except OSError as e:
    # Added logging for the exception caught during starting of the server.
    sys.stderr.write(f"⚠️ Metrics server already running or encountered an error: {e}\n")

# =========================================
# HELPERS
# =========================================
def get_ticker_from_args():

    if "--ticker" in sys.argv:

        idx = sys.argv.index("--ticker")

        if idx + 1 < len(sys.argv):
            return sys.argv[idx + 1]

    # Added a default ticker value to handle cases where the --ticker argument is not provided.
    return PRIMARY_TICKER


def get_interval_from_args(default=300):

    for arg in sys.argv:

        try:
            if arg.isdigit():

                return int(arg)
        except ValueError:  # Catching exceptions when converting arguments that are supposed to be integers but aren't
            pass

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

        try:
            print("🧪 Running tests...\n")

            agent = TradingAgent(ticker)

            agent.initialize()

        except Exception as e:  # Added exception handling for potential runtime crashes during initialization.
            sys.stderr.write(f"❌ Test failed due to an error: {e}\n")
        else:

            print(agent.get_results())

    # =====================================
    # TRAIN
    # =====================================
    elif "--train" in sys.argv:

        try:
            print("🧠 Training model...\n")

            agent = TradingAgent(ticker)

            agent.initialize()

        except Exception as e:  # Added exception handling for potential runtime crashes during initialization.
            sys.stderr.write(f"❌ Model training failed due to an error: {e}\n")
        else:

            print(agent.get_results())

    # =====================================
    # SIGNAL
    # =====================================
    elif "--signal" in sys.argv:

        try:
            print("📡 Generating signal...\n")

            agent = TradingAgent(ticker)

            signal = agent.get_signal()

            if not isinstance(signal, str):
                raise ValueError("Signal generation returned an unexpected type.")

            print(f"{signal}\n")
        except Exception as e:  # Added exception handling for potential runtime crashes.
            sys.stderr.write(f"❌ Signal generation failed due to an error: {e}\n")

    # =====================================
    # SCAN
    # =====================================
    elif "--scan" in sys.argv:

        try:
            print("🔍 Scanning stocks...\n")

            from config.settings import TICKERS

            for ticker_name in TICKERS:

                agent = TradingAgent(ticker_name)

                result = agent.get_signal()

                if not isinstance(result, str):
                    raise ValueError(f"Signal generation returned an unexpected type for {ticker_name}.")

                print(result)
        except Exception as e:  # Added exception handling to catch and log any errors during scanning.
            sys.stderr.write(f"❌ Scanning failed due to an error with ticker '{ticker_name}': {e}\n")

    # =====================================
    # BACKTEST
    # =====================================
    elif "--backtest" in sys.argv:

        try:
            print("📊 Running backtest...\n")

            agent = TradingAgent(ticker)

            agent.initialize()

        except Exception as e:  # Added exception handling for potential runtime crashes.
            sys.stderr.write(f"❌ Backtesting failed due to an error: {e}\n")
        else:

            print(agent.get_results())

    # =====================================
    # PAPER TRADING
    # =====================================
    elif "--paper" in sys.argv:

        try:
            interval = get_interval_from_args(300)

            agent = TradingAgent(ticker)

            if not isinstance(interval, int):
                raise ValueError("Paper trading interval must be an integer.")

            agent.run_live_loop(
                interval_seconds=interval
            )

        except Exception as e:  # Added exception handling for potential runtime crashes.
            sys.stderr.write(f"❌ Paper trading failed due to an error: {e}\n")
        else:

            print(agent.get_results())

    # =====================================
    # LIVE TRADING
    # =====================================
    elif "--live" in sys.argv:

        try:
            interval = get_interval_from_args(300)

            agent = TradingAgent(ticker)

            if not isinstance(interval, int):
                raise ValueError("Live trading interval must be an integer.")

            agent.run_live_loop(
                interval_seconds=interval
            )

        except Exception as e:  # Added exception handling for potential runtime crashes.
            sys.stderr.write(f"❌ Live trading failed due to an error: {e}\n")
        else:

            print(agent.get_results())

    # =====================================
    # STATS
    # =====================================
    elif "--stats" in sys.argv:

        try:
            agent = TradingAgent(ticker)

            risk_mgr_status = agent.risk_mgr.get_status()

            if not isinstance(risk_mgr_status, dict):
                raise ValueError("Risk manager status returned an unexpected type.")

            print(agent.print_risk_stats())
        except Exception as e:  # Added exception handling for potential runtime crashes.
            sys.stderr.write(f"❌ Stats retrieval failed due to an error: {e}\n")
