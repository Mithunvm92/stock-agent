import numpy as np
import pandas as pd
from config.settings import (
    INITIAL_CAPITAL, STOP_LOSS_PCT, TAKE_PROFIT_PCT,
    RISK_PER_TRADE, MIN_CONFIDENCE, MIN_ADX_FOR_TRADE,
    MAX_HOLD_BARS_LOSING, MAX_HOLD_BARS_WINNING,
    RSI_BUY_MIN, RSI_BUY_MAX, MIN_ATR_PCT, MAX_ATR_PCT,
    MIN_VOLUME_RATIO, MIN_FILTERS_TO_PASS
)


class Backtester:
    """
    v7 — Backtester with STRICT filters matching SignalStrategy
    """

    def __init__(self, model, feature_engineer):
        self.model = model
        self.fe = feature_engineer

    def run(self):
        print("\n📊 ═══════════════════════════════════")
        print("   BACKTESTING v7 (Strict Filters)")
        print("═══════════════════════════════════════")

        df = self.fe.df.copy()

        features = self.model.selected_features
        if not features:
            features = self.fe.FEATURE_COLUMNS
        features = [f for f in features if f in df.columns]

        if len(features) == 0:
            print("❌ No valid features")
            return self._empty_result()

        # Get filter columns
        has_adx = 'ADX' in df.columns
        has_rsi = 'RSI' in df.columns
        has_atr = 'ATR_Pct' in df.columns
        has_volume = 'Volume_Ratio' in df.columns
        has_macd = 'MACD_Hist' in df.columns
        has_sma = 'Close_to_SMA20' in df.columns

        capital = INITIAL_CAPITAL
        peak_capital = INITIAL_CAPITAL
        position = None
        trades = []

        start_idx = int(len(df) * 0.8)
        end_idx = len(df) - 1
        test_bars = end_idx - start_idx

        print(f"   Period:      last {test_bars} bars")
        print(f"   Features:    {len(features)}")
        print(f"   Min Conf:    {MIN_CONFIDENCE}%")
        print(f"   Min ADX:     {MIN_ADX_FOR_TRADE}")
        print(f"   Min Filters: {MIN_FILTERS_TO_PASS}/7")

        buy_signals = 0
        sell_signals = 0
        skipped = {'conf': 0, 'filters': 0}

        for i in range(start_idx, end_idx):
            current_price = float(df.iloc[i]['Close'])
            next_price = float(df.iloc[i + 1]['Close'])

            # Get indicators for filtering
            adx = float(df.iloc[i]['ADX']) if has_adx else 25
            rsi = float(df.iloc[i]['RSI']) if has_rsi else 50
            atr_pct = float(df.iloc[i]['ATR_Pct']) if has_atr else 2.0
            volume_ratio = float(df.iloc[i]['Volume_Ratio']) if has_volume else 1.0
            macd_hist = float(df.iloc[i]['MACD_Hist']) if has_macd else 0
            sma_dist = float(df.iloc[i]['Close_to_SMA20']) if has_sma else 0

            # ── Check exits ──
            if position is not None:
                bars_held = i - position['open_bar']
                unrealized_pnl = (next_price - position['entry']) * position['shares']

                exit_triggered = False
                exit_reason = ""
                exit_price = next_price

                if next_price <= position['stop_loss']:
                    exit_triggered = True
                    exit_reason = "SL"
                    exit_price = position['stop_loss']
                elif next_price >= position['take_profit']:
                    exit_triggered = True
                    exit_reason = "TP"
                    exit_price = position['take_profit']
                elif bars_held >= MAX_HOLD_BARS_LOSING and unrealized_pnl <= 0:
                    exit_triggered = True
                    exit_reason = "TIME_L"
                elif bars_held >= MAX_HOLD_BARS_WINNING and unrealized_pnl > 0:
                    exit_triggered = True
                    exit_reason = "TIME_W"

                if exit_triggered:
                    pnl = (exit_price - position['entry']) * position['shares']
                    capital += position['cost'] + pnl
                    pnl_pct = (pnl / position['cost']) * 100 if position['cost'] > 0 else 0
                    trades.append({
                        'pnl': pnl, 'type': exit_reason,
                        'entry': position['entry'], 'exit': exit_price,
                        'shares': position['shares'], 'cost': position['cost'],
                        'pnl_pct': pnl_pct, 'bars_held': bars_held,
                    })
                    position = None

                total_value = capital
                if position is not None:
                    total_value += position['cost'] + unrealized_pnl
                peak_capital = max(peak_capital, total_value)

            # ── Try to open position ──
            if position is None:
                X_row = df[features].iloc[[i]]

                try:
                    X_scaled = self.model.scaler.transform(X_row)
                    pred = self.model.model.predict(X_scaled)[0]
                    prob = self.model.model.predict_proba(X_scaled)[0]
                    confidence = max(prob) * 100
                except Exception:
                    continue

                if pred == 1:
                    buy_signals += 1
                else:
                    sell_signals += 1

                # ── STRICT FILTER CHECK (matching SignalStrategy) ──
                if pred == 1:
                    filters_passed = 0

                    # Filter 1: Confidence
                    if confidence >= MIN_CONFIDENCE:
                        filters_passed += 1

                    # Filter 2: RSI in range
                    if RSI_BUY_MIN <= rsi <= RSI_BUY_MAX:
                        filters_passed += 1

                    # Filter 3: ADX
                    if adx >= MIN_ADX_FOR_TRADE:
                        filters_passed += 1

                    # Filter 4: ATR in range
                    if MIN_ATR_PCT <= atr_pct <= MAX_ATR_PCT:
                        filters_passed += 1

                    # Filter 5: Volume
                    if volume_ratio >= MIN_VOLUME_RATIO:
                        filters_passed += 1

                    # Filter 6: MACD
                    if macd_hist > 0:
                        filters_passed += 1

                    # Filter 7: Trend alignment
                    if sma_dist >= -2.0:
                        filters_passed += 1

                    # Check if enough filters passed
                    if filters_passed < MIN_FILTERS_TO_PASS:
                        skipped['filters'] += 1
                        continue

                    # Open position
                    sl = round(current_price * (1 - STOP_LOSS_PCT), 2)
                    tp = round(current_price * (1 + TAKE_PROFIT_PCT), 2)

                    shares = self._calc_shares(capital, current_price, sl)

                    if shares > 0:
                        cost = current_price * shares
                        capital -= cost

                        position = {
                            'type': 'BUY',
                            'entry': current_price,
                            'shares': shares,
                            'cost': cost,
                            'stop_loss': sl,
                            'take_profit': tp,
                            'open_bar': i,
                            'filters_passed': filters_passed
                        }

        # Close remaining
        if position is not None:
            final_price = float(df['Close'].iloc[-1])
            pnl = (final_price - position['entry']) * position['shares']
            capital += position['cost'] + pnl
            pnl_pct = (pnl / position['cost']) * 100 if position['cost'] > 0 else 0
            trades.append({
                'pnl': pnl, 'type': 'FINAL',
                'entry': position['entry'], 'exit': final_price,
                'shares': position['shares'], 'cost': position['cost'],
                'pnl_pct': pnl_pct, 'bars_held': end_idx - position['open_bar'],
            })

        # Print results
        self._print_results(
            trades, capital, peak_capital, test_bars,
            buy_signals, sell_signals, skipped
        )

        return self._calc_metrics(trades, capital, peak_capital)

    def _calc_shares(self, capital, price, stop_loss):
        if price <= 0:
            return 0
        risk_amount = capital * RISK_PER_TRADE
        stop_distance = abs(price - stop_loss)
        if stop_distance <= 0:
            stop_distance = price * 0.02
        shares_by_risk = int(risk_amount / stop_distance)
        shares_by_capital = int(capital / price)

        shares = min(
            shares_by_risk,
            max(shares_by_capital, 1)
        )

        # ALWAYS ALLOW
        # AT LEAST 1 SHARE
        if shares <= 0 and capital >= price:

            shares = 1
        return max(shares, 0)

    def _print_results(self, trades, capital, peak_capital, test_bars,
                       buy_signals, sell_signals, skipped):
        total_trades = len(trades)
        wins = [t for t in trades if t['pnl'] > 0]
        losses = [t for t in trades if t['pnl'] <= 0]
        total_pnl = sum(t['pnl'] for t in trades)

        print(f"\n   ═══ SIGNAL BREAKDOWN ═══")
        print(f"   BUY signals:       {buy_signals}")
        print(f"   SELL signals:      {sell_signals}")
        print(f"   Skipped (filters): {skipped['filters']}")
        print(f"   Trades executed:   {total_trades}")

        if trades:
            print(f"\n   ═══ TRADE LOG ═══")
            for j, t in enumerate(trades[:15]):
                emoji = "✅" if t['pnl'] > 0 else "❌"
                print(f"   {emoji} #{j+1:2d} {t['type']:6s} | "
                      f"₹{t['entry']:.0f}→₹{t['exit']:.0f} | "
                      f"{t['shares']}sh | "
                      f"₹{t['pnl']:+,.0f} ({t['pnl_pct']:+.1f}%) | "
                      f"{t.get('bars_held', 0)}bars")
            if len(trades) > 15:
                print(f"   ... and {len(trades) - 15} more")

        win_rate = (len(wins) / max(total_trades, 1)) * 100
        roi = (total_pnl / INITIAL_CAPITAL) * 100

        avg_win = np.mean([t['pnl'] for t in wins]) if wins else 0
        avg_loss = np.mean([abs(t['pnl']) for t in losses]) if losses else 0

        gross_profit = sum(t['pnl'] for t in wins) if wins else 0
        gross_loss = abs(sum(t['pnl'] for t in losses)) if losses else 0.01
        profit_factor = gross_profit / max(gross_loss, 0.01)

        max_dd = ((peak_capital - min(capital, peak_capital)) / max(peak_capital, 1)) * 100
        expectancy = total_pnl / max(total_trades, 1)

        tp = sum(1 for t in trades if t['type'] == 'TP')
        sl = sum(1 for t in trades if t['type'] == 'SL')
        time_l = sum(1 for t in trades if t['type'] == 'TIME_L')
        time_w = sum(1 for t in trades if t['type'] == 'TIME_W')

        max_consec = 0
        streak = 0
        for t in trades:
            if t['pnl'] <= 0:
                streak += 1
                max_consec = max(max_consec, streak)
            else:
                streak = 0

        print(f"\n   ═══ PERFORMANCE ═══")
        print(f"   Initial Capital:  ₹{INITIAL_CAPITAL:,.0f}")
        print(f"   Final Capital:    ₹{capital:,.0f}")
        print(f"   Total P&L:        ₹{total_pnl:+,.0f}")
        print(f"   ROI:              {roi:+.2f}%")
        print(f"")
        print(f"   Total Trades:     {total_trades}")
        print(f"   Win Rate:         {win_rate:.1f}% ({len(wins)}W / {len(losses)}L)")
        print(f"   Avg Win:          ₹{avg_win:+,.0f}")
        print(f"   Avg Loss:         ₹{avg_loss:,.0f}")
        print(f"   Profit Factor:    {profit_factor:.2f}")
        print(f"   Expectancy:       ₹{expectancy:+,.0f}/trade")
        print(f"   Max Drawdown:     {max_dd:.2f}%")
        print(f"   Max Consec Loss:  {max_consec}")
        print(f"")
        print(f"   Exit Breakdown:")
        print(f"     Take Profit:    {tp}")
        print(f"     Stop Loss:      {sl}")
        print(f"     Time (losing):  {time_l}")
        print(f"     Time (winning): {time_w}")

        print(f"\n   ═══ ASSESSMENT ═══")
        if total_trades == 0:
            print(f"   ⚠️ NO TRADES — Filters too strict")
        elif profit_factor >= 1.5 and win_rate >= 50:
            print(f"   ✅ EXCELLENT — Ready for paper trading!")
        elif profit_factor >= 1.2 and win_rate >= 45:
            print(f"   ✅ GOOD — Profitable with discipline")
        elif profit_factor >= 1.0:
            print(f"   ⚠️ MARGINAL — Small edge")
        else:
            print(f"   ❌ NEEDS WORK")

        if total_trades > 0 and test_bars > 0:
            trades_per_month = (total_trades / test_bars) * 20
            monthly_pnl = expectancy * trades_per_month
            annual_roi = (monthly_pnl * 12 / INITIAL_CAPITAL) * 100
            print(f"\n   📈 PROJECTION:")
            print(f"      Trades/month:   ~{trades_per_month:.1f}")
            print(f"      Monthly P&L:    ₹{monthly_pnl:+,.0f}")
            print(f"      Annual ROI:     {annual_roi:+.1f}%")

        print(f"═══════════════════════════════════════\n")

    def _calc_metrics(self, trades, capital, peak_capital):
        total_trades = len(trades)
        wins = [t for t in trades if t['pnl'] > 0]
        losses = [t for t in trades if t['pnl'] <= 0]
        total_pnl = sum(t['pnl'] for t in trades)
        win_rate = (len(wins) / max(total_trades, 1)) * 100
        roi = (total_pnl / INITIAL_CAPITAL) * 100
        gross_profit = sum(t['pnl'] for t in wins) if wins else 0
        gross_loss = abs(sum(t['pnl'] for t in losses)) if losses else 0.01
        profit_factor = gross_profit / max(gross_loss, 0.01)
        max_dd = ((peak_capital - min(capital, peak_capital)) / max(peak_capital, 1)) * 100
        expectancy = total_pnl / max(total_trades, 1)

        return {
            'total_pnl': total_pnl, 'roi': roi,
            'total_trades': total_trades, 'win_rate': win_rate,
            'profit_factor': profit_factor, 'max_drawdown': max_dd,
            'expectancy': expectancy, 'final_capital': capital
        }

    def _empty_result(self):
        return {
            'total_pnl': 0, 'roi': 0, 'total_trades': 0,
            'win_rate': 0, 'profit_factor': 0,
            'max_drawdown': 0, 'expectancy': 0,
            'final_capital': INITIAL_CAPITAL
        }
