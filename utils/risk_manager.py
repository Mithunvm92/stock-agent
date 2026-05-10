from datetime import datetime


class RiskManager:

    def __init__(self):

        # =====================================
        # CAPITAL
        # =====================================
        self.initial_capital = 2000

        self.current_capital = 2000

        self.total_pnl = 0

        self.daily_pnl = 0

        # =====================================
        # RISK SETTINGS
        # =====================================
        self.max_risk_per_trade = 0.02

        self.max_daily_loss = 0.05

        self.max_open_positions = 3

        # =====================================
        # TRADE TRACKING
        # =====================================
        self.open_positions = []

        self.trade_history = []

        # PRIMARY COUNTERS
        self.trade_count = 0

        self.win_count = 0

        self.loss_count = 0

        self.win_rate = 0

        # COMPATIBILITY ALIASES
        self.total_trades = 0

        self.winning_trades = 0

        self.losing_trades = 0

        # =====================================
        # SYSTEM FLAGS
        # =====================================
        self.shutdown = False

    # =====================================
    # CAN TRADE?
    # =====================================
    def can_trade(self):

        if self.shutdown:

            return False, "Shutdown active"

        daily_limit = (

            self.initial_capital *

            self.max_daily_loss
        )

        if self.daily_pnl <= -daily_limit:

            self.shutdown = True

            return False, "Daily loss limit reached"

        if len(self.open_positions) >= self.max_open_positions:

            return False, "Max open positions reached"

        return True, "OK"

    # =====================================
    # POSITION SIZE
    # =====================================
    def calculate_position_size(

        self,

        entry_price,

        stop_loss
    ):

        if stop_loss is None:

            return 1

        risk_amount = (

            self.current_capital *

            self.max_risk_per_trade
        )

        risk_per_share = abs(

            entry_price -

            stop_loss
        )

        if risk_per_share <= 0:

            return 1

        shares = int(

            risk_amount /

            risk_per_share
        )

        shares = max(shares, 1)

        return shares

    # =====================================
    # OPEN POSITION
    # =====================================
    def open_position(

        self,

        ticker,

        signal,

        price,

        shares,

        stop_loss=None,

        take_profit=None
    ):

        position = {

            "ticker": ticker,

            "signal": signal,

            "entry_price": price,

            "shares": shares,

            "stop_loss": stop_loss,

            "take_profit": take_profit,

            "opened_at": datetime.now()
        }

        self.open_positions.append(position)

        cost = price * shares

        self.current_capital -= cost

        print(f"\n📈 OPENED {signal}")

        print(f"Ticker: {ticker}")

        print(f"Price: ₹{price:.2f}")

        print(f"Shares: {shares}")

        print(
            f"Capital Left: "
            f"₹{self.current_capital:.2f}"
        )

        return position

    # =====================================
    # CHECK EXITS
    # =====================================
    def check_exits(self, current_price):

        remaining_positions = []

        for pos in self.open_positions:

            exit_trade = False

            pnl = 0

            if pos['signal'] == 'BUY':

                pnl = (

                    current_price -

                    pos['entry_price']
                ) * pos['shares']

                # STOP LOSS
                if (

                    pos['stop_loss'] and

                    current_price <= pos['stop_loss']
                ):

                    print("🛑 Stop loss hit")

                    exit_trade = True

                # TAKE PROFIT
                if (

                    pos['take_profit'] and

                    current_price >= pos['take_profit']
                ):

                    print("🎯 Take profit hit")

                    exit_trade = True

            # =====================================
            # CLOSE POSITION
            # =====================================
            if exit_trade:

                self.current_capital += (

                    current_price *

                    pos['shares']
                )

                self.daily_pnl += pnl

                self.total_pnl += pnl

                # UPDATE COUNTERS
                self.total_trades += 1

                self.trade_count += 1

                if pnl > 0:

                    self.winning_trades += 1

                    self.win_count += 1

                else:

                    self.losing_trades += 1

                    self.loss_count += 1

                # UPDATE WIN RATE
                if self.total_trades > 0:

                    self.win_rate = (

                        self.winning_trades /

                        self.total_trades
                    ) * 100

                self.trade_history.append({

                    "ticker": pos['ticker'],

                    "pnl": pnl,

                    "closed_at": datetime.now()
                })

                print(

                    f"💰 CLOSED "

                    f"{pos['ticker']} | "

                    f"PnL: ₹{pnl:.2f}"
                )

            else:

                remaining_positions.append(pos)

        self.open_positions = remaining_positions

    # =====================================
    # STATUS
    # =====================================
    def get_status(self):

        print("\n═══════════════════════════════════════")

        print("        PORTFOLIO STATUS")

        print("═══════════════════════════════════════")

        print(

            f"Initial Capital: "

            f"₹{self.initial_capital:.2f}"
        )

        print(

            f"Current Capital: "

            f"₹{self.current_capital:.2f}"
        )

        print(

            f"Total PnL: "

            f"₹{self.total_pnl:.2f}"
        )

        print(

            f"Daily PnL: "

            f"₹{self.daily_pnl:.2f}"
        )

        print(

            f"Open Positions: "

            f"{len(self.open_positions)}"
        )

        print(

            f"Total Trades: "

            f"{self.total_trades}"
        )

        print(

            f"Win Rate: "

            f"{self.win_rate:.1f}%"
        )

        print("═══════════════════════════════════════\n")