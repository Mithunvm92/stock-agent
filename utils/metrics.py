from prometheus_client import (
    start_http_server,
    Gauge,
    Counter,
    Info
)

# =========================================
# METRIC DEFINITIONS
# =========================================

# ─────────────────────────────────────────
# GAUGES
# Values that go up/down
# ─────────────────────────────────────────
current_capital = Gauge(
    'bot_current_capital_inr',
    'Current available capital in INR'
)

total_pnl = Gauge(
    'bot_total_pnl_inr',
    'Total Profit and Loss in INR'
)

daily_pnl = Gauge(
    'bot_daily_pnl_inr',
    'Daily Profit and Loss in INR'
)

win_rate = Gauge(
    'bot_win_rate_percent',
    'Overall win rate percentage'
)

model_accuracy = Gauge(
    'bot_model_accuracy_percent',
    'Latest ML model accuracy'
)

open_positions = Gauge(
    'bot_open_positions_count',
    'Number of currently open positions'
)

signal_confidence = Gauge(
    'bot_latest_signal_confidence',
    'Confidence of latest ML signal'
)

trade_count_gauge = Gauge(
    'bot_trade_count',
    'Current total trade count'
)

wins_gauge = Gauge(
    'bot_wins_count',
    'Current total winning trades'
)

losses_gauge = Gauge(
    'bot_losses_count',
    'Current total losing trades'
)

# ─────────────────────────────────────────
# COUNTERS
# Values that only increase
# ─────────────────────────────────────────
total_trades = Counter(
    'bot_total_trades_count',
    'Total number of trades executed'
)

total_wins = Counter(
    'bot_total_wins_count',
    'Total number of winning trades'
)

total_losses = Counter(
    'bot_total_losses_count',
    'Total number of losing trades'
)

# ─────────────────────────────────────────
# INFO
# Static metadata
# ─────────────────────────────────────────
bot_info = Info(
    'bot_metadata',
    'Trading bot metadata'
)

# =========================================
# INTERNAL FLAGS
# =========================================
_metrics_started = False


# =========================================
# START METRICS SERVER
# =========================================
def start_metrics_server(port=8000):

    global _metrics_started

    if _metrics_started:

        print(
            "⚠️ Metrics server already running"
        )

        return

    try:

        print(
            f"📊 Starting Prometheus "
            f"metrics server on port {port}..."
        )

        start_http_server(port)

        # SET STATIC METADATA
        bot_info.info({

            'version': '1.0.0',

            'strategy': 'Ensemble_RF_GB_v3',

            'risk_per_trade': '2%',

            'max_daily_loss': '3%'
        })

        _metrics_started = True

    except OSError:

        print(
            "⚠️ Metrics server already active"
        )


# =========================================
# UPDATE METRICS
# =========================================
def update_metrics(

    risk_manager,

    model=None,

    signal_result=None
):

    try:

        # =====================================
        # RISK MANAGER METRICS
        # =====================================
        current_capital.set(

            float(
                getattr(
                    risk_manager,
                    'current_capital',
                    0
                )
            )
        )

        total_pnl.set(

            float(
                getattr(
                    risk_manager,
                    'total_pnl',
                    0
                )
            )
        )

        daily_pnl.set(

            float(
                getattr(
                    risk_manager,
                    'daily_pnl',
                    0
                )
            )
        )

        trade_count = int(

            getattr(
                risk_manager,
                'trade_count',
                0
            )
        )

        win_count = int(

            getattr(
                risk_manager,
                'win_count',
                0
            )
        )

        loss_count = int(

            getattr(
                risk_manager,
                'loss_count',
                0
            )
        )

        # WIN RATE
        calculated_win_rate = (

            (win_count / max(trade_count, 1))

            * 100
        )

        win_rate.set(
            calculated_win_rate
        )

        # OPEN POSITIONS
        open_positions.set(

            len(
                getattr(
                    risk_manager,
                    'open_positions',
                    []
                )
            )
        )

        # =====================================
        # GAUGE COUNTS
        # =====================================
        trade_count_gauge.set(
            trade_count
        )

        wins_gauge.set(
            win_count
        )

        losses_gauge.set(
            loss_count
        )

        # =====================================
        # COUNTER METRICS
        # SAFE DIRECT SET
        # =====================================
        total_trades._value.set(
            trade_count
        )

        total_wins._value.set(
            win_count
        )

        total_losses._value.set(
            loss_count
        )

        # =====================================
        # MODEL METRICS
        # =====================================
        if (

            model is not None and

            hasattr(model, 'accuracy')
        ):

            model_accuracy.set(

                float(model.accuracy)
            )

        # =====================================
        # SIGNAL METRICS
        # =====================================
        if (

            signal_result is not None and

            isinstance(signal_result, dict)
        ):

            confidence = float(

                signal_result.get(
                    'confidence',
                    0
                )
            )

            signal_confidence.set(
                confidence
            )

    except Exception as e:

        print(
            f"⚠️ Metrics update failed: {e}"
        )