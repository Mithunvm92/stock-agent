#!/usr/bin/env python3
"""Live trading bot - uses existing access token."""
import os
import sys
import time
import signal
from dotenv import load_dotenv
load_dotenv()

STOCKS = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "SBIN.NS", "KOTAKBANK.NS"]

def get_rsi(ticker):
    try:
        import yfinance as yf
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

def get_kite():
    """Get kite connection."""
    from kiteconnect import KiteConnect
    api_key = os.getenv("ZERODHA_API_KEY", "")
    access_token = os.getenv("ZERODHA_ACCESS_TOKEN", "")
    
    if not api_key or not access_token:
        print("❌ Missing API_KEY or ACCESS_TOKEN in .env")
        return None
    
    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(access_token)
    return kite

def place_trade(kite, ticker, action, qty=1):
    """Place order."""
    try:
        sym = ticker.replace(".NS", "")
        result = kite.place_order(
            variety="regular",
            exchange="NSE",
            trading_symbol=sym,
            transaction_type=action.upper(),
            quantity=qty,
            order_type="MARKET",
            product="CNC"
        )
        print(f"   ✅ {action} {qty} {ticker}: {result}")
        return result
    except Exception as e:
        print(f"   ❌ {e}")
        return None

def scan_and_trade(kite):
    print(f"\n{'='*50}")
    print(time.strftime('%Y-%m-%d %H:%M:%S'))
    for ticker in STOCKS:
        rsi = get_rsi(ticker)
        if rsi < 30:
            print(f"✅ {ticker} RSI:{rsi:.0f} BUY")
            place_trade(kite, ticker, "BUY", 1)
        elif rsi > 70:
            print(f"🔴 {ticker} RSI:{rsi:.0f} SELL")
            place_trade(kite, ticker, "SELL", 1)
        else:
            print(f"⚪ {ticker} RSI:{rsi:.0f} HOLD")

def main():
    print("🤖 Starting Live Trading Bot...")
    kite = get_kite()
    if not kite:
        sys.exit(1)
    
    # Test connection
    try:
        profile = kite.profile()
        print(f"✅ Logged in as: {profile.get('user_name', 'User')}")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("Get new access token:")
        print("1. python brokers/auto_auth.py --url")
        print("2. Visit URL, login, get request_token")
        print("3. python brokers/auto_auth.py <request_token>")
        sys.exit(1)
    
    print("\n🔄 Running 24/7 (Ctrl+C to stop)")
    scan_and_trade(kite)
    while True:
        time.sleep(300)
        scan_and_trade(kite)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Stopped")
