import json
import os
import time
from datetime import datetime
from data.fetcher import DataFetcher
from features.engineer import FeatureEngineer
from models.ml_model import MLModel
from strategies.signal_strategy import SignalStrategy
from utils.risk_manager import RiskManager
from db.trade_log import TradeLogger
from alerts.telegram_bot import TelegramAlert
from config.settings import (
    PRIMARY_TICKER, LOOKBACK_PERIOD, TICKERS,
    INITIAL_CAPITAL, PAPER_TRADE_LOG_PATH, PAPER_PORTFOLIO_PATH,
    PAPER_SCAN_INTERVAL_SECONDS, STOP_LOSS_PCT, TAKE_PROFIT_PCT,
    MAX_OPEN_POSITIONS
)


class PaperTrader:
    """
    Paper Trading Simulator
    
    Simulates real trading without risking money:
    - Scans stocks for signals
    - Opens paper positions
    - Tracks P&L
    - Closes positions on SL/TP/Time
    - Saves state to disk (survives restart)
    - Sends Telegram alerts
    """

    def __init__(self):
        self.capital = INITIAL_CAPITAL
        self.starting_capital = INITIAL_CAPITAL
        self.positions = []  # Open positions
        self.closed_trades = []  # Completed trades
        self.model = MLModel()
        self.telegram = TelegramAlert()
        self.logger = TradeLogger(PAPER_TRADE_LOG_PATH)
        self.is_running = False
        
        # Load saved state
        self._load_state()

    def _load_state(self):
        """Load saved portfolio state"""
        if os.path.exists(PAPER_PORTFOLIO_PATH):
            try:
                with open(PAPER_PORTFOLIO_PATH, 'r') as f:
                    state = json.load(f)
                    self.capital = state.get('capital', INITIAL_CAPITAL)
                    self.starting_capital = state.get('starting_capital', INITIAL_CAPITAL)
                    self.positions = state.get('positions', [])
                    self.closed_trades = state.get('closed_trades', [])
                    print(f"📂 Loaded paper portfolio: Capital=₹{self.capital:,.2f}, "
                          f"Open={len(self.positions)}, Closed={len(self.closed_trades)}")
            except Exception as e:
                print(f"⚠️ Could not load state: {e}")

    def _save_state(self):
        """Save portfolio state to disk"""
        os.makedirs(os.path.dirname(PAPER_PORTFOLIO_PATH), exist_ok=True)
        state = {
            'capital': self.capital,
            'starting_capital': self.starting_capital,
            'positions': self.positions,
            'closed_trades': self.closed_trades,
            'last_updated': datetime.now().isoformat()
        }
        with open(PAPER_PORTFOLIO_PATH, 'w') as f:
            json.dump(state, f, indent=2, default=str)

    def get_current_price(self, ticker):
        """Get current price for a ticker"""
        try:
            fetcher = DataFetcher(ticker, "5d")
            fetcher.fetch()
            return fetcher.get_latest_price()
        except Exception:
            return None

    def check_exits(self):
        """Check if any positions should be closed"""
        positions_to_close = []

        for pos in self.positions:
            ticker = pos['ticker']
            current_price = self.get_current_price(ticker)
            
            if current_price is None:
                continue

            entry_price = pos['entry_price']
            stop_loss = pos['stop_loss']
            take_profit = pos['take_profit']
            shares = pos['shares']

            # Calculate unrealized P&L
            if pos['type'] == 'BUY':
                unrealized_pnl = (current_price - entry_price) * shares
                unrealized_pct = ((current_price - entry_price) / entry_price) * 100

                # Check Stop Loss
                if current_price <= stop_loss:
                    positions_to_close.append({
                        'position': pos,
                        'exit_price': stop_loss,
                        'reason': 'STOP_LOSS',
                        'current_price': current_price
                    })
                # Check Take Profit
                elif current_price >= take_profit:
                    positions_to_close.append({
                        'position': pos,
                        'exit_price': take_profit,
                        'reason': 'TAKE_PROFIT',
                        'current_price': current_price
                    })
                # Check Time Exit (10 days max hold)
                elif self._days_held(pos) >= 10:
                    positions_to_close.append({
                        'position': pos,
                        'exit_price': current_price,
                        'reason': 'TIME_EXIT',
                        'current_price': current_price
                    })

            print(f"   {ticker}: ₹{current_price:.2f} | "
                  f"P&L: ₹{unrealized_pnl:+,.0f} ({unrealized_pct:+.1f}%)")

        # Close positions
        for exit_info in positions_to_close:
            self._close_position(
                exit_info['position'],
                exit_info['exit_price'],
                exit_info['reason']
            )

    def _days_held(self, position):
        """Calculate days held"""
        entry_time = datetime.fromisoformat(position['entry_time'])
        return (datetime.now() - entry_time).days

    def _close_position(self, position, exit_price, reason):
        """Close a position"""
        ticker = position['ticker']
        entry_price = position['entry_price']
        shares = position['shares']
        cost = position['cost']

        # Calculate P&L
        if position['type'] == 'BUY':
            pnl = (exit_price - entry_price) * shares
        else:
            pnl = (entry_price - exit_price) * shares

        pnl_pct = (pnl / cost) * 100

        # Update capital
        self.capital += cost + pnl

        # Create closed trade record
        closed_trade = {
            **position,
            'exit_price': exit_price,
            'exit_time': datetime.now().isoformat(),
            'exit_reason': reason,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'days_held': self._days_held(position)
        }

        self.closed_trades.append(closed_trade)

        # Remove from open positions
        self.positions = [p for p in self.positions if p['id'] != position['id']]

        # Log
        self.logger.log_trade(
            ticker=ticker,
            signal=f"CLOSE_{position['type']}",
            price=exit_price,
            shares=shares,
            confidence=0,
            reason=reason,
            stop_loss=position['stop_loss'],
            take_profit=position['take_profit'],
            pnl=pnl,
            capital=self.capital
        )

        # Alert
        emoji = "✅" if pnl >= 0 else "❌"
        print(f"\n{emoji} CLOSED {ticker} — {reason}")
        print(f"   Entry: ₹{entry_price:.2f} → Exit: ₹{exit_price:.2f}")
        print(f"   P&L: ₹{pnl:+,.2f} ({pnl_pct:+.1f}%)")
        print(f"   Capital: ₹{self.capital:,.2f}")

        self.telegram.send_trade_closed(ticker, pnl, pnl_pct, reason)
        self._save_state()

    def open_position(self, ticker, signal_data):
        """Open a new paper position"""
        if len(self.positions) >= MAX_OPEN_POSITIONS:
            print(f"⚠️ Max positions ({MAX_OPEN_POSITIONS}) reached")
            return None

        # Check if already have position in this ticker
        existing = [p for p in self.positions if p['ticker'] == ticker]
        if existing:
            print(f"⚠️ Already have position in {ticker}")
            return None

        price = signal_data['price']
        stop_loss = signal_data['stop_loss']
        take_profit = signal_data['take_profit']

        # Calculate position size
        risk_amount = self.capital * 0.02  # 2% risk
        stop_distance = abs(price - stop_loss)
        
        if stop_distance <= 0:
            stop_distance = price * STOP_LOSS_PCT

        shares = int(risk_amount / stop_distance)
        max_shares = int((self.capital * 0.40) / price)
        shares = min(shares, max_shares)

        if shares <= 0:
            print(f"⚠️ Position size = 0 for {ticker}")
            return None

        cost = price * shares

        if cost > self.capital:
            print(f"⚠️ Insufficient capital for {ticker}")
            return None

        # Create position
        position = {
            'id': len(self.closed_trades) + len(self.positions) + 1,
            'ticker': ticker,
            'type': signal_data['signal'],
            'entry_price': price,
            'shares': shares,
            'cost': cost,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'confidence': signal_data['confidence'],
            'entry_time': datetime.now().isoformat(),
            'filters_passed': signal_data['filters_passed'],
            'reason': signal_data['reason']
        }

        # Deduct from capital
        self.capital -= cost

        self.positions.append(position)

        # Log
        self.logger.log_trade(
            ticker=ticker,
            signal=signal_data['signal'],
            price=price,
            shares=shares,
            confidence=signal_data['confidence'],
            reason=signal_data['reason'],
            stop_loss=stop_loss,
            take_profit=take_profit,
            pnl=0,
            capital=self.capital
        )

        print(f"\n📈 OPENED {signal_data['signal']} — {ticker}")
        print(f"   Entry: ₹{price:.2f} × {shares} shares = ₹{cost:,.2f}")
        print(f"   SL: ₹{stop_loss:.2f} | TP: ₹{take_profit:.2f}")
        print(f"   Capital remaining: ₹{self.capital:,.2f}")

        self.telegram.send_trade_executed(
            ticker, signal_data['signal'], price, shares, stop_loss, take_profit
        )
        
        self._save_state()
        return position

    def scan_and_trade(self, tickers=None):
        """Scan stocks and open positions for signals"""
        if tickers is None:
            tickers = TICKERS

        print(f"\n{'='*60}")
        print(f"📡 PAPER TRADING SCAN — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Capital: ₹{self.capital:,.2f}")
        print(f"   Open positions: {len(self.positions)}/{MAX_OPEN_POSITIONS}")
        print(f"{'='*60}\n")

        # First, check existing positions for exits
        if self.positions:
            print("📊 Checking open positions...")
            self.check_exits()
            print()

        # Skip if max positions reached
        if len(self.positions) >= MAX_OPEN_POSITIONS:
            print(f"⏸️ Max positions reached. Waiting for exits.")
            return []

        # Load model
        if not self.model.is_trained:
            loaded = self.model.load()
            if not loaded:
                print("⚠️ No trained model. Train first with: python main.py --train")
                return []

        signals_found = []

        for ticker in tickers:
            # Skip if already have position
            if any(p['ticker'] == ticker for p in self.positions):
                continue

            try:
                print(f"   Scanning {ticker}...", end=" ")

                # Fetch data
                fetcher = DataFetcher(ticker, LOOKBACK_PERIOD)
                df = fetcher.fetch()
                if df is None or len(df) < 50:
                    print("❌ No data")
                    continue

                # Build features
                fe = FeatureEngineer(df)
                fe.build()

                # Update feature engineer with selected features
                if self.model.selected_features:
                    fe.set_selected_features(self.model.selected_features)

                # Get signal
                strategy = SignalStrategy(self.model, fe, ticker)
                result = strategy.generate_signal()
                result['ticker'] = ticker

                if result['signal'] in ['BUY', 'SELL']:
                    print(f"✅ {result['signal']} @ {result['confidence']:.1f}%")
                    signals_found.append(result)

                    # Open position
                    if len(self.positions) < MAX_OPEN_POSITIONS:
                        self.open_position(ticker, result)
                else:
                    print(f"⏸️ HOLD ({result['filters_passed']}/{result['total_filters']} filters)")

            except Exception as e:
                print(f"❌ Error: {e}")

        # Summary
        self.print_portfolio_status()

        return signals_found

    def print_portfolio_status(self):
        """Print current portfolio status"""
        total_pnl = sum(t['pnl'] for t in self.closed_trades)
        win_trades = [t for t in self.closed_trades if t['pnl'] > 0]
        loss_trades = [t for t in self.closed_trades if t['pnl'] <= 0]
        win_rate = (len(win_trades) / max(len(self.closed_trades), 1)) * 100

        # Calculate unrealized P&L
        unrealized_pnl = 0
        for pos in self.positions:
            current_price = self.get_current_price(pos['ticker'])
            if current_price:
                if pos['type'] == 'BUY':
                    unrealized_pnl += (current_price - pos['entry_price']) * pos['shares']

        total_value = self.capital + sum(p['cost'] for p in self.positions) + unrealized_pnl
        total_return = ((total_value - self.starting_capital) / self.starting_capital) * 100

        print(f"\n{'='*60}")
        print(f"💰 PAPER PORTFOLIO STATUS")
        print(f"{'='*60}")
        print(f"   Starting Capital: ₹{self.starting_capital:,.2f}")
        print(f"   Current Cash:     ₹{self.capital:,.2f}")
        print(f"   Unrealized P&L:   ₹{unrealized_pnl:+,.2f}")
        print(f"   Total Value:      ₹{total_value:,.2f}")
        print(f"   Total Return:     {total_return:+.2f}%")
        print(f"")
        print(f"   Realized P&L:     ₹{total_pnl:+,.2f}")
        print(f"   Closed Trades:    {len(self.closed_trades)}")
        print(f"   Win Rate:         {win_rate:.1f}% ({len(win_trades)}W / {len(loss_trades)}L)")
        print(f"   Open Positions:   {len(self.positions)}")

        if self.positions:
            print(f"\n   Open Positions:")
            for pos in self.positions:
                current = self.get_current_price(pos['ticker']) or pos['entry_price']
                pnl = (current - pos['entry_price']) * pos['shares']
                pnl_pct = ((current - pos['entry_price']) / pos['entry_price']) * 100
                emoji = "📈" if pnl >= 0 else "📉"
                print(f"     {emoji} {pos['ticker']}: {pos['shares']}sh @ ₹{pos['entry_price']:.2f} "
                      f"→ ₹{current:.2f} | P&L: ₹{pnl:+,.0f} ({pnl_pct:+.1f}%)")

        print(f"{'='*60}\n")

    def run_loop(self, interval_seconds=None):
        """Run continuous paper trading loop"""
        if interval_seconds is None:
            interval_seconds = PAPER_SCAN_INTERVAL_SECONDS

        self.is_running = True

        print(f"\n{'='*60}")
        print(f"🚀 PAPER TRADING MODE STARTED")
        print(f"   Interval: {interval_seconds} seconds")
        print(f"   Stocks: {len(TICKERS)}")
        print(f"   Press Ctrl+C to stop")
        print(f"{'='*60}\n")

        self.telegram.send_startup()

        try:
            while self.is_running:
                self.scan_and_trade()

                print(f"⏰ Next scan in {interval_seconds}s...")
                time.sleep(interval_seconds)

        except KeyboardInterrupt:
            print("\n🛑 Paper trading stopped by user")
            self.telegram.send_shutdown()
            self.print_portfolio_status()

    def reset(self):
        """Reset paper trading portfolio"""
        self.capital = INITIAL_CAPITAL
        self.starting_capital = INITIAL_CAPITAL
        self.positions = []
        self.closed_trades = []
        self._save_state()
        print("🔄 Paper portfolio reset to initial state")
