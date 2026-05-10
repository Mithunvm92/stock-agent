#!/usr/bin/env python3

import os
import time


def clear():
    os.system("clear")


def pause():
    input("\nPress Enter to continue...")


def run(cmd):

    print(f"\n🚀 Running:\n{cmd}\n")

    os.system(cmd)

    pause()


while True:

    clear()

    print("═══════════════════════════════════════")
    print("      AI TRADING CONTROL PANEL")
    print("═══════════════════════════════════════\n")

    print("[1] Start Live Trading")
    print("[2] Stop Trading")
    print("[3] View Live Logs")
    print("[4] Scan All Stocks")
    print("[5] Get Trading Signal")
    print("[6] Force Retraining")
    print("[7] Portfolio Status")
    print("[8] Zerodha Profile")
    print("[9] Paper Trading")
    print("[10] REAL Trading")
    print("[11] Open Dashboards")
    print("[12] Emergency Stop")
    print("[0] Exit\n")

    choice = input("Select option: ").strip()

    # =====================================
    # START LIVE
    # =====================================
    if choice == "1":

        run(
            "docker-compose up -d trading-agent"
        )

    # =====================================
    # STOP
    # =====================================
    elif choice == "2":

        run(
            "docker-compose stop trading-agent"
        )

    # =====================================
    # LOGS
    # =====================================
    elif choice == "3":

        os.system(
            "docker-compose logs -f trading-agent"
        )

    # =====================================
    # SCAN
    # =====================================
    elif choice == "4":

        run(
            "docker-compose exec trading-agent "
            "python main.py --scan"
        )

    # =====================================
    # SIGNAL
    # =====================================
    elif choice == "5":

        ticker = input(
            "\nTicker (e.g. RELIANCE.NS): "
        ).strip()

        run(
            f"docker-compose exec trading-agent "
            f"python main.py --signal "
            f"--ticker {ticker}"
        )

    # =====================================
    # RETRAIN
    # =====================================
    elif choice == "6":

        run(
            "docker-compose exec trading-agent "
            "python main.py --train"
        )

    # =====================================
    # PORTFOLIO
    # =====================================
    elif choice == "7":

        run(
            "docker-compose exec trading-agent "
            "python main.py --stats"
        )

    # =====================================
    # ZERODHA PROFILE
    # =====================================
    elif choice == "8":

        run(
            "docker-compose exec trading-agent "
            "python -c \"from brokers.zerodha "
            "import ZerodhaBroker; "
            "b=ZerodhaBroker(); "
            "print(b.kite.profile())\""
        )

    # =====================================
    # PAPER TRADING
    # =====================================
    elif choice == "9":

        run(
            "docker-compose exec trading-agent "
            "python main.py --paper"
        )

    # =====================================
    # REAL TRADING
    # =====================================
    elif choice == "10":

        print("\n⚠️ WARNING: REAL MONEY MODE ⚠️")

        confirm = input(
            "\nType YES to continue: "
        )

        if confirm == "YES":

            run(
                "docker-compose exec trading-agent "
                "python main.py --live 300"
            )

        else:

            print("\n❌ Cancelled")

            time.sleep(1)

    # =====================================
    # DASHBOARDS
    # =====================================
    elif choice == "11":

        print("\n📈 Grafana:")
        print("http://localhost:3000")

        print("\n📊 Prometheus:")
        print("http://localhost:9090")

        pause()

    # =====================================
    # EMERGENCY STOP
    # =====================================
    elif choice == "12":

        run("docker-compose stop")

    # =====================================
    # EXIT
    # =====================================
    elif choice == "0":

        print("\n👋 Exiting...\n")

        break

    # =====================================
    # INVALID
    # =====================================
    else:

        print("\n❌ Invalid option")

        time.sleep(1)
