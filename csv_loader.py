#!/usr/bin/env python3
"""
Manual CSV Data Loader for Swing Trading Bot

Allows loading historical data from manually downloaded CSV files
to avoid Yahoo API rate limits.

Usage:
1. Download CSV from Yahoo Finance (Historical Data)
2. Save as data/TICKER.csv (e.g., data/SBIN.csv)
3. Run backtest/swing bot with --csv flag
"""

import os
import pandas as pd
from datetime import datetime


def load_csv(ticker: str, csv_dir: str = "data") -> pd.DataFrame:
    """
    Load stock data from manually downloaded CSV
    
    Args:
        ticker: Stock ticker (e.g., SBIN.NS or SBIN)
        csv_dir: Directory containing CSV files
    
    Returns:
        DataFrame with OHLCV data or empty DataFrame
    
    CSV format expected:
        Date,Open,High,Low,Close,Volume
    """
    # Extract symbol from ticker
    symbol = ticker.replace('.NS', '').replace('.NS', '')
    
    # Try different file names
    possible_files = [
        os.path.join(csv_dir, f"{symbol}.csv"),
        os.path.join(csv_dir, f"{ticker}.csv"),
        os.path.join(csv_dir, f"{symbol.upper()}.csv"),
    ]
    
    csv_path = None
    for f in possible_files:
        if os.path.exists(f):
            csv_path = f
            break
    
    if not csv_path:
        print(f"❌ CSV not found for {ticker}")
        print(f"   Expected: {possible_files}")
        return pd.DataFrame()
    
    try:
        # Try different date formats
        date_formats = ['%Y-%m-%d', '%d-%m-%Y', '%m-%d-%Y', '%Y/%m/%d']
        
        for fmt in date_formats:
            try:
                df = pd.read_csv(csv_path)
                # Check if Date column exists
                if 'Date' in df.columns:
                    df['Date'] = pd.to_datetime(df['Date'], format=fmt)
                    df = df.set_index('Date').sort_index()
                elif 'Date' in str(df.columns).lower():
                    date_col = [c for c in df.columns if 'date' in c.lower()][0]
                    df[date_col] = pd.to_datetime(df[date_col], format=fmt)
                    df = df.set_index(date_col).sort_index()
                break
            except:
                continue
        
        # Standardize column names
        column_map = {
            'Open': 'Open',
            'High': 'High', 
            'Low': 'Low',
            'Close': 'Close',
            'Volume': 'Volume',
            'Adj Close': 'Close',
            'Adj Close': 'Close',
        }
        
        # Rename columns to standard
        df = df.rename(columns={k: v for k, v in column_map.items() if k in df.columns})
        
        # Ensure required columns exist
        required = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing = [c for c in required if c not in df.columns]
        
        if missing:
            print(f"❌ Missing columns: {missing}")
            return pd.DataFrame()
        
        # Select only needed columns
        df = df[required]
        
        # Remove NaN rows
        df = df.dropna()
        
        print(f"✅ Loaded {len(df)} rows from {csv_path}")
        return df
        
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        return pd.DataFrame()


def list_available_csv(csv_dir: str = "data") -> list:
    """List available CSV files"""
    if not os.path.exists(csv_dir):
        return []
    
    csv_files = [f for f in os.listdir(csv_dir) if f.endswith('.csv')]
    return sorted(csv_files)


def download_instructions(ticker: str) -> str:
    """Generate instructions for downloading CSV"""
    symbol = ticker.replace('.NS', '')
    
    instructions = f"""
📥 CSV Download Instructions for {symbol}:
    
1. Go to: https://finance.yahoo.com/quote/{symbol}.NS/history
2. Select "Historical Data" tab
3. Set Time Period: "Max" or desired range
4. Set Frequency: "Daily"
5. Click "Apply" then "Download"

Or use this URL directly:
https://query1.finance.yahoo.com/v7/finance/download/{symbol}.NS?periods=max&interval=1d&filter=history

6. Save the file as: data/{symbol}.csv

Note: The CSV must have columns: Date, Open, High, Low, Close, Volume
"""
    return instructions


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="CSV Data Loader")
    parser.add_argument('--ticker', default='SBIN.NS')
    parser.add_argument('--csv-dir', default='data')
    args = parser.parse_args()
    
    # List available
    files = list_available_csv(args.csv_dir)
    if files:
        print(f"\n📁 Available CSV files in {args.csv_dir}/:")
        for f in files:
            path = os.path.join(args.csv_dir, f)
            size = os.path.getsize(path)
            print(f"   • {f} ({size/1024:.1f} KB)")
    else:
        print(f"\n📁 No CSV files found in {args.csv_dir}/")
        print(download_instructions(args.ticker))
    
    # Try to load
    df = load_csv(args.ticker, args.csv_dir)
    if len(df) > 0:
        print(f"\n📊 Data Summary:")
        print(f"   Start: {df.index[0].strftime('%Y-%m-%d')}")
        print(f"   End:   {df.index[-1].strftime('%Y-%m-%d')}")
        print(f"   Rows:  {len(df)}")
        print(f"   Close: ₹{df['Close'].iloc[-1]:.2f}")