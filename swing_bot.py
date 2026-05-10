"""
Swing Trading Bot - Complete implementation for NSE swing trading
v2 — Silent mode, proxy support, 2000 INR capital
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

# Suppress warnings
warnings.filterwarnings('ignore')

# Silent mode - reduce output
SILENT = os.environ.get('SILENT', '0') == '1'
PROXY = os.environ.get('HTTPS_PROXY') or os.environ.get('HTTP_PROXY')

# Silent print helper
def slog(*args, **kwargs):
    if not SILENT:
        print(*args, **kwargs)

# Set proxy if configured
if PROXY:
    os.environ['http_proxy'] = PROXY
    os.environ['https_proxy'] = PROXY
    slog(f"🔐 Using proxy: {PROXY}")


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
        initial_capital: float = 2000,
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
    def fetch_data(self, period: str = "1y", force: bool = False) -> pd.DataFrame:
        """Fetch OHLCV data with caching"""
        # Check cache first (always use cache if available)
        safe_ticker = self.ticker.replace(".", "_")
        cache_file = f"db/swing_cache_{safe_ticker}.csv"
        
        if not force and os.path.exists(cache_file):
            try:
                cached = pd.read_csv(cache_file, index_col=0, parse_dates=True)
                if len(cached) > 100:
                    # Cache valid for 1 day (reduced API calls)
                    age = (datetime.now() - cached.index[-1]).days
                    if not SILENT: print(f"📂 Using cached data ({len(cached)} rows, {age}d old)")
                    self.df = cached
                    return cached
            except:
                pass
        
        # Check rate limit file
        rate_file = "db/.rate_limit"
        if os.path.exists(rate_file):
            with open(rate_file, 'r') as f:
                limit_time = datetime.fromisoformat(f.read())
                if datetime.now() < limit_time:
                    remaining = (limit_time - datetime.now()).seconds
                    print(f"⏳ Rate limited. Wait {remaining}s...")
                    # Try to use old cache instead
                    if os.path.exists(cache_file):
                        try:
                            cached = pd.read_csv(cache_file, index_col=0, parse_dates=True)
                            if len(cached) > 100:
                                print("📂 Using stale cache due to rate limit")
                                self.df = cached
                                return cached
                        except:
                            pass
                    return pd.DataFrame()
        
        # Fetch fresh data with retry
        if not SILENT: print(f"📥 Fetching {self.ticker}...")
        
        for attempt in range(3):
            try:
                stock = yf.Ticker(self.ticker)
                df = stock.history(period=period, auto_adjust=True)
                
                if df is not None and len(df) > 100:
                    # Save cache
                    os.makedirs("db", exist_ok=True)
                    df.to_csv(cache_file)
                    if not SILENT: print(f"✅ Loaded {len(df)} rows")
                    self.df = df
                    return df
                    
            except Exception as e:
                if "Too Many Requests" in str(e) or "rate limited" in str(e):
                    # Set rate limit for 15 minutes (silent)
                    os.makedirs("db", exist_ok=True)
                    with open(rate_file, 'w') as f:
                        f.write((datetime.now() + timedelta(minutes=15)).isoformat())
                    # Use local cache silently
                    if os.path.exists(cache_file):
                        try:
                            cached = pd.read_csv(cache_file, index_col=0, parse_dates=True)
                            if len(cached) > 50:
                                self.df = cached
                                return cached
                        except:
                            pass
                    return pd.DataFrame()
                    
                if attempt < 2:
                    wait = (attempt + 1) * 5
                    if not SILENT: print(f"⚠️ Attempt {attempt+1} failed, retrying in {wait}s...")
                    time.sleep(wait)
        
        if not SILENT: print(f"❌ Fetch failed for {self.ticker}")
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
        Generate trading signal using enhanced PKScreener multi-indicator strategy
        
        Weighted signals:
        - RSI: 15% (oversold/overbought)
        - MACD: 15% (crossovers)
        - ATR Trailing Stop: 20% (key risk management!)
        - Volume: 15% (price confirmation)
        - MA Crossovers: 15% (trend)
        - Price Action: 10% (patterns)
        - Momentum: 10% (strength)
        """
        if self.df is None or len(self.df) < 50:
            return "HOLD", 0, "No data"
        
        df = self.calculate_indicators(self.df)
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        prev2 = df.iloc[-3] if len(df) > 2 else prev
        
        # Current values
        close = latest['Close']
        rsi = latest['RSI']
        macd_hist = latest['MACD_Hist']
        prev_macd_hist = prev['MACD_Hist']
        sma20 = latest['SMA20']
        sma50 = latest['SMA50']
        volume_ratio = latest['Volume_Ratio']
        atr = latest['ATR']
        
        # ATR trailing stop (key risk management from PKScreener!)
        key_value = 2
        trailing_stop = close - (key_value * atr)
        price_vs_trailing = close / trailing_stop if trailing_stop > 0 else 1
        
        # Price change
        price_change = (close - df['Close'].iloc[-2]) / df['Close'].iloc[-2]
        mom_5d = (close - df['Close'].iloc[-5]) / df['Close'].iloc[-5] if len(df) > 5 else 0
        
        # Signal weights
        weights = {'rsi': 0.15, 'macd': 0.15, 'atr_trailing': 0.20, 'volume': 0.15, 
                 'ma_crossover': 0.15, 'price_action': 0.10, 'momentum': 0.10}
        
        signals = {}
        reasons = {}
        
        # 1. RSI (15%)
        if rsi < 30: signals['rsi'] = 0.8; reasons['rsi'] = f"RSI oversold ({rsi:.0f})"
        elif rsi < 40: signals['rsi'] = 0.65; reasons['rsi'] = f"RSI low ({rsi:.0f})"
        elif rsi > 70: signals['rsi'] = 0.2; reasons['rsi'] = f"RSI overbought ({rsi:.0f})"
        elif rsi > 60: signals['rsi'] = 0.35; reasons['rsi'] = f"RSI high ({rsi:.0f})"
        else: signals['rsi'] = 0.5; reasons['rsi'] = f"RSI neutral"
        
        # 2. MACD (15%)
        if prev_macd_hist <= 0 and macd_hist > 0: signals['macd'] = 0.85; reasons['macd'] = "MACD bullish cross"
        elif prev_macd_hist >= 0 and macd_hist < 0: signals['macd'] = 0.15; reasons['macd'] = "MACD bearish cross"
        elif macd_hist > prev_macd_hist: signals['macd'] = 0.7; reasons['macd'] = "MACD rising"
        elif macd_hist < prev_macd_hist: signals['macd'] = 0.3; reasons['macd'] = "MACD falling"
        else: signals['macd'] = 0.5
        
        # 3. ATR Trailing Stop (20%) - Key!
        if price_vs_trailing > 1.02: signals['atr_trailing'] = 0.75; reasons['atr_trailing'] = "Above ATR stop"
        elif price_vs_trailing < 0.98: signals['atr_trailing'] = 0.25; reasons['atr_trailing'] = "Below ATR stop"
        else: signals['atr_trailing'] = 0.5
        
        # 4. Volume (15%)
        if volume_ratio > 2 and price_change > 0.01: signals['volume'] = 0.85; reasons['volume'] = f"Vol surge"
        elif volume_ratio > 1.5 and price_change > 0: signals['volume'] = 0.7; reasons['volume'] = "High vol"
        elif volume_ratio > 2 and price_change < -0.01: signals['volume'] = 0.15; reasons['volume'] = "Vol surge -drop"
        elif volume_ratio > 1.5 and price_change < 0: signals['volume'] = 0.3; reasons['volume'] = "High vol -loss"
        else: signals['volume'] = 0.5
        
        # 5. MA Crossover (15%)
        if close > sma20 > sma50: signals['ma_crossover'] = 0.75; reasons['ma_crossover'] = "Above 20>50"
        elif close < sma20 < sma50: signals['ma_crossover'] = 0.25; reasons['ma_crossover'] = "Below 20<50"
        elif close > sma20: signals['ma_crossover'] = 0.6; reasons['ma_crossover'] = "Above SMA20"
        else: signals['ma_crossover'] = 0.4
        
        # 6. Price Action (10%)
        if price_change > 0.03: signals['price_action'] = 0.7; reasons['price_action'] = "Strong gain"
        elif price_change > 0.01: signals['price_action'] = 0.6; reasons['price_action'] = "Gaining"
        elif price_change < -0.03: signals['price_action'] = 0.3; reasons['price_action'] = "Strong loss"
        elif price_change < -0.01: signals['price_action'] = 0.4; reasons['price_action'] = "Losing"
        else: signals['price_action'] = 0.5
        
        # 7. Momentum (10%)
        if mom_5d > 0.05: signals['momentum'] = 0.75; reasons['momentum'] = "Strong +5d"
        elif mom_5d > 0.02: signals['momentum'] = 0.6; reasons['momentum'] = "Weak +5d"
        elif mom_5d < -0.05: signals['momentum'] = 0.25; reasons['momentum'] = "Strong -5d"
        elif mom_5d < -0.02: signals['momentum'] = 0.4; reasons['momentum'] = "Weak -5d"
        else: signals['momentum'] = 0.5
        
        # Calculate weighted score
        weighted_score = sum(signals.get(k, 0.5) * v for k, v in weights.items())
        normalized_score = weighted_score * 100
        confidence = min(100, abs(normalized_score - 50) * 2)
        
        # Exit conditions (check position first!)
        if self.position and self.position['signal'] == 'BUY':
            pnl_pct = (close - self.position['entry']) / self.position['entry']
            if close < trailing_stop: return "SELL", 95, "ATR stop hit"
            if pnl_pct >= 0.04: return "SELL", 90, "Target hit"
            if pnl_pct <= -0.02: return "SELL", 95, "Stop loss"
            if rsi > 65 and macd_hist < prev_macd_hist: return "SELL", 70, "RSI overbought"
        
        # Check for existing position
        if self.position:
            return "HOLD", confidence, f"In position @ ₹{self.position['entry']:.0f}"
        
        # Buy signal (score >= 65)
        if normalized_score >= 65:
            top_reasons = sorted([(k, v) for k, v in reasons.items() if signals.get(k, 0.5) > 0.6], 
                        key=lambda x: signals.get(x[0]), reverse=True)[:3]
            return "BUY", confidence, "; ".join([reasons.get(r[0]) for r in top_reasons])
        
        # Sell signal (score <= 35)
        if normalized_score <= 35:
            return "SELL", confidence, "Weak signals"
        
        return "HOLD", confidence, f"Neutral ({normalized_score:.0f})"
    
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
            if not SILENT: print(f"✅ BUY EXECUTED")
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
            if not SILENT: print(f"⚠️ Log error: {e}")
    
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