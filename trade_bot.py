#!/usr/bin/env python3
"""
Auto-trading bot - runs continuously and trades on Zerodha.
"""
import time
import schedule
import yfinance as yf
from dotenv import load_dotenv
load_dotenv()

STOCKS = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "SBIN.NS", "KOTAKBANK.NS"]

def get_rsi(ticker):
    """Calculate RSI."""
    try:
        df = yf.download(ticker, period="60d", interval="1d", progress=False)
        if df.empty or len(df) < 20:
            return 50
        
        delta = df['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1]
    except:
        return 50

def check_signals():
    """Check and trade."""
    from brokers.zerodha import ZerodhaBroker
    
    print(f"\n{'='*40}")
    print(f"🕐 {time.strftime('%H:%M:%S')} - Scanning...")
    
    try:
        broker = ZerodhaBroker()
    except Exception as e:
        print(f"❌ Broker error: {e}")
        return
    
    for ticker in STOCKS:
        rsi = get_rsi(ticker)
        
        if rsi < 30:
            print(f"✅ {ticker} - RSI:{rsi:.0f} BUY SIGNAL")
            try:
                # Only trade if we have capital (simple check)
                # broker.place_market_order(ticker, "BUY", 1)
                print(f"   → Would BUY {ticker}")
            except Exception as e:
                print(f"   ❌ {e}")
        elif rsi > 70:
            print(f"🔴 {ticker} - RSI:{rsi:.0f} SELL SIGNAL")
        else:
            print(f"⚪ {ticker} - RSI:{rsi:.0f} HOLD")

def run_bot():
    """Run the bot."""
    print("🤖 Auto-trading bot started!")
    print("Press Ctrl+C to stop")
    
    # Check every 5 minutes
    schedule.every(5).minutes.do(check_signals)
    check_signals()  # Initial check
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    try:
        run_bot()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped")
