#!/usr/bin/env python3
# swing_bot has built-in 7-indicator strategy - no external strategy imports needed

import os
import time


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
    print("[21] Swing Bot Signal (Single Stock)")
    print("[22] Swing Bot Scan (Multi Stock)")
    print("[23] Swing Bot Paper Trading")
    print("[24] Swing Bot LIVE Trading")
    print("[25] CSV - Show Data Files")
    print("[26] CSV - Backtest with CSV")
    print("[27] CSV - Download Data")
    print("[28] Price Scanner - Stocks <₹1000")
    print("[0] Exit\n")

    choice = input("Select option: ").strip()

    if choice == "1":

        run("docker-compose up -d")

        pause()

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

        run("python portfolio_summary.py")

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
    # SWING BOT - SINGLE STOCK SIGNAL
    # =====================================
    elif choice == "21":

        ticker = input("\nTicker (e.g. RELIANCE.NS): ").strip().upper()

        if not ticker.endswith(".NS"):
            ticker = ticker + ".NS"

        run(f"python swing_bot.py --ticker {ticker} --mode paper")

        pause()

    # =====================================
    # SWING BOT - MULTI STOCK SCAN
    # =====================================
    elif choice == "22":

        print("\n📊 Running Swing Bot Multi-Stock Scan...\n")

        run("python swing_bot.py --ticker NONE --mode scan")

        pause()

    # =====================================
    # SWING BOT - PAPER TRADING
    # =====================================
    elif choice == "23":

        ticker = input("\nTicker (e.g. RELIANCE.NS): ").strip().upper()

        if not ticker.endswith(".NS"):
            ticker = ticker + ".NS"

        print(f"\n📈 Starting Swing Bot Paper Trading for {ticker}...")

        run(f"python swing_bot.py --ticker {ticker} --mode paper")

        pause()

    # =====================================
    # SWING BOT - LIVE TRADING
    # =====================================
    elif choice == "24":

        ticker = input("\nTicker (e.g. RELIANCE.NS): ").strip().upper()

        if not ticker.endswith(".NS"):
            ticker = ticker + ".NS"

        print(f"\n🚀 Starting Swing Bot LIVE Trading for {ticker}...")

        print("⚠️  WARNING: LIVE TRADING WITH REAL MONEY!")

        confirm = input("Type 'YES' to confirm: ").strip()

        if confirm == "YES":

            run(f"python swing_bot.py --ticker {ticker} --mode live")

        else:

            print("❌ Cancelled")

        pause()

    # =====================================
    # CSV - SHOW FILES
    # =====================================
    elif choice == "25":

        print("\n📁 Available CSV Data Files...\n")

        run("ls -la data/*.csv 2>/dev/null || echo 'No CSV files found'")

        pause()

    # =====================================
    # CSV - BACKTEST
    # =====================================
    elif choice == "26":

        ticker = input("\nTicker (e.g. SBIN): ").strip().upper()

        capital = input("Capital (default 5000): ").strip() or "5000"

        ticker_ns = ticker + ".NS" if not ticker.endswith(".NS") else ticker

        run(f"python swing_backtest.py --ticker {ticker_ns} --csv --capital {capital}")

        pause()

    # =====================================
    # CSV - DOWNLOAD
    # =====================================
    elif choice == "27":

        ticker = input("\nTicker (e.g. SBIN): ").strip().upper()

        period = input("Period (1mo/3mo/6mo/1y, default 1y): ").strip() or "1y"

        ticker_ns = ticker + ".NS" if not ticker.endswith(".NS") else ticker

        run(f"python csv_loader.py --ticker {ticker_ns} --download --period {period}")

        pause()

    # =====================================
    # PRICE SCANNER
    # =====================================
    elif choice == "28":

        print("\n📊 Price Scanner - Stocks Under ₹1000\n")

        run("python price_scanner.py")

        pause()

    elif choice == "0":

        print("\n👋 Exiting...")
        break

    else:

        print("\n⚠️ Invalid option. Try again.")

        pause()
