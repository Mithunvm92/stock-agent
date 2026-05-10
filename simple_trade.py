#!/usr/bin/env python3
"""Simple live trading - scan and buy."""
import sys
import yfinance as yf
from dotenv import load_dotenv
load_dotenv()

# Small caps to scan
STOCKS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "SBIN.NS", "BAJFINANCE.NS", "ASIANPAINT.NS", "HINDUNILVR.NS",
    "KOTAKBANK.NS", "LT.NS"
]

def get_price(ticker):
    """Get current price."""
    try:
        df = yf.download(ticker, period="1d", progress=False)
        if not df.empty:
            return df['Close'].iloc[-1]
    except:
        pass
    return 0

def check_signal(ticker):
    """Simple RSI signal."""
    try:
        df = yf.download(ticker, period="60d", interval="1d", progress=False)
        if df.empty or len(df) < 20:
            return None
        
        delta = df['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        if rsi.iloc[-1] < 30:  # Oversold = BUY
            return "BUY"
        elif rsi.iloc[-1] > 70:  # Overbought = SELL
            return "SELL"
    except:
        pass
    return None

def main():
    print("📊 Scanning for signals...\n")
    signals = []
    
    for ticker in STOCKS:
        price = get_price(ticker)
        signal = check_signal(ticker)
        
        if signal == "BUY":
            print(f"✅ {ticker} - Price: ₹{price:.2f} - RSI: OVERSOLD - BUY SIGNAL")
            signals.append((ticker, price))
        elif signal == "SELL":
            print(f"🔴 {ticker} - Price: ₹{price:.2f} - RSI: OVERBOUGHT - SELL SIGNAL")
    
    if not signals:
        print("No BUY signals found")
        return
    
    # Ask to trade
    print(f"\nFound {len(signals)} BUY signals")
    print("\nTo execute live trade:")
    print("1. Edit .env with ZERODHA_ACCESS_TOKEN")
    print("2. Run: python simple_trade.py --buy TICKER QUANTITY")
    print("   Example: python simple_trade.py --buy RELIANCE.NS 1")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--buy":
        try:
            from brokers.zerodha import ZerodhaBroker
            ticker = sys.argv[2]
            qty = int(sys.argv[3])
            
            broker = ZerodhaBroker()
            result = broker.place_market_order(ticker, "BUY", qty)
            print(f"✅ Order placed: {result}")
        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        main()
