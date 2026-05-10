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
    
Manual Download:
1. Go to: https://finance.yahoo.com/quote/{symbol}.NS/history
2. Select "Historical Data" tab
3. Set Time Period: "Max" or desired range
4. Set Frequency: "Daily"
5. Click "Apply" then "Download"

Or use curl (one-time download):
curl -o data/{symbol}.csv "https://query1.finance.yahoo.com/v7/finance/download/{symbol}.NS?periods=max&interval=1d&filter=history"

Save the file as: data/{symbol}.csv
Format: Date,Open,High,Low,Close,Volume
"""
    return instructions


def download_csv(ticker: str, period: str = "max", csv_dir: str = "data") -> bool:
    """Download CSV using yfinance or NSEpy
    
    Args:
        ticker: Stock ticker
        period: Data period (max, 5y, 2y, 1y, 6mo, 3mo, 1mo)
        csv_dir: Directory to save CSV
    
    Returns:
        True if successful
    """
    symbol = ticker.replace('.NS', '')
    os.makedirs(csv_dir, exist_ok=True)
    
    csv_path = os.path.join(csv_dir, f"{symbol}.csv")
    
    # Try yfinance first
    print(f"📥 Downloading {ticker} data via yfinance...")
    
    period_options = [period, '1y', '6mo', '3mo', '1mo']
    
    for attempt_period in period_options:
        try:
            import yfinance as yf
            import time
            
            stock = yf.Ticker(ticker)
            df = stock.history(period=attempt_period, auto_adjust=True)
            
            if df is None or len(df) < 10:
                continue
            
            df = df.reset_index()
            df.to_csv(csv_path, index=False)
            
            size = os.path.getsize(csv_path)
            print(f"✅ Saved to {csv_path} ({size/1024:.1f} KB, {len(df)} rows)")
            return True
            
        except Exception as e:
            if 'Too Many Requests' in str(e):
                time.sleep(1)
                continue
    
    # Try NSEpy as fallback (for NSE stocks only)
    print(f"📥 Trying NSEpy (Indian stocks)...")
    
    try:
        from nsepy import get_history
        from datetime import datetime, timedelta
        import warnings
        warnings.filterwarnings('ignore')
        
        # Calculate date range
        if period == 'max':
            days = 365 * 5
        elif period == '5y':
            days = 365 * 5
        elif period == '2y':
            days = 365 * 2
        elif period == '1y':
            days = 365
        elif period == '6mo':
            days = 180
        elif period == '3mo':
            days = 90
        elif period == '1mo':
            days = 30
        else:
            days = 365
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # NSEpy uses symbol without .NS
        nse_symbol = symbol.upper()
        
        # Disable threading in nsepy
        df = get_history(symbol=nse_symbol, start=start_date, end=end_date, threads=False)
        
        if df is None or len(df) < 10:
            print(f"⚠️ NSEpy failed for {nse_symbol}")
        else:
            df = df.reset_index()
            df.to_csv(csv_path, index=False)
            size = os.path.getsize(csv_path)
            print(f"✅ Saved via NSEpy ({size/1024:.1f} KB, {len(df)} rows)")
            return True
            
    except Exception as e:
        print(f"⚠️ NSEpy error: {e}")
    
    print(f"\n❌ Rate limited - all sources failed")
    print("📌 Options:")
    print("   1. Wait 15 minutes and try 1mo period")
    print("   2. Use option 30 for manual download")
    return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="CSV Data Loader")
    parser.add_argument('--ticker', default='SBIN.NS')
    parser.add_argument('--csv-dir', default='data')
    parser.add_argument('--download', action='store_true', help='Download CSV from Yahoo')
    parser.add_argument('--period', default='max', help='Period: max, 5y, 2y, 1y, 6mo, 3mo')
    args = parser.parse_args()
    
    # Download if requested
    if args.download:
        success = download_csv(args.ticker, args.period, args.csv_dir)
        if not success:
            exit(1)
        # Show summary
        args.ticker = args.ticker  # Keep same for load
    
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