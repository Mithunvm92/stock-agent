#!/usr/bin/env python3
"""
Swing Bot Backtest - Test strategy on historical data
Usage: python swing_backtest.py --ticker SBIN.NS
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))

from swing_bot import SwingBot
import yfinance as yf
import pandas as pd


def backtest(ticker: str, initial_capital: float = 2000) -> dict:
    """Run backtest on 1 year historical data"""
    
    print(f"\n{'='*50}")
    print(f"   BACKTEST: {ticker}")
    print(f"{'='*50}")
    
    # Get 2 years of data (1 year for backtest + 1 year for indicators)
    print("📥 Fetching 2 years of data...")
    stock = yf.Ticker(ticker)
    df = stock.history(period="2y", auto_adjust=True)
    
    if df is None or len(df) < 250:
        print("❌ Insufficient data")
        return {}
    
    print(f"✅ {len(df)} rows loaded")
    
    # Initialize bot
    bot = SwingBot(ticker, initial_capital=initial_capital, mode='paper')
    bot.df = df
    
    # Backtest state
    cash = initial_capital
    position = None  # {'entry': price, 'shares': n, 'stop_loss': price}
    wins = 0
    losses = 0
    trades = []
    
    # Start from 1 year ago (skip first year for indicator warmup)
    start_idx = max(50, len(df) - 252)  # ~1 year of trading days
    
    print(f"\n🔄 Running backtest from day {start_idx} to {len(df)}...")
    
    for day in range(start_idx, len(df)):
        # Get current data slice
        current_df = df.iloc[:day+1].copy()
        
        # Calculate indicators on current slice
        current_df = bot.calculate_indicators(current_df)
        
        # Get current values
        close = current_df['Close'].iloc[-1]
        rsi = current_df['RSI'].iloc[-1]
        
        # Get previous day for MACD cross detection
        if day > start_idx:
            prev_rsi = current_df['RSI'].iloc[-2]
            prev_macd = current_df['MACD_Hist'].iloc[-2]
            macd = current_df['MACD_Hist'].iloc[-1]
        else:
            prev_rsi = rsi
            prev_macd = 0
            macd = 0
        
        sma20 = current_df['SMA20'].iloc[-1]
        sma50 = current_df['SMA50'].iloc[-1]
        volume_ratio = current_df['Volume_Ratio'].iloc[-1]
        atr_pct = current_df['ATR_Pct'].iloc[-1]
        
        # Get signals for the day (simulating real-time)
        price_sma20_pct = ((close - sma20) / sma20) * 100 if sma20 > 0 else 0
        
        # === SELL CHECK ===
        if position and position['signal'] == 'BUY':
            pnl_pct = (close - position['entry']) / position['entry']
            
            # Stop loss
            if pnl_pct <= -0.02:
                # SELL - Stop loss
                proceeds = close * position['shares']
                trade_pnl = proceeds - (position['entry'] * position['shares'])
                cash += proceeds
                trades.append({'type': 'SELL', 'pnl': trade_pnl, 'reason': 'STOP LOSS'})
                position = None
                losses += 1
                continue
            
            # Target reached
            if pnl_pct >= 0.04:
                # SELL - Take profit
                proceeds = close * position['shares']
                trade_pnl = proceeds - (position['entry'] * position['shares'])
                cash += proceeds
                trades.append({'type': 'SELL', 'pnl': trade_pnl, 'reason': 'TARGET'})
                position = None
                wins += 1
                continue
            
            # RSI overbought + MACD weakening
            if rsi > 65 and macd < prev_macd:
                proceeds = close * position['shares']
                trade_pnl = proceeds - (position['entry'] * position['shares'])
                cash += proceeds
                trades.append({'type': 'SELL', 'pnl': trade_pnl, 'reason': 'RSI OVERBOUGHT'})
                position = None
                if trade_pnl > 0:
                    wins += 1
                else:
                    losses += 1
                continue
            
            # Price below SMA20
            if close < sma20:
                proceeds = close * position['shares']
                trade_pnl = proceeds - (position['entry'] * position['shares'])
                cash += proceeds
                trades.append({'type': 'SELL', 'pnl': trade_pnl, 'reason': 'BELOW SMA20'})
                position = None
                if trade_pnl > 0:
                    wins += 1
                else:
                    losses += 1
                continue
        
        # === BUY CHECK ===
        elif not position:
            # Score the buy signal
            buy_score = 0
            
            if rsi < 35:
                buy_score += 4
            elif rsi < 50:
                buy_score += 2
            
            if macd > 0 and macd > prev_macd:
                buy_score += 2
            
            if close > sma20 > 0:
                buy_score += 2
            
            if close > sma50 > 0:
                buy_score += 1
            
            if volume_ratio > 1.0:
                buy_score += 1
            
            if atr_pct < 3.0:
                buy_score += 1
            
            # Execute BUY if score >= 5
            if buy_score >= 5:
                # Calculate shares
                risk_amount = cash * 0.02
                stop_loss = close * 0.98
                shares = int(risk_amount / (close - stop_loss))
                shares = min(shares, int(cash * 0.9 / close))
                shares = max(shares, 1)
                
                cost = close * shares
                if cost <= cash:
                    cash -= cost
                    position = {
                        'signal': 'BUY',
                        'entry': close,
                        'shares': shares,
                        'stop_loss': stop_loss
                    }
                    trades.append({'type': 'BUY', 'price': close, 'shares': shares})
    
    # Close any remaining position at end
    if position:
        close = df['Close'].iloc[-1]
        proceeds = close * position['shares']
        trade_pnl = proceeds - (position['entry'] * position['shares'])
        cash += proceeds
        trades.append({'type': 'SELL', 'pnl': trade_pnl, 'reason': 'END'})
        if trade_pnl > 0:
            wins += 1
        else:
            losses += 1
    
    # Calculate results
    total_trades = wins + losses
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
    final_capital = cash
    total_pnl = final_capital - initial_capital
    pnl_pct = (total_pnl / initial_capital) * 100
    
    # Print results
    print(f"\n{'='*50}")
    print(f"   BACKTEST RESULTS")
    print(f"{'='*50}")
    print(f"   Initial Capital:  ₹{initial_capital:,.0f}")
    print(f"   Final Capital:  ₹{final_capital:,.0f}")
    print(f"   Total P&L:      ₹{total_pnl:+,.0f} ({pnl_pct:+.1f}%)")
    print(f"   Total Trades:   {total_trades}")
    print(f"   Wins:         {wins}")
    print(f"   Losses:       {losses}")
    print(f"   Win Rate:     {win_rate:.0f}%")
    print(f"{'='*50}")
    
    # Print trade list
    print(f"\n📋 Trade History:")
    for i, t in enumerate(trades):
        if t['type'] == 'BUY':
            print(f"  {i+1}. BUY  @ ₹{t['price']:.2f} x {t['shares']} shares")
        else:
            pnl = t.get('pnl', 0)
            print(f"  {i+1}. SELL @ ₹{close:.2f} ({pnl:+,.0f}) - {t.get('reason','')}")
    
    return {
        'initial': initial_capital,
        'final': final_capital,
        'pnl': total_pnl,
        'pnl_pct': pnl_pct,
        'trades': total_trades,
        'wins': wins,
        'losses': losses,
        'win_rate': win_rate
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--ticker', default='SBIN.NS')
    parser.add_argument('--capital', type=float, default=2000)
    args = parser.parse_args()
    
    backtest(args.ticker, args.capital)