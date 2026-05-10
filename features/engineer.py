import pandas as pd
import numpy as np
import ta
from config.settings import TARGET_THRESHOLD_PCT, TARGET_LOOKAHEAD_DAYS


class FeatureEngineer:
    """
    v3 — Key improvements:
    1. Only compute proven features (removed noise)
    2. Smart target with 3-day lookahead
    3. Ratio-based features (normalize across price levels)
    4. Auto feature selection support
    """

    # All candidate features
    ALL_FEATURES = [
        # Momentum (5)
        'RSI', 'RSI_Slope',
        'Stoch_K', 'Stoch_D',
        'CCI',
        # Trend (7)
        'MACD_Hist', 'MACD_Hist_Slope',
        'Close_to_SMA10', 'Close_to_SMA20', 'Close_to_SMA50',
        'EMA_Spread',
        'ADX',
        # Volatility (4)
        'BB_Width', 'BB_Pct',
        'ATR_Pct',
        'Volatility_Ratio',
        # Volume (3)
        'Volume_Ratio',
        'Volume_Trend',
        'OBV_Slope_Norm',
        # Price Action (5)
        'Return_1d', 'Return_3d', 'Return_5d',
        'High_Low_Pct',
        'Body_Pct',
        # Cross signals (4)
        'SMA_Cross_10_20',
        'SMA_Cross_20_50',
        'MACD_Cross',
        'RSI_Above_50',
        # Lag (3)
        'RSI_Lag1',
        'MACD_Hist_Lag1',
        'Return_1d_Lag1',
    ]

    TARGET_COL = 'Target'

    def __init__(self, df):
        self.df = df.copy()
        self.latest_indicators = {}
        # Will be set after build — either all or selected
        self.FEATURE_COLUMNS = self.ALL_FEATURES.copy()

    def build(self):
        """Build all features"""
        df = self.df

        close = pd.to_numeric(df['Close'].squeeze(), errors='coerce')
        high = pd.to_numeric(df['High'].squeeze(), errors='coerce')
        low = pd.to_numeric(df['Low'].squeeze(), errors='coerce')
        opn = pd.to_numeric(df['Open'].squeeze(), errors='coerce')
        volume = pd.to_numeric(df['Volume'].squeeze(), errors='coerce')

        # ═══ MOMENTUM ═══
        rsi = ta.momentum.RSIIndicator(close, window=14).rsi()
        df['RSI'] = rsi
        df['RSI_Slope'] = rsi.diff(5)  # RSI direction over 5 days

        stoch = ta.momentum.StochasticOscillator(high, low, close)
        df['Stoch_K'] = stoch.stoch()
        df['Stoch_D'] = stoch.stoch_signal()

        df['CCI'] = ta.trend.CCIIndicator(high, low, close).cci()

        # ═══ TREND (all ratio-based to normalize) ═══
        macd_ind = ta.trend.MACD(close)
        macd_hist = macd_ind.macd_diff()
        df['MACD_Hist'] = macd_hist
        df['MACD_Hist_Slope'] = macd_hist.diff(3)

        sma10 = close.rolling(window=10).mean()
        sma20 = close.rolling(window=20).mean()
        sma50 = close.rolling(window=50).mean()
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()

        # Distance to SMA as percentage (not absolute price)
        df['Close_to_SMA10'] = ((close - sma10) / sma10) * 100
        df['Close_to_SMA20'] = ((close - sma20) / sma20) * 100
        df['Close_to_SMA50'] = ((close - sma50) / sma50) * 100

        # EMA spread (short vs long term momentum)
        df['EMA_Spread'] = ((ema12 - ema26) / ema26) * 100

        df['ADX'] = ta.trend.ADXIndicator(high, low, close).adx()

        # ═══ VOLATILITY ═══
        bb = ta.volatility.BollingerBands(close, window=20)
        bb_upper = bb.bollinger_hband()
        bb_lower = bb.bollinger_lband()
        df['BB_Width'] = ((bb_upper - bb_lower) / close) * 100
        df['BB_Pct'] = bb.bollinger_pband()

        atr = ta.volatility.AverageTrueRange(high, low, close, window=14).average_true_range()
        df['ATR_Pct'] = (atr / close) * 100

        # Volatility ratio: current vs historical
        vol_short = close.pct_change().rolling(5).std()
        vol_long = close.pct_change().rolling(20).std()
        df['Volatility_Ratio'] = (vol_short / vol_long.replace(0, np.nan)).fillna(1.0)

        # ═══ VOLUME ═══
        vol_sma = volume.rolling(window=20).mean().replace(0, np.nan)
        df['Volume_Ratio'] = (volume / vol_sma).fillna(1.0)

        vol_short_avg = volume.rolling(5).mean()
        vol_long_avg = volume.rolling(20).mean().replace(0, np.nan)
        df['Volume_Trend'] = (vol_short_avg / vol_long_avg).fillna(1.0)

        # OBV slope normalized by price
        obv = ta.volume.on_balance_volume(close, volume)
        df['OBV_Slope_Norm'] = obv.diff(5) / (close * volume.rolling(5).mean()).replace(0, np.nan)
        df['OBV_Slope_Norm'] = df['OBV_Slope_Norm'].fillna(0)

        # ═══ PRICE ACTION ═══
        df['Return_1d'] = close.pct_change(1) * 100
        df['Return_3d'] = close.pct_change(3) * 100
        df['Return_5d'] = close.pct_change(5) * 100
        df['High_Low_Pct'] = ((high - low) / close) * 100

        # Candle body size as % of range
        body = abs(close - opn)
        hl_range = (high - low).replace(0, np.nan)
        df['Body_Pct'] = (body / hl_range).fillna(0.5)

        # ═══ CROSS SIGNALS ═══
        df['SMA_Cross_10_20'] = (sma10 > sma20).astype(float)
        df['SMA_Cross_20_50'] = (sma20 > sma50).astype(float)
        df['MACD_Cross'] = (macd_ind.macd() > macd_ind.macd_signal()).astype(float)
        df['RSI_Above_50'] = (rsi > 50).astype(float)

        # ═══ LAG FEATURES ═══
        df['RSI_Lag1'] = rsi.shift(1)
        df['MACD_Hist_Lag1'] = macd_hist.shift(1)
        df['Return_1d_Lag1'] = df['Return_1d'].shift(1)

        # ═══ TARGET ═══
        future_max = close.rolling(window=TARGET_LOOKAHEAD_DAYS).max().shift(-TARGET_LOOKAHEAD_DAYS)
        future_return = (future_max - close) / close
        df[self.TARGET_COL] = np.where(future_return >= TARGET_THRESHOLD_PCT, 1, 0)

        # Drop NaN
        df = df.dropna()
        df = df.reset_index(drop=True)

        # Verify all features exist
        available = [f for f in self.ALL_FEATURES if f in df.columns]
        missing = [f for f in self.ALL_FEATURES if f not in df.columns]
        if missing:
            print(f"   ⚠️ Missing features (skipped): {missing}")
        self.FEATURE_COLUMNS = available

        # Store latest indicators
        self._store_latest_indicators(df)

        self.df = df

        buy_pct = (df[self.TARGET_COL].sum() / len(df)) * 100
        print(f"🔧 Built {len(self.FEATURE_COLUMNS)} features | "
              f"{len(df)} samples | "
              f"BUY={buy_pct:.1f}% SELL={100-buy_pct:.1f}%")
        return df

    def _store_latest_indicators(self, df):
        """Store latest indicators as Python floats"""
        if len(df) == 0:
            return
        latest = df.iloc[-1]
        keys = [
            'RSI', 'MACD_Hist', 'Close_to_SMA20', 'Close_to_SMA50',
            'ATR_Pct', 'ADX', 'BB_Pct', 'BB_Width', 'Volume_Ratio',
            'Return_1d', 'Close', 'Stoch_K', 'CCI', 'EMA_Spread',
            'Volatility_Ratio', 'Volume_Trend'
        ]
        self.latest_indicators = {}
        for key in keys:
            try:
                val = latest.get(key, 0)
                if isinstance(val, pd.Series):
                    val = val.iloc[0]
                self.latest_indicators[key] = round(float(val), 4)
            except Exception:
                self.latest_indicators[key] = 0.0

    def set_selected_features(self, feature_list):
        """Set the features to use (called by model after selection)"""
        self.FEATURE_COLUMNS = feature_list

    def get_X_y(self):
        X = self.df[self.FEATURE_COLUMNS].copy()
        y = self.df[self.TARGET_COL].copy()
        return X, y

    def get_latest_features(self):
        return self.df[self.FEATURE_COLUMNS].iloc[[-1]]

    def get_indicator_summary(self):
        """Human-readable summary"""
        ind = self.latest_indicators
        if not ind:
            return "No indicators computed."

        rsi = ind.get('RSI', 50)
        rsi_status = 'OVERBOUGHT' if rsi > 70 else 'OVERSOLD' if rsi < 30 else 'NEUTRAL'
        macd_hist = ind.get('MACD_Hist', 0)
        macd_status = 'BULLISH' if macd_hist > 0 else 'BEARISH'
        adx = ind.get('ADX', 0)
        adx_status = 'STRONG TREND' if adx > 25 else 'WEAK/NO TREND'
        vol = ind.get('Volume_Ratio', 1)
        vol_status = 'HIGH VOLUME' if vol > 1.5 else 'NORMAL'

        summary = (
            f"\nLIVE COMPUTED INDICATORS:\n"
            f"  Price:           Rs.{ind.get('Close', 0):.2f}\n"
            f"  1-Day Return:    {ind.get('Return_1d', 0):.2f}%\n"
            f"  RSI(14):         {rsi:.1f} ({rsi_status})\n"
            f"  Stoch K:         {ind.get('Stoch_K', 0):.1f}\n"
            f"  CCI:             {ind.get('CCI', 0):.1f}\n"
            f"  MACD Hist:       {macd_hist:.4f} ({macd_status})\n"
            f"  EMA Spread:      {ind.get('EMA_Spread', 0):.3f}%\n"
            f"  ADX:             {adx:.1f} ({adx_status})\n"
            f"  Dist to SMA20:   {ind.get('Close_to_SMA20', 0):.2f}%\n"
            f"  Dist to SMA50:   {ind.get('Close_to_SMA50', 0):.2f}%\n"
            f"  ATR%:            {ind.get('ATR_Pct', 0):.2f}%\n"
            f"  BB Width:        {ind.get('BB_Width', 0):.2f}%\n"
            f"  BB Position:     {ind.get('BB_Pct', 0):.3f}\n"
            f"  Vol Ratio:       {ind.get('Volatility_Ratio', 0):.2f}\n"
            f"  Volume Ratio:    {vol:.2f}x ({vol_status})\n"
        )
        return summary
