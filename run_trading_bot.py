#!/usr/bin/env python3
"""
Stock Trading Bot — Main Entry Point

Usage:
  python run_trading_bot.py              → Start automated trading
  python run_trading_bot.py --scan       → Quick scan all stocks
  python run_trading_bot.py --test       → Test Telegram connection
  python run_trading_bot.py --signal     → Get signal for primary ticker
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scheduler.market_scheduler import MarketScheduler, QuickScanner
from alerts.telegram_bot import TelegramAlert
from agents.trading_agent import TradingAgent
from config.settings import PRIMARY_TICKER, TICKERS


def main():
    if len(sys.argv) > 1:
        command = sys.argv[1].lower().replace("--", "")

        if command == "scan":
            # Quick scan
            scanner = QuickScanner()
            scanner.scan()

        elif command == "test":
            # Test Telegram
            print("📱 Testing Telegram connection...")
            telegram = TelegramAlert()
            
            if telegram.enabled:
                success = telegram.send_message("🧪 Test message from Trading Bot!")
                if success:
                    print("✅ Telegram working!")
                else:
                    print("❌ Telegram failed. Check your token and chat ID.")
            else:
                print("⚠️ Telegram not configured.")
                print("   Set environment variables:")
                print("   export TELEGRAM_BOT_TOKEN='your_token'")
                print("   export TELEGRAM_CHAT_ID='your_chat_id'")

        elif command == "signal":
            # Get signal for primary ticker
            ticker = PRIMARY_TICKER
            if len(sys.argv) > 2:
                ticker = sys.argv[2]

            agent = TradingAgent(ticker)
            agent.initialize()
            result = agent.get_signal()

            # Send to Telegram
            telegram = TelegramAlert()
            telegram.send_signal_alert(result, ticker)

        elif command == "train":
            # Force retrain
            from training.trainer import SelfTrainer
            trainer = SelfTrainer()
            trainer.run_training_cycle()

        elif command == "help":
            print(__doc__)

        else:
            print(f"Unknown command: {command}")
            print(__doc__)

    else:
        # Start automated scheduler
        print("""
╔═══════════════════════════════════════════════════════════╗
║           STOCK TRADING BOT — AUTO MODE                   ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║  This will:                                               ║
║  • Scan 30 stocks every 15 minutes                        ║
║  • Send Telegram alerts for BUY/SELL signals              ║
║  • Retrain model daily at 4:00 PM                         ║
║  • Run continuously during market hours                   ║
║                                                           ║
║  Press Ctrl+C to stop                                     ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
        """)

        scheduler = MarketScheduler()
        scheduler.run()


if __name__ == "__main__":
    main()
