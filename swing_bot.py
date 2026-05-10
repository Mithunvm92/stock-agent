"""
Swing Trading Bot - Complete implementation for NSE swing trading
v1 — Uses RSI + MACD + Moving Averages with proper risk management

Usage:
    python swing_bot.py --ticker RELIANCE.NS --capital 100000 --mode paper
    python swing_bot.py --ticker SBIN.NS --mode live --interval 300
"""

import os
import sys
import time
import json
import warnings
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple

import pandas as pd
import numpy as np
import yfinance as yf
import requests

# Suppress warnings
warnings.filterwarnings('ignore')


class SwingBot:
    """
    Swing Trading Bot for Indian NSE stocks
    
    Strategy:
    - Entry: RSI low (<50) + MACD bullish + Price above SMA20
    - Exit: Stop loss (2%) or Target (4%) or RSI overbought
    - Hold: 3-10 days (swing period)
    """
    
    # Default NSE tickers
    DEFAULT_TICKERS = [
        "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS",
        "ICICIBANK.NS", "KOTAKBANK.NS", "SBIN.NS", "BHARTIARTL.NS"
    ]
    
    def __init__(
        self,
        ticker: str = "RELIANCE.NS",
        initial_capital: float = 100000,
        mode: str = "paper"  # "paper" or "live"
    ):
        self.ticker = ticker
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.mode = mode
        
        # Risk settings
        self.risk_per_trade = 0.02  # 2% risk per trade
        self.stop_loss_pct = 0.02  # 2% stop loss
        self.target_pct = 0.04  # 4% target profit
        
        # Position tracking
        self.position = None  # {"entry": price, "shares": n, "signal": "BUY"/"SELL"}
        self.trade_history = []
        self.wins = 0
        self.losses = 0
        
        # Data cache
        self.df = None
        self.last_fetch = None
        
        print(f"\n📈 Swing Trading Bot initialized")
        print(f"   Ticker: {ticker}")
        print(f"   Capital: ₹{initial_capital:,.0f}")
        print(f"   Mode: {mode}")
        
    # ===================
    # DATA FETCHING
    # ===================
    def fetch_data(self, period: str = "1y") -> pd.DataFrame:
        """Fetch OHLCV data with caching"""
        # Check cache
        safe_ticker = self.ticker.replace(".", "_")
        cache_file = f"db/swing_cache_{safe_ticker}.csv"
        
        if os.path.exists(cache_file):
            try:
                cached = pd.read_csv(cache_file, index_col=0, parse_dates=True)
                if len(cached) > 0:
                    age = (datetime.now() - cached.index[-1]).days
                    if age < 1:
                        print(f"📂 Using cached data ({len(cached)} rows)")
                        self.df = cached
                        return cached
            except:
                pass
        
        # Fetch fresh data
        print(f"📥 Fetching {self.ticker}...")
        
        try:
            stock = yf.Ticker(self.ticker)
            df = stock.history(period=period, auto_adjust=True)
            
            if df is not None and len(df) > 100:
                # Save cache
                os.makedirs("db", exist_ok=True)
                df.to_csv(cache_file)
                print(f"✅ Loaded {len(df)} rows")
                self.df = df
                return df
            else:
                print(f"⚠️ No data returned")
        except Exception as e:
            print(f"❌ Fetch error: {e}")
        
        return pd.DataFrame()
    
    # ===================
    # INDICATORS
    # ===================
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators"""
        df = df.copy()
        
        close = df['Close']
        high = df['High']
        low = df['Low']
        volume = df['Volume']
        
        # RSI (14)
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss.replace(0, np.nan)
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        df['MACD'] = ema12 - ema26
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
        
        # Moving Averages
        df['SMA20'] = close.rolling(window=20).mean()
        df['SMA50'] = close.rolling(window=50).mean()
        df['SMA200'] = close.rolling(window=200).mean()
        
        # EMA
        df['EMA9'] = close.ewm(span=9, adjust=False).mean()
        
        # ATR (Average True Range)
        high_low = high - low
        high_close = (high - close.shift()).abs()
        low_close = (low - close.shift()).abs()
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['ATR'] = true_range.rolling(window=14).mean()
        df['ATR_Pct'] = (df['ATR'] / close) * 100
        
        # Volume
        df['Volume_SMA20'] = volume.rolling(window=20).mean()
        df['Volume_Ratio'] = volume / df['Volume_SMA20']
        
        # Price position
        df['Close_SMA20_Pct'] = ((close - df['SMA20']) / df['SMA20']) * 100
        
        # Bollinger Bands
        df['BB_Mid'] = close.rolling(window=20).mean()
        bb_std = close.rolling(window=20).std()
        df['BB_Upper'] = df['BB_Mid'] + (bb_std * 2)
        df['BB_Lower'] = df['BB_Mid'] - (bb_std * 2)
        df['BB_Width'] = df['BB_Upper'] - df['BB_Lower']
        
        # Stochastic
        low14 = low.rolling(window=14).min()
        high14 = high.rolling(window=14).max()
        df['Stoch_K'] = 100 * (close - low14) / (high14 - low14).replace(0, np.nan)
        df['Stoch_D'] = df['Stoch_K'].rolling(window=3).mean()
        
        # Fill NaN
        df.fillna(0, inplace=True)
        
        return df
    
    # ===================
    # SIGNAL GENERATION
    # ===================
    def generate_signal(self) -> Tuple[str, float, str]:
        """
        Generate trading signal
        
        Returns: (signal, confidence, reason)
        """
        if self.df is None or len(self.df) < 50:
            return "HOLD", 0, "No data"
        
        df = self.calculate_indicators(self.df)
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        
        # Current values
        close = latest['Close']
        rsi = latest['RSI']
        macd_hist = latest['MACD_Hist']
        prev_macd_hist = prev['MACD_Hist']
        sma20 = latest['SMA20']
        sma50 = latest['SMA50']
        volume_ratio = latest['Volume_Ratio']
        atr_pct = latest['ATR_Pct']
        price_sma20_pct = ((close - sma20) / sma20) * 100
        
        # ===== SELL / EXIT CONDITIONS (check first!) =====
        if self.position and self.position['signal'] == 'BUY':
            pnl_pct = (close - self.position['entry']) / self.position['entry']
            exit_reason = ""
            exit_score = 0
            
            # 1. Stop loss hit
            if pnl_pct <= -self.stop_loss_pct:
                exit_score = 5
                exit_reason = f"Stop loss ({pnl_pct*100:.1f}%)"
            
            # 2. Target reached
            elif pnl_pct >= self.target_pct:
                exit_score = 5
                exit_reason = f"Target hit ({pnl_pct*100:.1f}%)"
            
            # 3. RSI overbought + weakening MACD
            elif rsi > 65 and macd_hist < prev_macd_hist:
                exit_score = 4
                exit_reason = f"RSI overbought + MACD weakening"
            
            # 4. Price below SMA20 (trend reversal)
            elif close < sma20:
                exit_score = 3
                exit_reason = "Price below SMA20"
            
            # 5. Time-based exit (5+ days in profit)
            elif 'opened_at' in self.position:
                days_held = (datetime.now() - self.position['opened_at']).days
                if days_held >= 5 and pnl_pct > 0:
                    exit_score = 3
                    exit_reason = f"Time exit ({days_held}d, +{pnl_pct*100:.1f}%)"
            
            if exit_score >= 3:
                return "SELL", min(exit_score * 20, 100), exit_reason
        
        # ===== NEW BUY SIGNALS =====
        buy_score = 0
        buy_reasons = []
        
        # 1. RSI in oversold zone (<45)
        if rsi < 35:
            buy_score += 4
            buy_reasons.append(f"RSI oversold ({rsi:.0f})")
        elif rsi < 50:
            buy_score += 2
            buy_reasons.append(f"RSI low ({rsi:.0f})")
        
        # 2. MACD bullish (histogram turning positive or rising)
        if prev_macd_hist < 0 and macd_hist > 0:
            buy_score += 4
            buy_reasons.append("MACD bullish cross")
        elif macd_hist > 0 and macd_hist > prev_macd_hist:
            buy_score += 2
            buy_reasons.append("MACD rising")
        
        # 3. Price in uptrend (above key moving averages)
        if close > sma20 > 0:
            buy_score += 2
            buy_reasons.append(f"Above SMA20 (+{price_sma20_pct:.1f}%)")
        if close > sma50 > 0:
            buy_score += 1
            buy_reasons.append("Above SMA50")
        
        # 4. Volume confirmation
        if volume_ratio > 1.0:
            buy_score += 1
            buy_reasons.append(f"Vol {volume_ratio:.1f}x")
        
        # 5. Low volatility (safe entry)
        if atr_pct < 3.0:
            buy_score += 1
            buy_reasons.append(f"Low ATR ({atr_pct:.1f}%)")
        
        # Check for existing position (no new entry if already in)
        if self.position:
            return "HOLD", buy_score * 10, f"In position (entry: ₹{self.position['entry']:.0f})"
        
        # ===== DECISION =====
        if buy_score >= 5:
            confidence = min(buy_score * 12, 100)
            return "BUY", confidence, "; ".join(buy_reasons[:3])
        
        if buy_score >= 3:
            confidence = min(buy_score * 15, 90)
            return "BUY", confidence, "; ".join(buy_reasons[:2])
        
        return "HOLD", max(buy_score * 8, 30), f"RSI={rsi:.0f}, MACD={macd_hist:.1f}, Price={price_sma20_pct:+.1f}% vs SMA20"
    
    # ===================
    # POSITION SIZING
    # ===================
    def calculate_shares(self, price: float, stop_price: float) -> int:
        """Calculate position size based on risk"""
        risk_amount = self.current_capital * self.risk_per_trade
        risk_per_share = abs(price - stop_price)
        
        if risk_per_share > 0:
            shares = int(risk_amount / risk_per_share)
        else:
            shares = int(risk_amount / price)
        
        # Ensure we can afford at least 1 share
        max_affordable = int(self.current_capital * 0.9 / price)
        shares = min(shares, max_affordable)
        
        return max(shares, 1)
    
    # ===================
    # EXECUTE TRADE
    # ===================
    def execute_signal(self, signal: str = None, confidence: float = 0, reason: str = "") -> bool:
        """Execute trading signal"""
        if signal is None:
            signal, confidence, reason = self.generate_signal()
        
        if signal == "HOLD":
            return False
        
        price = self.df['Close'].iloc[-1] if self.df is not None else 0
        
        if price <= 0:
            print("❌ No valid price")
            return False
        
        # Calculate stop loss and target
        if signal == "BUY":
            stop_loss = price * (1 - self.stop_loss_pct)
            take_profit = price * (1 + self.target_pct)
            
            # Check if we can trade
            if self.position:
                print("⚠️ Position already open")
                return False
            
            # Calculate shares
            shares = self.calculate_shares(price, stop_loss)
            cost = price * shares
            
            if cost > self.current_capital:
                print("❌ Insufficient capital")
                return False
            
            # Execute BUY
            self.position = {
                'signal': 'BUY',
                'entry': price,
                'shares': shares,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'opened_at': datetime.now(),
                'reason': reason
            }
            
            self.current_capital -= cost
            
            print(f"\n{'='*40}")
            print(f"✅ BUY EXECUTED")
            print(f"{'='*40}")
            print(f"   Ticker: {self.ticker}")
            print(f"   Price:  ₹{price:.2f}")
            print(f"   Shares: {shares}")
            print(f"   Value:  ₹{cost:.2f}")
            print(f"   Stop:   ₹{stop_loss:.2f} (-{self.stop_loss_pct*100:.0f}%)")
            print(f"   Target: ₹{take_profit:.2f} (+{self.target_pct*100:.0f}%)")
            print(f"   Reason: {reason}")
            print(f"   Capital: ₹{self.current_capital:.2f}")
            print(f"{'='*40}\n")
            
            self.log_trade(signal, price, shares, confidence, reason)
            return True
            
        elif signal == "SELL" and self.position:
            # Execute SELL
            proceeds = price * self.position['shares']
            pnl = proceeds - (self.position['entry'] * self.position['shares'])
            pnl_pct = pnl / (self.position['entry'] * self.position['shares']) * 100
            
            self.current_capital += proceeds
            
            is_win = pnl > 0
            if is_win:
                self.wins += 1
            else:
                self.losses += 1
            
            # Log trade
            self.trade_history.append({
                'ticker': self.ticker,
                'entry': self.position['entry'],
                'exit': price,
                'shares': self.position['shares'],
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'signal': self.position['signal'],
                'exited_at': str(datetime.now())
            })
            
            print(f"\n{'='*40}")
            print(f"{'✅' if is_win else '❌'} SELL EXECUTED")
            print(f"{'='*40}")
            print(f"   Ticker: {self.ticker}")
            print(f"   Entry:  ₹{self.position['entry']:.2f}")
            print(f"   Exit:   ₹{price:.2f}")
            print(f"   P&L:    ₹{pnl:+.2f} ({pnl_pct:+.1f}%)")
            print(f"   Capital: ₹{self.current_capital:.2f}")
            print(f"   Reason: {reason}")
            print(f"{'='*40}\n")
            
            self.position = None
            return True
        
        return False
    
    # ===================
    # LOGGING
    # ===================
    def log_trade(self, signal, price, shares, confidence, reason):
        """Log trade to file"""
        try:
            os.makedirs("db", exist_ok=True)
            log_file = "db/swing_trades.csv"
            
            entry = {
                'timestamp': datetime.now().isoformat(),
                'ticker': self.ticker,
                'signal': signal,
                'price': price,
                'shares': shares,
                'confidence': confidence,
                'reason': reason,
                'capital': self.current_capital,
                'mode': self.mode
            }
            
            df = pd.DataFrame([entry])
            
            if os.path.exists(log_file):
                existing = pd.read_csv(log_file)
                df = pd.concat([existing, df], ignore_index=True)
            
            df.to_csv(log_file, index=False)
        except Exception as e:
            print(f"⚠️ Log error: {e}")
    
    # ===================
    # STATUS
    # ===================
    def get_status(self) -> Dict:
        """Get bot status"""
        total = self.wins + self.losses
        win_rate = (self.wins / total * 100) if total > 0 else 0
        
        # Calculate unrealized P&L
        unrealized_pnl = 0
        if self.position and self.df is not None:
            current_price = self.df['Close'].iloc[-1]
            unrealized_pnl = (current_price - self.position['entry']) * self.position['shares']
        
        return {
            'ticker': self.ticker,
            'mode': self.mode,
            'capital': self.current_capital,
            'initial_capital': self.initial_capital,
            'pnl': unrealized_pnl,
            'position': self.position is not None,
            'wins': self.wins,
            'losses': self.losses,
            'win_rate': win_rate
        }
    
    def print_status(self):
        """Print bot status"""
        s = self.get_status()
        
        print(f"\n{'='*40}")
        print(f"   SWING BOT STATUS")
        print(f"{'='*40}")
        print(f"   Ticker:      {s['ticker']}")
        print(f"   Mode:        {s['mode']}")
        print(f"   Capital:     ₹{s['capital']:,.0f}")
        print(f"   P&L:         ₹{s['pnl']:+,.0f}")
        print(f"   Position:    {'OPEN' if s['position'] else 'NONE'}")
        print(f"   Win Rate:    {s['win_rate']:.0f}% ({s['wins']}W/{s['losses']}L)")
        print(f"{'='*40}\n")
    
    # ===================
    # RUN LOOP
    # ===================
    def run(self, interval_seconds: int = 300, max_iterations: int = None):
        """Run trading loop"""
        print(f"\n🔴 Starting Swing Bot ({interval_seconds}s interval)")
        
        iteration = 0
        
        while True:
            try:
                iteration += 1
                
                # Fetch latest data
                self.fetch_data()
                
                # Generate and execute signal
                signal, confidence, reason = self.generate_signal()
                
                print(f"\n📊 Iteration {iteration}")
                print(f"   Time: {datetime.now().strftime('%H:%M:%S')}")
                print(f"   Signal: {signal} ({confidence:.0f}%)")
                print(f"   Reason: {reason}")
                
                # Execute
                self.execute_signal(signal, confidence, reason)
                
                # Print status every 5 iterations
                if iteration % 5 == 0:
                    self.print_status()
                
                # Check max iterations
                if max_iterations and iteration >= max_iterations:
                    print(f"\n🛑 Max iterations reached")
                    break
                
                # Wait
                print(f"\n⏳ Waiting {interval_seconds}s...")
                time.sleep(interval_seconds)
                
            except KeyboardInterrupt:
                print("\n🛑 Stopped by user")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                time.sleep(60)
        
        # Final status
        self.print_status()


# ===================
# MAIN
# ===================
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Swing Trading Bot')
    parser.add_argument('--ticker', default='RELIANCE.NS', help='NSE ticker')
    parser.add_argument('--capital', type=float, default=100000, help='Initial capital')
    parser.add_argument('--mode', default='paper', choices=['paper', 'live'], help='Trading mode')
    parser.add_argument('--interval', type=int, default=300, help='Check interval (seconds)')
    parser.add_argument('--iterations', type=int, help='Max iterations')
    
    args = parser.parse_args()
    
    # Create and run bot
    bot = SwingBot(
        ticker=args.ticker,
        initial_capital=args.capital,
        mode=args.mode
    )
    
    # Single run (not loop)
    bot.fetch_data()
    signal, confidence, reason = bot.generate_signal()
    
    print(f"\n{'='*40}")
    print(f"   SIGNAL RESULT")
    print(f"{'='*40}")
    print(f"   Signal:     {signal}")
    print(f"   Confidence: {confidence:.0f}%")
    print(f"   Reason:     {reason}")
    print(f"{'='*40}")
    
    if args.mode == 'paper' and signal != 'HOLD':
        bot.execute_signal(signal, confidence, reason)
        bot.print_status()
    
    # Or run loop
    if args.interval > 0 and args.mode == 'live':
        bot.run(args.interval, args.iterations)


if __name__ == "__main__":
    main()