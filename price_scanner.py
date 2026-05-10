#!/usr/bin/env python3
"""
Price Scanner - Find stocks under 1000 INR
"""

import yfinance as yf
import pandas as pd
from datetime import datetime


# Common NSE large/mid cap stocks
NSE_STOCKS = [
    # Large Cap
    'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'SBIN', 'BHARTIARTL',
    'ITC', 'LT', 'HINDUNILVR', 'AXISBANK', 'KOTAKBANK', 'SUNPHARMA',
    'TATASTEEL', 'ADANIPORTS', 'M&M', 'BAJFINANCE', 'WIPRO', 'HCLTECH',
    'ASIANPAINT', 'MARUTI', 'TITAN', 'ULTRACEMCO', 'NESTLEIND', 'POWERGRID',
    'CIPLA', 'DRREDDY', 'SBILIFE', 'GRASIM', 'TATAMOTORS', 'NTPC',
    'COALINDIA', 'ADANIGREEN', 'ADANITRANS', 'SIEMENS', 'BPCL', 'TECHM',
    'HDFCLIFE', 'SHREECEM', 'DIVISLAB', 'POLYCAB', 'HAVELLS', 'GAIL',
    'CONCOR', 'EXIDEIND', 'AMBUJACEM', 'GODREJPRO', 'UBL', 'COLGATE',
    # Mid Cap
    'APOLLOTYRE', 'CREATED', 'TORNTPHARM', 'GLENMARK', 'APOLLOHOSP', 'RAYMOND',
    'BANDHANBNK', 'INDUSINDBK', 'IDICIBANK', 'FEDERALBANK', 'RBLBANK', 'AUBANK',
    'PNB', 'CANBK', 'BANKBARODA', 'IOB', 'CORPBANK', 'KARURVYSYA',
    'LALPATHLABS', 'METROBRAND', 'VGUARD', 'FINOLEXIND', 'REDINGTON', 'VIPIND',
    'TATAELXSI', 'TEAMLEASE', 'SPANDANA', 'MAGMA', 'BIRLACORP', 'GSFC',
]


def get_prices():
    """Get current prices for all stocks"""
    print("📊 Checking prices...")
    
    prices = []
    
    for symbol in NSE_STOCKS:
        try:
            ticker = f"{symbol}.NS"
            stock = yf.Ticker(ticker)
            info = stock.fast_info
            
            # Try different price sources
            price = 0
            if 'lastPrice' in info:
                price = info['lastPrice']
            elif 'previousClose' in info:
                price = info['previousClose']
            elif 'close' in info:
                price = info['close']
            
            if price > 0:
                prices.append({
                    'symbol': symbol,
                    'price': price,
                    'ticker': ticker
                })
                print(f"  {symbol}: ₹{price:.2f}")
            
        except Exception as e:
            print(f"  {symbol}: Error - {e}")
    
    return prices


def filter_under_1000(prices):
    """Filter stocks under 1000 INR"""
    under_1000 = [p for p in prices if p['price'] < 1000]
    return sorted(under_1000, key=lambda x: x['price'])


def main():
    print("="*50)
    print("NSE Stock Price Scanner")
    print("="*50)
    
    prices = get_prices()
    
    print(f"\n{'='*50}")
    print(f"STOCKS UNDER ₹1000")
    print(f"{'='*50}")
    
    under_1000 = filter_under_1000(prices)
    
    print(f"\nTotal: {len(under_1000)} stocks\n")
    
    for p in under_1000:
        print(f"  {p['symbol']:15} ₹{p['price']:8.2f}")
    
    # Save list
    print(f"\n{'='*50}")
    
    # Save to file for CSV download
    with open('data/stocks_under_1000.txt', 'w') as f:
        f.write("symbol,ticker,price\n")
        for p in under_1000:
            f.write(f"{p['symbol']},{p['ticker']},{p['price']}\n")
    
    print(f"✅ Saved to data/stocks_under_1000.txt")
    print(f"\n📥 To download CSV for each:")
    print(f"   python csv_loader.py --ticker SYMBOL --download")


if __name__ == "__main__":
    main()