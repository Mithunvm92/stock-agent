import json
import os
from datetime import datetime
from data.fetcher import DataFetcher
from features.engineer import FeatureEngineer
from models.ml_model import MLModel
from config.settings import PRIMARY_TICKER, LOOKBACK_PERIOD, RETRAIN_INTERVAL_HOURS


class SelfTrainer:
    """
    v3 Self-trainer — passes feature_engineer to model
    so feature selection can update the engineer
    """

    def __init__(self, ticker=None):
        self.ticker = ticker or PRIMARY_TICKER
        self.lookback = LOOKBACK_PERIOD
        self.model = MLModel()
        self.last_trained = None
        self.train_count = 0
        self.accuracy_history = []
        self.log_path = "db/training_history.json"

    def needs_retrain(self):
        if self.last_trained is None:
            return True
        hours = (datetime.now() - self.last_trained).total_seconds() / 3600
        return hours >= RETRAIN_INTERVAL_HOURS

    def run_training_cycle(self):
        """Full training pipeline with feature selection"""
        print("\n🔄 ═══════════════════════════════════")
        print(f"   SELF-TRAINING #{self.train_count + 1}")
        print(f"   Ticker: {self.ticker}")
        print(f"   Time:   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("═══════════════════════════════════════")

        # Step 1: Fetch
        fetcher = DataFetcher(self.ticker, self.lookback)
        df = fetcher.fetch()
        if df is None:
            print("❌ Training failed: No data")
            return None

        # Step 2: Features
        fe = FeatureEngineer(df)
        fe.build()
        X, y = fe.get_X_y()

        if len(X) < 100:
            print(f"❌ Not enough data ({len(X)} < 100)")
            return None

        # Step 3: Train WITH feature engineer reference
        # This allows the model to update fe.FEATURE_COLUMNS after selection
        accuracy = self.model.train(X, y, feature_engineer=fe)

        # Step 4: Record
        self.last_trained = datetime.now()
        self.train_count += 1
        self.accuracy_history.append(accuracy)
        self._save_log(accuracy)

        avg_acc = sum(self.accuracy_history) / len(self.accuracy_history)
        print(f"\n✅ Training #{self.train_count} done")
        print(f"   Accuracy: {accuracy:.1f}% | Avg: {avg_acc:.1f}%")
        print(f"   Features used: {len(self.model.selected_features)}")

        return accuracy, self.model, fe

    def _save_log(self, accuracy):
        os.makedirs("db", exist_ok=True)
        history = []
        if os.path.exists(self.log_path):
            try:
                with open(self.log_path, 'r') as f:
                    history = json.load(f)
            except Exception:
                history = []

        history.append({
            'timestamp': datetime.now().isoformat(),
            'ticker': self.ticker,
            'accuracy': round(accuracy, 2),
            'features_used': len(self.model.selected_features),
            'train_count': self.train_count
        })

        with open(self.log_path, 'w') as f:
            json.dump(history, f, indent=2)

    def get_model(self):
        return self.model
