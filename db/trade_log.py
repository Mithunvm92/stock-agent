import csv
import os
import json
from datetime import datetime
from config.settings import TRADE_LOG_PATH


class TradeLogger:
    """Enhanced trade logger with analysis capabilities"""

    def __init__(self, log_path=None):
        self.log_path = log_path or TRADE_LOG_PATH
        self._init_log()

    def _init_log(self):
        """Create log file with headers if doesn't exist"""
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

        if not os.path.exists(self.log_path):
            with open(self.log_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp', 'ticker', 'signal', 'price',
                    'shares', 'confidence', 'reason',
                    'stop_loss', 'take_profit', 'pnl', 'capital',
                    'filters_passed', 'total_filters'
                ])
            print(f"📝 Trade log created → {self.log_path}")

    def log_trade(self, ticker, signal, price, shares, confidence,
                  reason, stop_loss, take_profit, pnl, capital,
                  filters_passed=0, total_filters=0):
        """Log a single trade"""
        with open(self.log_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ticker, signal, round(price, 2), shares,
                round(confidence, 2), reason,
                round(stop_loss, 2), round(take_profit, 2),
                round(pnl, 2), round(capital, 2),
                filters_passed, total_filters
            ])

    def get_history(self):
        """Read trade history as DataFrame"""
        import pandas as pd
        if os.path.exists(self.log_path):
            return pd.read_csv(self.log_path)
        return None

    def get_statistics(self):
        """Calculate trading statistics"""
        import pandas as pd
        
        df = self.get_history()
        if df is None or len(df) == 0:
            return {}

        # Filter only closed trades (with P&L)
        closed = df[df['pnl'] != 0].copy()
        
        if len(closed) == 0:
            return {'total_trades': len(df), 'closed_trades': 0}

        wins = closed[closed['pnl'] > 0]
        losses = closed[closed['pnl'] <= 0]

        stats = {
            'total_trades': len(df),
            'closed_trades': len(closed),
            'wins': len(wins),
            'losses': len(losses),
            'win_rate': (len(wins) / len(closed)) * 100 if len(closed) > 0 else 0,
            'total_pnl': closed['pnl'].sum(),
            'avg_win': wins['pnl'].mean() if len(wins) > 0 else 0,
            'avg_loss': abs(losses['pnl'].mean()) if len(losses) > 0 else 0,
            'largest_win': wins['pnl'].max() if len(wins) > 0 else 0,
            'largest_loss': losses['pnl'].min() if len(losses) > 0 else 0,
            'avg_confidence': closed['confidence'].mean(),
            'profit_factor': (wins['pnl'].sum() / abs(losses['pnl'].sum())) if len(losses) > 0 and losses['pnl'].sum() != 0 else 0,
        }

        return stats

    def print_statistics(self):
        """Print formatted statistics"""
        stats = self.get_statistics()
        
        if not stats:
            print("No trades recorded yet.")
            return

        print(f"\n📊 TRADING STATISTICS")
        print(f"{'='*40}")
        print(f"Total Trades:    {stats.get('total_trades', 0)}")
        print(f"Closed Trades:   {stats.get('closed_trades', 0)}")
        print(f"Wins:            {stats.get('wins', 0)}")
        print(f"Losses:          {stats.get('losses', 0)}")
        print(f"Win Rate:        {stats.get('win_rate', 0):.1f}%")
        print(f"Total P&L:       ₹{stats.get('total_pnl', 0):+,.2f}")
        print(f"Avg Win:         ₹{stats.get('avg_win', 0):+,.2f}")
        print(f"Avg Loss:        ₹{stats.get('avg_loss', 0):,.2f}")
        print(f"Largest Win:     ₹{stats.get('largest_win', 0):+,.2f}")
        print(f"Largest Loss:    ₹{stats.get('largest_loss', 0):,.2f}")
        print(f"Profit Factor:   {stats.get('profit_factor', 0):.2f}")
        print(f"Avg Confidence:  {stats.get('avg_confidence', 0):.1f}%")
        print(f"{'='*40}\n")
