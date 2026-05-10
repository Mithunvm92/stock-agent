#!/usr/bin/env python3
"""
Prometheus Metrics Exporter for Trading Bot
Pushes metrics to Prometheus PushGateway
"""

import os
import time
from datetime import datetime
from prometheus_client import Counter, Gauge, Histogram, push_to_gateway


# Define metrics
pnl_gauge = Gauge('trading_pnl', 'Profit/Loss in INR')
capital_gauge = Gauge('trading_capital', 'Current Capital in INR')
wins_counter = Counter('trading_wins', 'Total Wins')
losses_counter = Counter('trading_losses', 'Total Losses')
trades_counter = Counter('trading_trades', 'Total Trades')
signal_gauge = Gauge('trading_signal', 'Current Signal (1=BUY, 0=HOLD, -1=SELL)')
position_gauge = Gauge('trading_position', 'Position Open (1=yes, 0=no)')
confidence_gauge = Gauge('trading_confidence', 'Signal Confidence')
entry_gauge = Gauge('trading_entry', 'Entry Price')
current_price_gauge = Gauge('trading_current_price', 'Current Price')


def update_metrics(bot=None, ticker='UNKNOWN'):
    """Update all metrics from bot state or defaults"""
    
    job_name = f"trading_bot_{ticker}"
    
    try:
        if bot:
            # Update from bot state
            pnl_gauge.set(bot.total_pnl)
            capital_gauge.set(bot.current_capital)
            wins_counter.inc(bot.wins - getattr(bot, '_last_wins', 0))
            losses_counter.inc(bot.losses - getattr(bot, '_last_losses', 0))
            trades_counter.inc()
            
            # Track changes
            bot._last_wins = bot.wins
            bot._last_losses = bot.losses
            
            # Signal
            if bot.signal:
                signal_gauge.set({'BUY': 1, 'SELL': -1, 'HOLD': 0}.get(bot.signal, 0))
            else:
                signal_gauge.set(0)
            
            # Position
            position_gauge.set(1 if bot.position else 0)
            
            # Confidence
            confidence_gauge.set(bot.confidence)
            
            # Entry price
            if bot.position:
                entry_gauge.set(bot.position.get('entry', 0))
            
            # Current price
            if bot.df is not None and len(bot.df) > 0:
                current_price_gauge.set(bot.df['Close'].iloc[-1])
        
        # Push to gateway
        gateway = os.getenv('PUSHGATEWAY', 'http://localhost:9091')
        
        try:
            push_to_gateway(gateway, job=job_name, grouping_key={'ticker': ticker})
            print(f"📊 Metrics pushed to {gateway}")
        except Exception as e:
            print(f"⚠️ Push gateway unavailable: {e}")
    
    except Exception as e:
        print(f"❌ Metrics error: {e}")


def export_trade(trade, ticker):
    """Export single trade to Prometheus"""
    
    job_name = f"trading_trades_{ticker}"
    
    # Create trade metrics
    trade_pnl = Gauge('trade_pnl', 'Trade P&L')
    trade_pnl.set(trade.get('pnl', 0))
    
    trade_shares = Gauge('trade_shares', 'Trade Shares')
    trade_shares.set(trade.get('shares', 0))
    
    trade_entry = Gauge('trade_entry', 'Entry Price')
    trade_entry.set(trade.get('entry', 0))
    
    trade_exit = Gauge('trade_exit', 'Exit Price')
    trade_exit.set(trade.get('exit', 0))
    
    try:
        gateway = os.getenv('PUSHGATEWAY', 'http://localhost:9091')
        push_to_gateway(gateway, job=job_name, grouping_key={'trade': str(time.time())})
    except:
        pass


if __name__ == "__main__":
    # Test
    print("📊 Testing Prometheus metrics...")
    update_metrics()