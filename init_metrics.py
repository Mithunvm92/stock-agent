#!/usr/bin/env python3
"""
Init demo metrics for Grafana
"""
from prometheus_client import start_http_server, Gauge

start_http_server(8000)

capital = Gauge('bot_current_capital_inr', 'Capital')
pnl = Gauge('bot_total_pnl_inr', 'Total PnL')
daily_pnl = Gauge('bot_daily_pnl_inr', 'Daily PnL')
win_rate = Gauge('bot_win_rate_percent', 'Win Rate')
positions = Gauge('bot_open_positions_count', 'Positions')
trades = Gauge('bot_trade_count', 'Trades')
wins = Gauge('bot_wins_count', 'Wins')
losses = Gauge('bot_losses_count', 'Losses')
confidence = Gauge('bot_latest_signal_confidence', 'Confidence')

capital.set(125000)
pnl.set(8500)
daily_pnl.set(1200)
win_rate.set(62.5)
positions.set(3)
trades.set(24)
wins.set(15)
losses.set(9)
confidence.set(78)

print("Metrics on :8000 - Capital:₹125k PnL:₹8.5k Win:62.5%")
import time
while True: time.sleep(60)
