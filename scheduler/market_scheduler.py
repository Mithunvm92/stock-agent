import schedule
import time
from datetime import datetime, timedelta
import pytz
from config.settings import (
    MARKET_OPEN, MARKET_CLOSE, TIMEZONE,
    SCAN_INTERVAL_MINUTES, RETRAIN_TIME, TICKERS
)
from agents.trading_agent import TradingAgent
from alerts.telegram_bot import TelegramAlert
from training.trainer import SelfTrainer


class MarketScheduler:
    """
    Automated trading scheduler:
    1. Scans market every 15 minutes during trading hours
    2. Sends Telegram alerts for signals
    3. Retrains model daily after market close
    4. Tracks all trades
    """

    def __init__(self):
        self.tz = pytz.timezone(TIMEZONE)
        self.telegram = TelegramAlert()
        self.agent = TradingAgent()
        self.trainer = SelfTrainer()
        self.is_running = False
        self.last_scan_results = []
        self.trades_today = 0
        self.pnl_today = 0

    def is_market_open(self):
        """Check if market is currently open"""
        now = datetime.now(self.tz)
        
        # Skip weekends
        if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False

        # Parse market hours
        open_time = datetime.strptime(MARKET_OPEN, "%H:%M").time()
        close_time = datetime.strptime(MARKET_CLOSE, "%H:%M").time()
        current_time = now.time()

        return open_time <= current_time <= close_time

    def scan_all_stocks(self):
        """Scan all stocks and send alerts"""
        if not self.is_market_open():
            print(f"📊 Market closed. Skipping scan.")
            return

        print(f"\n{'='*50}")
        print(f"🔍 SCANNING {len(TICKERS)} STOCKS...")
        print(f"   Time: {datetime.now(self.tz).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*50}\n")

        results = []

        for ticker in TICKERS:
            try:
                print(f"   Scanning {ticker}...", end=" ")
                
                # Create a fresh agent for each ticker
                agent = TradingAgent(ticker)
                
                # Quick initialization (load model if exists)
                if not agent.model or not agent.model.is_trained:
                    agent.model.load()

                # Get signal
                result = agent.get_signal()
                result['ticker'] = ticker
                results.append(result)

                signal = result['signal']
                conf = result['confidence']
                
                if signal != "HOLD":
                    print(f"✅ {signal} @ {conf:.1f}%")
                    # Send individual alert for actionable signals
                    self.telegram.send_signal_alert(result, ticker)
                else:
                    print(f"⏸️ HOLD")

            except Exception as e:
                print(f"❌ Error: {e}")
                results.append({'ticker': ticker, 'signal': 'ERROR', 'error': str(e)})

        self.last_scan_results = results

        # Send summary
        self.telegram.send_scan_results(results)

        # Print summary
        actionable = [r for r in results if r.get('signal') in ['BUY', 'SELL']]
        print(f"\n{'='*50}")
        print(f"📊 SCAN COMPLETE")
        print(f"   Total: {len(results)} | Signals: {len(actionable)}")
        print(f"{'='*50}\n")

        return results

    def retrain_model(self):
        """Retrain the model after market close"""
        print(f"\n{'='*50}")
        print(f"🤖 DAILY RETRAINING")
        print(f"   Time: {datetime.now(self.tz).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*50}\n")

        try:
            result = self.trainer.run_training_cycle()
            
            if result:
                accuracy, model, fe = result
                self.telegram.send_retrain_complete(
                    accuracy, 
                    len(model.selected_features)
                )
                print(f"✅ Retraining complete. Accuracy: {accuracy:.1f}%")
            else:
                self.telegram.send_error("Retraining failed - no data")
                print(f"❌ Retraining failed")

        except Exception as e:
            self.telegram.send_error(f"Retraining error: {e}")
            print(f"❌ Retraining error: {e}")

    def send_daily_summary(self):
        """Send end-of-day summary"""
        self.telegram.send_daily_summary(
            self.trades_today,
            self.pnl_today,
            self.agent.risk_mgr.current_capital if hasattr(self.agent, 'risk_mgr') else 100000
        )
        
        # Reset daily counters
        self.trades_today = 0
        self.pnl_today = 0

    def setup_schedule(self):
        """Setup the automated schedule"""
        # Scan every N minutes during market hours
        schedule.every(SCAN_INTERVAL_MINUTES).minutes.do(self.scan_all_stocks)

        # Retrain daily at specified time
        schedule.every().day.at(RETRAIN_TIME).do(self.retrain_model)

        # Daily summary at market close
        schedule.every().day.at(MARKET_CLOSE).do(self.send_daily_summary)

        print(f"📅 Schedule configured:")
        print(f"   • Scan: Every {SCAN_INTERVAL_MINUTES} minutes")
        print(f"   • Retrain: Daily at {RETRAIN_TIME}")
        print(f"   • Summary: Daily at {MARKET_CLOSE}")

    def run(self):
        """Start the scheduler"""
        self.is_running = True

        print(f"\n{'='*60}")
        print(f"🚀 TRADING BOT STARTED")
        print(f"   Market Hours: {MARKET_OPEN} - {MARKET_CLOSE} ({TIMEZONE})")
        print(f"   Stocks: {len(TICKERS)}")
        print(f"   Scan Interval: {SCAN_INTERVAL_MINUTES} minutes")
        print(f"{'='*60}\n")

        # Send startup notification
        self.telegram.send_startup()

        # Setup schedule
        self.setup_schedule()

        # Do initial scan if market is open
        if self.is_market_open():
            print("📊 Market is OPEN. Running initial scan...")
            self.scan_all_stocks()
        else:
            print("📊 Market is CLOSED. Waiting for market open...")

        # Run the schedule loop
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(30)  # Check every 30 seconds

        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
            self.telegram.send_shutdown()
            self.is_running = False

    def stop(self):
        """Stop the scheduler"""
        self.is_running = False
        self.telegram.send_shutdown()


class QuickScanner:
    """Quick scanner for manual use"""

    def __init__(self):
        self.telegram = TelegramAlert()

    def scan(self, tickers=None):
        """Quick scan of specified tickers"""
        if tickers is None:
            tickers = TICKERS

        print(f"\n🔍 Quick Scan: {len(tickers)} stocks\n")
        results = []

        for ticker in tickers:
            try:
                agent = TradingAgent(ticker)
                
                # Try to load existing model
                if hasattr(agent, 'model') and agent.model:
                    agent.model.load()

                result = agent.get_signal()
                result['ticker'] = ticker
                results.append(result)

                signal = result['signal']
                conf = result.get('confidence', 0)
                price = result.get('price', 0)

                emoji = "🟢" if signal == "BUY" else "🔴" if signal == "SELL" else "⏸️"
                print(f"{emoji} {ticker:15s} | {signal:6s} | Conf: {conf:5.1f}% | Price: ₹{price:,.2f}")

                if signal != "HOLD":
                    self.telegram.send_signal_alert(result, ticker)

            except Exception as e:
                print(f"❌ {ticker:15s} | Error: {e}")

        # Sort by confidence
        actionable = [r for r in results if r.get('signal') in ['BUY', 'SELL']]
        actionable.sort(key=lambda x: x.get('confidence', 0), reverse=True)

        print(f"\n📊 Summary: {len(actionable)} actionable signals out of {len(tickers)} stocks")

        if actionable:
            print(f"\n🏆 TOP OPPORTUNITIES:")
            for r in actionable[:5]:
                print(f"   {r['ticker']}: {r['signal']} @ {r['confidence']:.1f}% | "
                      f"Entry: ₹{r['price']:.2f} → Target: ₹{r.get('take_profit', 0):.2f}")

        return results
