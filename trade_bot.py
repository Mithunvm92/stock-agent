#!/usr/bin/env python3
"""Auto-trading bot for Zerodha."""
import time
import yfinance as yf
from dotenv import load_dotenv
load_dotenv()

STOCKS = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "SBIN.NS", "KOTAKBANK.NS"]

def get_rsi(ticker):
    """Calculate RSI."""
    try:
        df = yf.download(ticker, period="60d", interval="1d", progress=False)
        if df.empty or len(df) < 20:
            return 50.0
        
        close = df['Close'].squeeze()
        delta = close.diff()
        gain = delta.where(delta > 0, 0.0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1])
    except:
        return 50.0

def check_signals():
    """Check signals."""
    print(f"\n{'='*40}")
    print(f"🕐 {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    for ticker in STOCKS:
        rsi = get_rsi(ticker)
        if rsi < 30:
            print(f"✅ {ticker} RSI:{rsi:.0f} BUY")
        elif rsi > 70:
            print(f"🔴 {ticker} RSI:{rsi:.0f} SELL")
        else:
            print(f"⚪ {ticker} RSI:{rsi:.0f} HOLD")

def run_bot():
    """Run the bot."""
    print("🤖 Trading bot started! Ctrl+C to stop")
    while True:
        check_signals()
        time.sleep(300)  # 5 minutes

if __name__ == "__main__":
    try:
        run_bot()
    except KeyboardInterrupt:
        print("\n🛑 Stopped")
