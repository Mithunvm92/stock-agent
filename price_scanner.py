#!/usr/bin/env python3
"""
Price Scanner - Find stocks under 1000 INR
Rate-limited with caching
"""

import yfinance as yf
import time
import os
import json
from datetime import datetime, timedelta


CACHE_FILE = "/tmp/price_cache.json"
CACHE_TTL_HOURS = 1


NSE_STOCKS = [
    'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'SBIN', 'BHARTIARTL',
    'ITC', 'LT', 'HINDUNILVR', 'AXISBANK', 'KOTAKBANK', 'SUNPHARMA',
    'TATASTEEL', 'ADANIPORTS', 'M&M', 'BAJFINANCE', 'WIPRO', 'HCLTECH',
    'ASIANPAINT', 'MARUTI', 'TITAN', 'ULTRACEMCO', 'NESTLEIND', 'POWERGRID',
    'CIPLA', 'DRREDDY', 'SBILIFE', 'GRASIM', 'TATAMOTORS', 'NTPC',
    'COALINDIA', 'ADANIGREEN', 'ADANITRANS', 'SIEMENS', 'BPCL', 'TECHM',
    'HDFCLIFE', 'SHREECEM', 'DIVISLAB', 'POLYCAB', 'HAVELLS', 'GAIL',
]


def load_cache():
    """Load cached prices"""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                data = json.load(f)
            cache_time = datetime.fromisoformat(data.get('timestamp', '2000-01-01'))
            if datetime.now() - cache_time < timedelta(hours=CACHE_TTL_HOURS):
                return data.get('prices', {})
        except:
            pass
    return {}


def save_cache(prices):
    """Save cache"""
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump({'timestamp': datetime.now().isoformat(), 'prices': prices}, f)
    except:
        pass


def get_prices():
    """Get all stock prices"""
    print("📊 Checking prices...")
    
    # Try cache
    cached = load_cache()
    if cached:
        print(f"💾 Using cache ({len(cached)} stocks)")
        return [{'symbol': k, 'price': v} for k, v in cached.items()]
    
    prices = []
    
    for symbol in NSE_STOCKS:
        try:
            ticker = yf.Ticker(f"{symbol}.NS")
            time.sleep(0.3)  # Rate limit
            
            info = ticker.fast_info
            price = info.get('lastPrice') or info.get('previousClose') or 0
            
            if price > 0:
                prices.append({'symbol': symbol, 'price': price})
                print(f"  {symbol}: ₹{price:.2f}")
            else:
                print(f"  {symbol}: No data")
                
        except Exception as e:
            print(f"  {symbol}: Error")
    
    # Save to cache
    if prices:
        save_cache({p['symbol']: p['price'] for p in prices})
    
    return prices


def main():
    prices = get_prices()
    under_1000 = [p for p in prices if p['price'] < 1000]
    under_1000.sort(key=lambda x: x['price'])
    
    print("\n" + "="*50)
    print("   STOCKS UNDER ₹1000")
    print("="*50)
    
    if under_1000:
        for p in under_1000[:15]:
            print(f"  {p['symbol']:12} ₹{p['price']:.2f}")
    else:
        print("  No stocks found under ₹1000")
    
    print("="*50)


if __name__ == "__main__":
    main()
