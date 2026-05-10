import time
from datetime import datetime

from data.fetcher import DataFetcher
from features.engineer import FeatureEngineer
from strategies.signal_strategy import SignalStrategy
from training.trainer import SelfTrainer
from backtesting.backtester import Backtester
from utils.risk_manager import RiskManager
from db.trade_log import TradeLogger

from utils.metrics import (
    start_metrics_server,
    update_metrics
)

from config.settings import PRIMARY_TICKER


# =====================================
# START METRICS ONLY ONCE
# =====================================
METRICS_STARTED = False


class TradingAgent:
    """
    Main Trading Agent
    """

    def __init__(
        self,
        ticker=None,
        enable_metrics=False
    ):

        self.ticker = ticker or PRIMARY_TICKER

        self.trainer = SelfTrainer(self.ticker)

        self.risk_mgr = RiskManager()

        self.logger = TradeLogger()

        self.model = None

        self.feature_engineer = None

        self.initialized = False

        # START PROMETHEUS ONLY
        # FOR MAIN LIVE BOT
        if enable_metrics:

            try:

                print(
                    "📊 Starting Prometheus "
                    "metrics server on port 8000..."
                )

                start_metrics_server(port=8000)

            except OSError:

                print(
                    "⚠️ Metrics server already running"
                )

    # =====================================
    # INITIALIZE
    # =====================================
    def initialize(self):

        print("\n🚀 ═══════════════════════════════════")

        print("      STOCK TRADING AGENT")

        print(f"      Ticker: {self.ticker}")

        print(f"      Time: {datetime.now()}")

        print("═══════════════════════════════════════\n")

        result = self.trainer.run_training_cycle()

        if result is None:

            print("❌ Initialization failed")

            return False

        accuracy, self.model, self.feature_engineer = result

        print(
            f"✅ Training Accuracy: "
            f"{accuracy:.2f}%"
        )

        # =====================================
        # BACKTEST
        # =====================================
        bt = Backtester(

            self.model,

            self.feature_engineer
        )

        bt_result = bt.run()

        if bt_result:

            print(

                f"📊 Backtest Win Rate: "

                f"{bt_result.get('win_rate', 0):.2f}%"
            )

        self.initialized = True

        print("✅ Agent ready!\n")

        return True

    # =====================================
    # GET SIGNAL
    # =====================================
    def get_signal(self):

        if not self.initialized:

            ok = self.initialize()

            if not ok:

                return None

        # =====================================
        # RETRAIN IF NEEDED
        # =====================================
        if self.trainer.needs_retrain():

            print("🔄 Retraining model...")

            result = self.trainer.run_training_cycle()

            if result:

                _, self.model, self.feature_engineer = result

        # =====================================
        # FETCH DATA
        # =====================================
        fetcher = DataFetcher(self.ticker)

        data = fetcher.fetch()

        if data is None or len(data) < 50:

            print("❌ Not enough market data")

            return None

        # =====================================
        # FEATURE ENGINEERING
        # =====================================
        self.feature_engineer = FeatureEngineer(data)

        self.feature_engineer.build()

        latest = (
            self.feature_engineer
            .get_latest_features()
        )

        # =====================================
        # MODEL PREDICTION
        # =====================================
        prediction = self.model.predict(latest)[0]

        probability = 0.5

        try:

            proba = self.model.predict_proba(latest)

            probability = max(proba[0])

        except Exception:

            pass

        # =====================================
        # SIGNAL STRATEGY
        # =====================================
        strategy = SignalStrategy(

            self.model,

            self.feature_engineer
        )

        signal = strategy.generate_signal()

        result = {

            "ticker": self.ticker,

            "signal": signal,

            "confidence": probability,

            "price": float(
                data['Close'].iloc[-1]
            ),

            "timestamp": str(datetime.now())
        }

        return result

    # =====================================
    # EXECUTE ONE CYCLE
    # =====================================
    def execute_cycle(self):

        result = self.get_signal()

        if result is None:

            return

        signal = result['signal']

        price = result['price']

        confidence = result['confidence']

        print("\n═══════════════════════════════════════")

        print(f"📡 SIGNAL: {signal}")

        print(f"💰 PRICE: ₹{price:.2f}")

        print(
            f"🧠 CONFIDENCE: "
            f"{confidence:.2f}"
        )

        print("═══════════════════════════════════════\n")

        # =====================================
        # CHECK EXITS FIRST
        # =====================================
        self.risk_mgr.check_exits(price)

        # UPDATE METRICS AFTER EXIT CHECK
        update_metrics(

            self.risk_mgr,

            self.model,

            result
        )

        # =====================================
        # CHECK EXISTING POSITIONS
        # =====================================
        for pos in self.risk_mgr.open_positions:

            if (

                pos['ticker'] == self.ticker and

                pos['signal'] == signal
            ):

                print(
                    "⚠️ Existing position "
                    "already open"
                )

                return

        # =====================================
        # CHECK RISK RULES
        # =====================================
        allowed, reason = self.risk_mgr.can_trade()

        if not allowed:

            print(f"❌ Trade blocked: {reason}")

            return

        # =====================================
        # HOLD
        # =====================================
        if signal not in ["BUY", "SELL"]:

            print("⏸ HOLD signal")

            update_metrics(

                self.risk_mgr,

                self.model,

                result
            )

            return

        # =====================================
        # STOP LOSS / TAKE PROFIT
        # =====================================
        if signal == "BUY":

            stop_loss = price * 0.98

            take_profit = price * 1.04

        else:

            stop_loss = price * 1.02

            take_profit = price * 0.96

        # =====================================
        # POSITION SIZE
        # =====================================
        shares = (
            self.risk_mgr
            .calculate_position_size(
                price,
                stop_loss
            )
        )

        # SAFE TEST SIZE
        shares = max(shares, 1)

        # =====================================
        # OPEN POSITION
        # =====================================
        self.risk_mgr.open_position(

            ticker=self.ticker,

            signal=signal,

            price=price,

            shares=shares,

            stop_loss=stop_loss,

            take_profit=take_profit
        )

        # =====================================
        # LOG TRADE
        # =====================================
        self.logger.log_trade({

            "ticker": self.ticker,

            "signal": signal,

            "price": price,

            "shares": shares,

            "confidence": confidence,

            "time": str(datetime.now())
        })

        # =====================================
        # UPDATE METRICS
        # =====================================
        update_metrics(

            self.risk_mgr,

            self.model,

            result
        )

        print("✅ Trade execution complete")    # =====================================
    # LIVE LOOP
    # =====================================
    def run_live_loop(

        self,

        interval_seconds=300
    ):

        print(

            f"\n🔴 LIVE LOOP STARTED "

            f"({interval_seconds}s)\n"
        )

        if not self.initialized:

            ok = self.initialize()

            if not ok:

                print("❌ Failed to initialize")

                return

        while True:

            try:

                self.execute_cycle()

                print(

                    f"\n⏰ Waiting "

                    f"{interval_seconds} seconds...\n"
                )

                time.sleep(interval_seconds)

            except KeyboardInterrupt:

                print("\n🛑 Live trading stopped")

                break

            except Exception as e:

                print(
                    f"\n❌ Runtime Error: {e}"
                )

                time.sleep(30)