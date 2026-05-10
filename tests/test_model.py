"""Run: python main.py --test"""

import sys
import pandas as pd
from data.fetcher import DataFetcher
from features.engineer import FeatureEngineer
from models.ml_model import MLModel


def test_pipeline():
    print("🧪 Testing pipeline v3...\n")

    # ─── Test 1: Data ───
    print("--- Test 1: Data Fetch ---")
    tickers = ["RELIANCE.NS", "TCS.NS", "AAPL", "MSFT"]
    df = None
    working_ticker = None

    for ticker in tickers:
        print(f"   Trying {ticker}...", end=" ")
        try:
            fetcher = DataFetcher(ticker, "2y")
            result = fetcher.fetch()
            if result is not None and len(result) > 100:
                df = result
                working_ticker = ticker
                print(f"✅ ({len(df)} rows)")
                break
            else:
                print("❌")
        except Exception as e:
            print(f"❌ {e}")

    if df is None:
        print("❌ FATAL: No data")
        sys.exit(1)
    print(f"✅ Test 1 PASSED\n")

    # ─── Test 2: Features ───
    print("--- Test 2: Features ---")
    fe = FeatureEngineer(df)
    fe.build()
    X, y = fe.get_X_y()
    buy_count = int(sum(y == 1))
    sell_count = int(sum(y == 0))
    print(f"   Samples: {len(X)} | BUY={buy_count} SELL={sell_count}")
    assert len(X) > 100, f"❌ Too few: {len(X)}"
    print(f"✅ Test 2 PASSED\n")

    # ─── Test 3: Train with Feature Selection ───
    print("--- Test 3: Model Training ---")
    model = MLModel()
    acc = model.train(X, y, feature_engineer=fe)
    print(f"   Selected features: {len(model.selected_features)}")
    print(f"   Accuracy: {acc:.1f}%")
    assert acc > 30, f"❌ Acc too low: {acc}"
    print(f"✅ Test 3 PASSED\n")

    # ─── Test 4: Predict ───
    print("--- Test 4: Prediction ---")
    # Use selected features
    if model.selected_features:
        latest = fe.df[model.selected_features].iloc[[-1]]
    else:
        latest = fe.get_latest_features()
    signal, conf, prob = model.predict(latest)
    print(f"   Signal: {signal} @ {conf:.1f}%")
    assert signal in ["BUY", "SELL"]
    print(f"✅ Test 4 PASSED\n")

    # ─── Test 5: Indicators ───
    print("--- Test 5: Indicators ---")
    summary = fe.get_indicator_summary()
    assert "RSI" in summary
    print(summary)
    print(f"✅ Test 5 PASSED\n")

    # ─── Test 6: Save/Load ───
    print("--- Test 6: Save/Load ---")
    model.save()
    model2 = MLModel()
    loaded = model2.load()
    assert loaded
    if model2.selected_features:
        latest2 = fe.df[model2.selected_features].iloc[[-1]]
    else:
        latest2 = fe.get_latest_features()
    s2, c2, _ = model2.predict(latest2)
    assert s2 == signal
    print(f"   Match: {s2} == {signal} ✅")
    print(f"✅ Test 6 PASSED\n")

    # ─── Test 7: Risk Manager ───
    print("--- Test 7: Risk Manager ---")
    from utils.risk_manager import RiskManager
    rm = RiskManager()
    can, status = rm.can_trade()
    assert can == True
    price = float(fe.latest_indicators.get('Close', 100))
    shares = rm.calculate_position_size(price)
    print(f"   Can trade: {can} | Shares: {shares}")
    print(f"✅ Test 7 PASSED\n")

    print("=" * 50)
    print(f"🎉 ALL TESTS PASSED!")
    print(f"   Ticker:   {working_ticker}")
    print(f"   Accuracy: {acc:.1f}%")
    print(f"   Signal:   {signal} @ {conf:.1f}%")
    print(f"   Features: {len(model.selected_features)} selected")
    print("=" * 50)

    return working_ticker


if __name__ == "__main__":
    test_pipeline()
