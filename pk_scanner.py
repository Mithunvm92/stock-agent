#!/usr/bin/env python3
"""
High Win Rate Scanner - Multiple Indicators
- RSI Oversold (<30) + MACD Cross Up = BUY
- RSI Overbought (>70) + MACD Cross Down = SELL
- Volume spike confirms signal
"""
import yfinance as yf
import pandas as pd

STOCKS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "SBIN.NS", "KOTAKBANK.NS",
    "ASIANPAINT.NS", "HINDUNILVR.NS", "BAJFINANCE.NS", "LT.NS", "ICICIBANK.NS"
]

def get_signals(ticker):
    """Get multi-indicator signals."""
    try:
        df = yf.download(ticker, period="90d", interval="1d", progress=False)
        if len(df) < 30:
            return None
        
        close = df['Close'].squeeze()
        volume = df['Volume']
        
        # RSI
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rsi = 100 - (100 / (1 + (gain / loss)))
        
        # MACD
        ema12 = close.ewm(span=12).mean()
        ema26 = close.ewm(span=26).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9).mean()
        macd_cross = macd.iloc[-1] - signal.iloc[-1]
        macd_prev = macd.iloc[-2] - signal.iloc[-2]
        
        # Volume spike
        vol_avg = volume.rolling(20).mean()
        vol_spike = volume.iloc[-1] > vol_avg.iloc[-1] * 1.5
        
        rsi_val = float(rsi.iloc[-1])
        macd_cross_up = macd_prev < 0 and macd_cross > 0
        macd_cross_down = macd_prev > 0 and macd_cross < 0
        
        # BUY: RSI oversold + MACD cross up
        if rsi_val < 30 and macd_cross_up:
            return ("BUY", rsi_val, "RSI<30 + MACD CROSS")
        # SELL: RSI overbought + MACD cross down
        if rsi_val > 70 and macd_cross_down:
            return ("SELL", rsi_val, "RSI>70 + MACD CROSS")
        if rsi_val < 30:
            return ("BUY", rsi_val, "RSI ONLY")
        if rsi_val > 70:
            return ("SELL", rsi_val, "RSI ONLY")
        
        return None
    except:
        return None

def scan():
    print("=" * 50)
    print("HIGH WIN RATE SCANNER")
    print("=" * 50)
    
    buy_signals = []
    sell_signals = []
    
    for ticker in STOCKS:
        result = get_signals(ticker)
        if result:
            signal, rsi, reason = result
            price = yf.download(ticker, period="1d", progress=False)['Close'].iloc[-1]
            if signal == "BUY":
                print(f"✅ {ticker} ₹{price:.0f} RSI:{rsi:.0f} {reason}")
                buy_signals.append(ticker)
            elif signal == "SELL":
                print(f"🔴 {ticker} ₹{price:.0f} RSI:{rsi:.0f} {reason}")
                sell_signals.append(ticker)
        else:
            print(f"⚪ {ticker} HOLD")
    
    print(f"\nBUY Signals: {len(buy_signals)}")
    print(f"SELL Signals: {len(sell_signals)}")
    return buy_signals, sell_signals

if __name__ == "__main__":
    scan()
