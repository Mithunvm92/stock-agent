#!/usr/bin/env python3
"""
Initialize demo metrics for Grafana dashboard
"""
from prometheus_client import start_http_server, Gauge

# Start metrics server
start_http_server(8000)

# Define gauges (same as utils/metrics)
current_capital = Gauge('bot_current_capital_inr', 'Current capital')
total_pnl = Gauge('bot_total_pnl_inr', 'Total PnL')
daily_pnl = Gauge('bot_daily_pnl_inr', 'Daily PnL')
win_rate = Gauge('bot_win_rate_percent', 'Win rate')
open_positions = Gauge('bot_open_positions_count', 'Open positions')
trade_count = Gauge('bot_trade_count', 'Trade count')
wins = Gauge('bot_wins_count', 'Wins')
losses = Gauge('bot_losses_count', 'Losses')
signal_confidence = Gauge('bot_latest_signal_confidence', 'Signal confidence')

# Set demo values
current_capital.set(125000)  # Starting capital
total_pnl.set(8500)    # Total PnL
daily_pnl.set(1200)    # Today's PnL
win_rate.set(62.5)     # 62.5% win rate
open_positions.set(3)    # 3 positions
trade_count.set(24)     # 24 trades
wins.set(15)           # 15 wins
losses.set(9)          # 9 losses
signal_confidence.set(78) # 78% confidence

print("✅ Demo metrics initialized on :8000/metrics")
print("   Capital: ₹125,000")
print("   PnL: ₹8,500")
print("   Win Rate: 62.5%")
print("   Positions: 3")
print()
print("Press Ctrl+C to stop")
import time
while True:
    time.sleep(60)
