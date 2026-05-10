#!/usr/bin/env python3
"""One-click live trading bot - auto auth + trade 24/7."""
import os
import sys
import time
import signal

# ==== CONFIG ====
STOCKS = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "SBIN.NS", "KOTAKBANK.NS"]
INTERVAL = 300  # 5 minutes

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

def auto_auth():
    """Auto authenticate with Zerodha."""
    from kiteconnect import KiteConnect
    api_key = os.getenv("ZERODHA_API_KEY")
    api_secret = os.getenv("ZERODHA_API_SECRET")
    request_token = os.getenv("ZERODHA_REQUEST_TOKEN")
    
    if not all([api_key, api_secret, request_token]):
        print("❌ Missing credentials. Set in .env:")
        print("   ZERODHA_API_KEY")
        print("   ZERODHA_API_SECRET")
        print("   ZERODHA_REQUEST_TOKEN")
        return None
    
    kite = KiteConnect(api_key=api_key)
    try:
        data = kite.generate_session(request_token, api_secret=api_secret)
        access_token = data["access_token"]
        kite.set_access_token(access_token)
        print(f"✅ Auto-authenticated!")
        return kite
    except Exception as e:
        print(f"❌ Auth failed: {e}")
        return None

def place_trade(kite, ticker, action, qty=1):
    """Place order."""
    try:
        result = kite.place_order(
            variety="regular",
            exchange="NSE",
            trading_symbol=ticker.replace(".NS", ""),
            transaction_type=action.upper(),
            quantity=qty,
            order_type="MARKET",
            product="CNC"
        )
        print(f"   ✅ {action} {qty} {ticker}: {result}")
        return result
    except Exception as e:
        print(f"   ❌ Trade failed: {e}")
        return None

def scan_and_trade(kite):
    """Scan and trade."""
    print(f"\n{'='*50}")
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

def signal_handler(sig, frame):
    print("\n🛑 Bot stopped")
    sys.exit(0)

def main():
    print("🤖 Starting Live Trading Bot...")
    print("="*50)
    
    # Authenticate
    kite = auto_auth()
    if not kite:
        print("\nGet request_token:")
        print("1. Set ZERODHA_API_KEY and ZERODHA_API_SECRET in .env")
        print("2. Visit: https://kite.zerodha.com/connect?api_key=YOUR_KEY")
        print("3. Copy request_token from URL and add to .env")
        print("4. Run again")
        sys.exit(1)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Initial scan
    scan_and_trade(kite)
    
    # Loop forever
    print("\n🔄 Running 24/7 (Ctrl+C to stop)")
    while True:
        time.sleep(INTERVAL)
        scan_and_trade(kite)

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    main()
