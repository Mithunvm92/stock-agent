import requests
from datetime import datetime
from config.settings import (
    MIN_CONFIDENCE, USE_LLM_VALIDATION,
    LLM_API_URL, LLM_MODEL,
    MIN_ADX_FOR_TRADE,
    STOP_LOSS_PCT, TAKE_PROFIT_PCT
)

# Try to import fundamental settings, use defaults if not available
try:
    from config.settings import USE_FUNDAMENTAL_FILTER
except ImportError:
    USE_FUNDAMENTAL_FILTER = False


class SignalStrategy:
    """
    Signal Strategy with:
    1. ML Prediction
    2. Technical Filters (7 checks)
    3. Fundamental Filter (optional)
    """

    def __init__(self, model, feature_engineer, ticker="RELIANCE.NS"):
        self.model = model
        self.fe = feature_engineer
        self.ticker = ticker

    def generate_signal(self):
        """Generate signal with all filters"""

        # Get latest features
        if self.model.selected_features:
            available = [f for f in self.model.selected_features
                        if f in self.fe.df.columns]
            if available:
                latest_features = self.fe.df[available].iloc[[-1]]
            else:
                latest_features = self.fe.get_latest_features()
        else:
            latest_features = self.fe.get_latest_features()

        signal, confidence, prob = self.model.predict(latest_features)

        # Get indicators
        ind = self.fe.latest_indicators
        current_price = ind.get('Close', 0)
        rsi = ind.get('RSI', 50)
        macd_hist = ind.get('MACD_Hist', 0)
        adx = ind.get('ADX', 0)
        volume_ratio = ind.get('Volume_Ratio', 1)
        atr_pct = ind.get('ATR_Pct', 0)
        close_to_sma20 = ind.get('Close_to_SMA20', 0)

        print(f"\n📡 ═══════════════════════════════════")
        print(f"   SIGNAL ANALYSIS — {self.ticker}")
        print(f"═══════════════════════════════════════")
        print(f"   Price:        ₹{current_price:.2f}")
        print(f"   RSI:          {rsi:.1f}")
        print(f"   MACD Hist:    {macd_hist:.4f}")
        print(f"   ADX:          {adx:.1f}")
        print(f"   ATR%:         {atr_pct:.2f}%")
        print(f"   Volume Ratio: {volume_ratio:.2f}x")
        print(f"   SMA20 Dist:   {close_to_sma20:.2f}%")
        print(f"   ML Signal:    {signal}")
        print(f"   ML Conf:      {confidence:.1f}%")

        # ══════════════════════════════════════════
        # TECHNICAL FILTERS
        # ══════════════════════════════════════════

        filters = {}
        
        # Filter 1: Confidence
        filters['confidence'] = confidence >= MIN_CONFIDENCE
        
        # Filter 2: RSI in range (35-65 for BUY)
        if signal == "BUY":
            filters['rsi'] = 35 <= rsi <= 65
        else:
            filters['rsi'] = True
        
        # Filter 3: ADX (trend strength)
        filters['adx'] = adx >= MIN_ADX_FOR_TRADE
        
        # Filter 4: ATR in range (1-4%)
        filters['atr'] = 1.0 <= atr_pct <= 4.0
        
        # Filter 5: Volume
        filters['volume'] = volume_ratio >= 0.7
        
        # Filter 6: MACD
        if signal == "BUY":
            filters['macd'] = macd_hist > 0
        else:
            filters['macd'] = True
        
        # Filter 7: Trend alignment
        if signal == "BUY":
            filters['trend'] = close_to_sma20 >= -2.0
        else:
            filters['trend'] = True

        passed = sum(filters.values())
        total = len(filters)

        # Need 6/7 filters to pass
        min_filters = 6
        
        final_signal = signal
        reason = f"ML + {passed}/{total} filters"

        if passed < min_filters:
            final_signal = "HOLD"
            failed = [k for k, v in filters.items() if not v]
            reason = f"Only {passed}/{total} filters. Failed: {', '.join(failed)}"

        # ══════════════════════════════════════════
        # FUNDAMENTAL FILTER (Optional)
        # ══════════════════════════════════════════
        
        fundamental_passed = True
        fundamental_report = None

        if USE_FUNDAMENTAL_FILTER and final_signal != "HOLD":
            try:
                from fundamentals.balance_sheet import FundamentalAnalyzer
                analyzer = FundamentalAnalyzer(self.ticker)
                fundamental_report = analyzer.analyze()

                print(f"   ─────────────────────────────────")
                if fundamental_report['is_tradeable']:
                    print(f"   📊 Fundamentals: ✅ Grade {fundamental_report['grade']} ({fundamental_report['score']}/10)")
                else:
                    print(f"   📊 Fundamentals: ❌ Grade {fundamental_report['grade']} ({fundamental_report['score']}/10)")
                    final_signal = "HOLD"
                    reason = f"Failed fundamentals (Grade {fundamental_report['grade']})"
                    fundamental_passed = False

            except Exception as e:
                print(f"   📊 Fundamentals: ⚠️ Could not check ({e})")

        # Calculate SL/TP
        if final_signal == "BUY":
            stop_loss = round(current_price * (1 - STOP_LOSS_PCT), 2)
            take_profit = round(current_price * (1 + TAKE_PROFIT_PCT), 2)
        elif final_signal == "SELL":
            stop_loss = round(current_price * (1 + STOP_LOSS_PCT), 2)
            take_profit = round(current_price * (1 - TAKE_PROFIT_PCT), 2)
        else:
            stop_loss = 0
            take_profit = 0

        risk_reward = round(TAKE_PROFIT_PCT / STOP_LOSS_PCT, 2) if STOP_LOSS_PCT > 0 else 0

        # Print results
        print(f"   ─────────────────────────────────")
        print(f"   FILTERS ({passed}/{total}):")
        for fname, fpassed in filters.items():
            icon = "✅" if fpassed else "❌"
            print(f"     {icon} {fname}")
        print(f"   ─────────────────────────────────")

        if final_signal == "HOLD":
            print(f"   ⏸️  FINAL:      HOLD")
            print(f"   📝 Reason:     {reason}")
        else:
            print(f"   ✅ FINAL:      {final_signal}")
            print(f"   📝 Reason:     {reason}")
            print(f"   🛑 Stop Loss:  ₹{stop_loss}")
            print(f"   🎯 Target:     ₹{take_profit}")
            print(f"   ⚖️  R:R:        1:{risk_reward}")

        print(f"═══════════════════════════════════════\n")

        result = {
            'signal': final_signal,
            'ml_signal': signal,
            'confidence': confidence,
            'price': current_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'risk_reward': risk_reward,
            'rsi': rsi,
            'adx': adx,
            'atr_pct': atr_pct,
            'volume_ratio': volume_ratio,
            'reason': reason,
            'filters_passed': passed,
            'total_filters': total,
            'filter_details': filters,
            'fundamental_passed': fundamental_passed,
            'fundamental_report': fundamental_report,
            'indicators': ind,
            'timestamp': datetime.now().isoformat(),
            'probabilities': {
                'sell_prob': float(prob[0]),
                'buy_prob': float(prob[1])
            }
        }

        return result
