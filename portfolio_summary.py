#!/usr/bin/env python3
"""Portfolio Summary - shows trading stats"""
import csv, sys
from pathlib import Path

def main():
    trades = []
    try:
        with open('db/paper_trades.csv') as f:
            trades = list(csv.DictReader(f))
    except: pass
    
    if not trades:
        print("❌ No trades found")
        return
    
    total_pnl = sum(float(t.get('pnl', 0) or 0) for t in trades)
    wins = sum(1 for t in trades if float(t.get('pnl', 0) or 0) > 0)
    losses = sum(1 for t in trades if float(t.get('pnl', 0) or 0) < 0)
    positions = sum(1 for t in trades if t.get('signal') in ['BUY', 'SELL'])
    last_capital = float(trades[-1].get('capital', 1000) or 1000) if trades else 1000
    
    print("═" * 40)
    print("    MASTER TRADING PANEL")
    print("═" * 40)
    print(f"Total Trades   : {len(trades)}")
    print(f"Wins         : {wins}")
    print(f"Losses      : {losses}")
    print(f"Win Rate    : {wins*100/(wins+losses) if wins+losses else 0:.1f}%")
    print(f"Total PnL    : ₹{total_pnl:,.2f}")
    print(f"Current Cap  : ₹{last_capital:,.2f}")
    print(f"Open Pos    : {positions}")
    print("═" * 40)

if __name__ == "__main__":
    main()
