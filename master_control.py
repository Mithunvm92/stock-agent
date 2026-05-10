#!/usr/bin/env python3

import os
import time

from strategies.ichimoku_rsi_strategy import (
    IchimokuRSIStrategy
)


# =====================================
# CLEAR SCREEN
# =====================================
def clear():

    os.system("clear")


# =====================================
# PAUSE
# =====================================
def pause():

    input("\nPress Enter to continue...")


# =====================================
# RUN SHELL COMMAND
# =====================================
def run(cmd):

    print(f"\n🚀 Running:\n{cmd}\n")

    os.system(cmd)


# =====================================
# MAIN LOOP
# =====================================
while True:

    clear()

    print("═══════════════════════════════════════")
    print("     AI TRADING MASTER CONTROL")
    print("═══════════════════════════════════════\n")

    print("[1] Start All Containers")
    print("[2] Stop All Containers")
    print("[3] Restart Containers")
    print("[4] Rebuild Containers")
    print("[5] Container Status")
    print("[6] Trading Bot Logs")
    print("[7] Scan All Stocks")
    print("[8] Get Trading Signal")
    print("[9] Run ML Backtest")
    print("[10] Force Retraining")
    print("[11] Portfolio Status")
    print("[12] Start Paper Trading")
    print("[13] Start LIVE Trading")
    print("[14] Emergency Stop Trading")
    print("[15] Grafana URL")
    print("[16] Prometheus URL")
    print("[17] Metrics Endpoint")
    print("[18] Zerodha Profile")
    print("[19] Open Container Shell")
    print("[20] Docker Cleanup")
    print("[21] Run Ichimoku Backtest")
    print("[22] Optimize Ichimoku RSI")
    print("[23] Run Ichimoku Paper Trading")
    print("[0] Exit\n")

    choice = input("Select option: ").strip()

    # =====================================
    # START CONTAINERS
    # =====================================
    if choice == "1":

        run("docker-compose up -d")

        pause()

    # =====================================
    # STOP CONTAINERS
    # =====================================
    elif choice == "2":

        run("docker-compose down")

        pause()

    # =====================================
    # RESTART CONTAINERS
    # =====================================
    elif choice == "3":

        run("docker-compose restart")

        pause()

    # =====================================
    # REBUILD CONTAINERS
    # =====================================
    elif choice == "4":

        run("docker-compose down")

        run("docker-compose build --no-cache")

        run("docker-compose up -d")

        pause()

    # =====================================
    # CONTAINER STATUS
    # =====================================
    elif choice == "5":

        run("docker-compose ps")

        pause()

    # =====================================
    # VIEW LOGS
    # =====================================
    elif choice == "6":

        os.system(
            "docker-compose logs -f trading-agent"
        )

    # =====================================
    # SCAN ALL STOCKS
    # =====================================
    elif choice == "7":

        run(
            "docker-compose exec trading-agent "
            "python main.py --scan"
        )

        pause()

    # =====================================
    # GET SIGNAL
    # =====================================
    elif choice == "8":

        ticker = input(
            "\nTicker (e.g. RELIANCE.NS): "
        ).strip()

        run(
            f"docker-compose exec trading-agent "
            f"python main.py --signal "
            f"--ticker {ticker}"
        )

        pause()

    # =====================================
    # ML BACKTEST
    # =====================================
    elif choice == "9":

        run(
            "docker-compose exec trading-agent "
            "python main.py --backtest"
        )

        pause()

    # =====================================
    # FORCE RETRAIN
    # =====================================
    elif choice == "10":

        run(
            "docker-compose exec trading-agent "
            "python main.py --train"
        )

        pause()

    # =====================================
    # PORTFOLIO STATUS
    # =====================================
    elif choice == "11":

        run(
            "docker-compose exec trading-agent "
            "python main.py --stats"
        )

        pause()

    # =====================================
    # PAPER TRADING
    # =====================================
    elif choice == "12":

        run(
            "docker-compose exec trading-agent "
            "python main.py --paper"
        )

        pause()

    # =====================================
    # LIVE TRADING
    # =====================================
    elif choice == "13":

        print("\n⚠️ WARNING: LIVE MONEY MODE ⚠️")

        confirm = input(
            "Type YES to continue: "
        )

        if confirm == "YES":

            run(
                "docker-compose exec trading-agent "
                "python main.py --live 300"
            )

        else:

            print("\n❌ Cancelled")

            time.sleep(2)

    # =====================================
    # EMERGENCY STOP
    # =====================================
    elif choice == "14":

        run(
            "docker-compose stop trading-agent"
        )

        pause()

    # =====================================
    # GRAFANA
    # =====================================
    elif choice == "15":

        print("\n📈 Grafana")
        print("http://localhost:3000")
        print("Username: admin")
        print("Password: admin123")

        pause()

    # =====================================
    # PROMETHEUS
    # =====================================
    elif choice == "16":

        print("\n📊 Prometheus")
        print("http://localhost:9090")

        pause()

    # =====================================
    # METRICS
    # =====================================
    elif choice == "17":

        print("\n📡 Metrics")
        print("http://localhost:8000/metrics")

        pause()

    # =====================================
    # ZERODHA PROFILE
    # =====================================
    elif choice == "18":

        run(
            "docker-compose exec trading-agent "
            "python -c \"from brokers.zerodha "
            "import ZerodhaBroker; "
            "b=ZerodhaBroker(); "
            "print(b.kite.profile())\""
        )

        pause()

    # =====================================
    # CONTAINER SHELL
    # =====================================
    elif choice == "19":

        os.system(
            "docker-compose exec trading-agent bash"
        )

    # =====================================
    # FULL CLEANUP + REBUILD
    # =====================================
    elif choice == "20":

        print(
            "\n🧹 FULL DOCKER + PYTHON CLEANUP\n"
        )

        run(
            "find . -type d -name '__pycache__' "
            "-exec rm -rf {} +"
        )

        run(
            "find . -name '*.pyc' -delete"
        )

        run(
            "docker-compose down "
            "--remove-orphans"
        )

        run(
            "docker system prune -f"
        )

        run(
            "docker builder prune -f"
        )

        run(
            "docker-compose build --no-cache"
        )

        run(
            "docker-compose up -d"
        )

        print(
            "\n✅ FULL CLEAN REBUILD COMPLETE"
        )

        pause()

    # =====================================
    # ICHIMOKU BACKTEST
    # =====================================
    elif choice == "21":

        print(
            "\n📊 Running Ichimoku Backtest...\n"
        )

        strategy = IchimokuRSIStrategy(

            ticker="RELIANCE.NS",

            initial_capital=100000,

            rsi_threshold=40
        )

        strategy.load_data()

        strategy.build_indicators()

        strategy.generate_signals()

        strategy.backtest()

        strategy.performance_report()

        strategy.plot_results()

        pause()

    # =====================================
    # RSI OPTIMIZATION
    # =====================================
    elif choice == "22":

        print(
            "\n🔍 Optimizing RSI Threshold...\n"
        )

        strategy = IchimokuRSIStrategy(

            ticker="RELIANCE.NS",

            initial_capital=100000
        )

        strategy.optimize_rsi()

        pause()

    # =====================================
    # ICHIMOKU PAPER TRADING
    # =====================================
    elif choice == "23":

        print(
            "\n📈 Starting Ichimoku "
            "Paper Trading...\n"
        )

        while True:

            try:

                strategy = IchimokuRSIStrategy(

                    ticker="RELIANCE.NS",

                    initial_capital=100000,

                    rsi_threshold=40
                )

                strategy.load_data()

                strategy.build_indicators()

                strategy.generate_signals()

                latest = strategy.df.iloc[-1]

                signal = latest['signal']

                close = latest['Close']

                rsi = latest['rsi']

                print(
                    "\n════════════════════════════"
                )

                print(
                    f"Ticker: RELIANCE.NS"
                )

                print(
                    f"Price: ₹{close:.2f}"
                )

                print(
                    f"RSI: {rsi:.2f}"
                )

                if signal == 1:

                    print("📈 SIGNAL: BUY")

                elif signal == -1:

                    print("📉 SIGNAL: SELL")

                else:

                    print("⏸ SIGNAL: HOLD")

                print(
                    "════════════════════════════\n"
                )

                print(
                    "⏰ Waiting 1 hour...\n"
                )

                time.sleep(3600)

            except KeyboardInterrupt:

                print(
                    "\n🛑 Ichimoku paper "
                    "trading stopped"
                )

                break

            except Exception as e:

                print(
                    f"\n❌ Error: {e}"
                )

                time.sleep(30)

    # =====================================
    # EXIT
    # =====================================
    elif choice == "0":

        print("\n👋 Exiting...\n")

        break

    # =====================================
    # INVALID OPTION
    # =====================================
    else:

        print("\n❌ Invalid option")

        time.sleep(1)