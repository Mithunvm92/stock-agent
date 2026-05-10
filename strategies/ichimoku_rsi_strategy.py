import pandas as pd
import numpy as np
import yfinance as yf
import time
import warnings

from ta.trend import IchimokuIndicator
from ta.momentum import RSIIndicator

# Suppress pandas/yfinance deprecation warnings
warnings.filterwarnings('ignore')

class IchimokuRSIStrategy:

    def __init__(
        self,
        ticker="RELIANCE.NS",
        start="2020-01-01",
        end="2026-01-01",
        initial_capital=100000,
        rsi_threshold=40
    ):
        self.ticker = ticker
        self.start = start
        self.end = end
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.rsi_threshold = rsi_threshold

        self.df = pd.DataFrame()
        
        # Stats
        self.trades = 0
        self.wins = 0
        self.losses = 0
        self.equity_curve = []

        print("\n" + "═"*40)
        print(" ICHIMOKU RSI STRATEGY INIT")
        print("═"*40)
        print(f"Ticker: {self.ticker}")
        print(f"Period: {self.start} to {self.end}")
        print(f"Capital: ₹{self.initial_capital:,.0f}")
        print(f"RSI Threshold: {self.rsi_threshold}")
        print("═"*40 + "\n")

    def load_data(self):
        """FIX: Uses custom headers to bypass bot-blocker and caches data locally to prevent rate limits."""
        import os
        import requests
        
        # Create a safe filename for the cache
        safe_ticker = self.ticker.replace(".", "_")
        cache_file = f"cache_{safe_ticker}_{self.start}_{self.end}.csv"

        # ── STEP 1: Check if we already have the data saved locally ──
        if os.path.exists(cache_file):
            print(f"📂 Loading from local cache: {cache_file}")
            try:
                self.df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
                # Ensure columns are standard
                self.df = self.df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
                self.df.dropna(inplace=True)
                print(f"✅ Loaded {len(self.df)} rows from cache")
                return
            except Exception as e:
                print(f"⚠️ Cache file corrupted, re-downloading... ({e})")

        # ── STEP 2: Download with Custom Headers (Bypasses basic rate limits) ──
        print(f"📥 Downloading {self.ticker} from Yahoo Finance...")
        
        # Create a custom session with a realistic browser User-Agent
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive"
        })

        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Pass the custom session to yfinance
                stock = yf.Ticker(self.ticker, session=session)
                df = stock.history(start=self.start, end=self.end, auto_adjust=True)
                
                if df is None or len(df) == 0:
                    print("⚠️ Empty dataframe received.")
                    time.sleep(5)
                    continue
                
                # Clean and format
                df = df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
                df.dropna(inplace=True)
                
                # ── STEP 3: Save to local cache for next time ──
                df.to_csv(cache_file)
                print(f"💾 Data cached locally to: {cache_file}")
                
                self.df = df
                print(f"✅ Downloaded and loaded {len(df)} rows")
                return
                
            except Exception as e:
                print(f"⚠️ Attempt {attempt+1} failed: {e}")
                if "Rate limited" in str(e) or "Too Many Requests" in str(e):
                    print("   ⏳ Yahoo is rate-limiting this IP. Waiting 15 seconds...")
                    time.sleep(15) # Wait longer if specifically rate limited
                else:
                    time.sleep(5)
                    
        print("❌ Download failed after retries.")
        print("   💡 TIP: Your IP is temporarily blocked by Yahoo.")
        print("   Wait 1-2 hours, or use a VPN to change your IP.")
        self.df = pd.DataFrame()        # ICHIMOKU
        ichi = IchimokuIndicator(high=high, low=low, window1=9, window2=26, window3=52)
        df['tenkan'] = ichi.ichimoku_conversion_line()
        df['kijun'] = ichi.ichimoku_base_line()
        df['senkou_a'] = ichi.ichimoku_a()
        df['senkou_b'] = ichi.ichimoku_b()

        # RSI
        rsi = RSIIndicator(close=close, window=14)
        df['rsi'] = rsi.rsi()

        # VOLUME SMA
        df['volume_sma20'] = volume.rolling(20).mean()

        # CLEAN NaNs
        df.dropna(inplace=True)
        self.df = df
        print(f"✅ Indicators built | {len(df)} rows clean")

    def generate_signals(self):
        """FIX 2: Vectorized signals (100x faster than for-loops)"""
        if self.df.empty:
            print("❌ No data available")
            return

        df = self.df
        
        # Shift RSI to compare previous row
        prev_rsi = df['rsi'].shift(1)

        # Vectorized Bullish Condition
        bullish = (
            (df['Close'] > df['senkou_a']) &
            (df['Close'] > df['senkou_b']) &
            (df['tenkan'] > df['kijun']) &
            (prev_rsi <= self.rsi_threshold) &
            (df['rsi'] > self.rsi_threshold) &
            (df['Volume'] > df['volume_sma20'])
        )

        # Vectorized Bearish Condition
        bearish = (
            (df['Close'] < df['senkou_a']) &
            (df['Close'] < df['senkou_b']) &
            (df['tenkan'] < df['kijun']) &
            (prev_rsi >= 60) &
            (df['rsi'] < 60)
        )

        df['signal'] = 0
        df.loc[bullish, 'signal'] = 1
        df.loc[bearish, 'signal'] = -1

        self.df = df
        
        buy_signals = sum(df['signal'] == 1)
        sell_signals = sum(df['signal'] == -1)
        print(f"✅ Signals generated (Buys: {buy_signals}, Sells: {sell_signals})")

    def backtest(self):
        if self.df.empty or 'signal' not in self.df.columns:
            print("❌ No signals to backtest")
            return

        df = self.df
        capital = self.initial_capital
        position = None
        
        trades = 0
        wins = 0
        losses = 0
        
        self.equity_curve = [capital] # FIX 3: Actually populate the equity curve

        for i in range(1, len(df)):
            row = df.iloc[i]
            price = float(row['Close'])
            signal = int(row['signal'])

            if position is None:
                if signal == 1:
                    position = price
            else:
                pnl_pct = (price - position) / position

                # Take Profit (4%)
                if pnl_pct >= 0.04:
                    capital *= 1.04
                    trades += 1
                    wins += 1
                    position = None
                # Stop Loss (2%)
                elif pnl_pct <= -0.02:
                    capital *= 0.98
                    trades += 1
                    losses += 1
                    position = None
            
            self.equity_curve.append(capital)

        self.current_capital = capital
        self.trades = trades
        self.wins = wins
        self.losses = losses
        print("✅ Backtest complete")

    def performance_report(self):
        if self.trades == 0:
            print("❌ No completed trades (Strategy conditions might be too strict)")
            return

        roi = ((self.current_capital - self.initial_capital) / self.initial_capital) * 100
        win_rate = (self.wins / max(self.trades, 1)) * 100

        print("\n" + "═"*40)
        print(" ICHIMOKU STRATEGY REPORT")
        print("═"*40)
        print(f"Total Trades : {self.trades}")
        print(f"Wins         : {self.wins}")
        print(f"Losses       : {self.losses}")
        print(f"Win Rate     : {win_rate:.2f}%")
        print(f"ROI          : {roi:+.2f}%")
        print(f"Final Capital: ₹{self.current_capital:,.2f}")
        print("═"*40 + "\n")

    def plot_results(self):
        if len(self.equity_curve) == 0:
            print("❌ No equity curve data")
            return

        try:
            import matplotlib.pyplot as plt
            
            plt.figure(figsize=(12, 6))
            plt.plot(self.equity_curve, color='blue', linewidth=1.5, label="Equity Curve")
            plt.axhline(y=self.initial_capital, color='r', linestyle='--', label='Initial Capital')
            
            plt.title(f"{self.ticker} - Ichimoku + RSI Equity Curve")
            plt.xlabel("Days")
            plt.ylabel("Portfolio Value (₹)")
            plt.grid(True, alpha=0.3)
            plt.legend()
            plt.tight_layout()
            plt.show()
            print("✅ Plot displayed")
        except Exception as e:
            print(f"❌ Plot failed: {e}")

    def optimize_rsi(self):
        """FIX 4: Download data ONCE, then loop. Prevents rate limits."""
        print("\n🔍 Optimizing RSI Threshold...")
        
        # Load data and build indicators ONLY ONCE
        if self.df.empty:
            self.load_data()
        if 'rsi' not in self.df.columns:
            self.build_indicators()
            
        if self.df.empty:
            print("❌ Cannot optimize without data.")
            return

        best_threshold = None
        best_return = -999
        results = []

        # Test thresholds from 30 to 45
        for threshold in range(30, 46):
            self.rsi_threshold = threshold
            self.generate_signals()
            self.backtest()
            
            roi = ((self.current_capital - self.initial_capital) / self.initial_capital) * 100
            results.append((threshold, self.trades, roi))
            
            print(f"   RSI={threshold:2d} | Trades: {self.trades:3d} | ROI: {roi:+6.2f}%")

            if roi > best_return and self.trades >= 5: # Must have at least 5 trades to be valid
                best_return = roi
                best_threshold = threshold

        print("\n" + "═"*40)
        print(" RSI OPTIMIZATION COMPLETE")
        print("═"*40)
        if best_threshold:
            print(f"🏆 Best RSI Threshold : {best_threshold}")
            print(f"📈 Best ROI          : {best_return:+.2f}%")
        else:
            print("⚠️ No profitable threshold found with >5 trades.")
        print("═"*40 + "\n")
        
        # Reset to best threshold
        if best_threshold:
            self.rsi_threshold = best_threshold


# =====================================
# RUN THE STRATEGY
# =====================================
if __name__ == "__main__":
    # Initialize
    bot = IchimokuRSIStrategy(
        ticker="RELIANCE.NS",
        start="2020-01-01",
        end="2024-01-01", # Changed to 2024 to ensure data is fully available
        initial_capital=100000,
        rsi_threshold=40
    )
    
    # Run Pipeline
    bot.load_data()
    bot.build_indicators()
    bot.generate_signals()
    bot.backtest()
    bot.performance_report()
    
    # Optional: Plot (requires matplotlib)
    # bot.plot_results()
    
    # Optional: Find the best RSI setting
    # bot.optimize_rsi()