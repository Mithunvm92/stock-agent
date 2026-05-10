#!/usr/bin/env python3
"""Auto-trading bot for Zerodha."""
import time
import yfinance as yf
import os
from dotenv import load_dotenv
load_dotenv()

STOCKS = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "SBIN.NS", "KOTAKBANK.NS"]

# DRY RUN - set to False to enable live trading
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"

def get_rsi(ticker):
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

def place_trade(ticker, action, qty=1):
    """Place trade on Zerodha."""
    if DRY_RUN:
        print(f"   [DRY RUN] Would {action} {qty} {ticker}")
        return {"order_id": "dry_run"}
    
    from brokers.zerodha import ZerodhaBroker
    broker = ZerodhaBroker()
    result = broker.place_market_order(ticker, action, qty)
    return result

def check_signals():
    print(f"\n{'='*50}")
    print(f"🤖 {time.strftime('%Y-%m-%d %H:%M:%S')} | MODE: {'DRY RUN' if DRY_RUN else 'LIVE'}")
    
    for ticker in STOCKS:
        rsi = get_rsi(ticker)
        if rsi < 30:
            print(f"✅ {ticker} RSI:{rsi:.0f} BUY")
            place_trade(ticker, "BUY", 1)
        elif rsi > 70:
            print(f"🔴 {ticker} RSI:{rsi:.0f} SELL")
            place_trade(ticker, "SELL", 1)
        else:
            print(f"⚪ {ticker} RSI:{rsi:.0f} HOLD")

def run_bot():
    print("🤖 Trading bot started!")
    print(f"Mode: {'DRY RUN' if DRY_RUN else 'LIVE'} (set DRY_RUN=false in .env for live)")
    print("Ctrl+C to stop\n")
    
    while True:
        check_signals()
        time.sleep(300)

if __name__ == "__main__":
    try:
        run_bot()
    except KeyboardInterrupt:
        print("\n🛑 Stopped")
