from dotenv import load_dotenv
load_dotenv()

import os

# ============================================
#  STOCK LIST — 30+ NSE STOCKS
# ============================================

TICKERS = [
    # NIFTY 50 Top Stocks
    "RELIANCE.NS",
    "TCS.NS",
    "HDFCBANK.NS",
    "INFY.NS",
    "ICICIBANK.NS",
    "HINDUNILVR.NS",
    "SBIN.NS",
    "BHARTIARTL.NS",
    "KOTAKBANK.NS",
    "ITC.NS",
    "LT.NS",
    "AXISBANK.NS",
    "ASIANPAINT.NS",
    "MARUTI.NS",
    "HCLTECH.NS",
    "SUNPHARMA.NS",
    "TITAN.NS",
    "BAJFINANCE.NS",
    "WIPRO.NS",
    "ULTRACEMCO.NS",
    "NESTLEIND.NS",
    "TATAMOTORS.NS",
    "POWERGRID.NS",
    "NTPC.NS",
    "TECHM.NS",
    "M&M.NS",
    "TATASTEEL.NS",
    "INDUSINDBK.NS",
    "BAJAJFINSV.NS",
    "ADANIENT.NS",
]

FALLBACK_TICKERS = ["AAPL", "MSFT", "GOOGL"]

# Small cap stocks under ₹1000 - good for small capital (₹2000)
SMALL_CAP_TICKERS = [
    "TATAMOTORS.NS",  # Tata Motors ~₹750
    "UPL.NS",  # UPL ~₹500
    "SBILIFE.NS",  # SBI Life ~₹800
    "ICICIPRULI.NS",  # ICICI Pru Life ~₹400
    "COFORGE.NS",  # Coforge ~₹4000
    "LTI.NS",  # L&T Infotech ~₹3500
    "MINDTREE.NS",  # MindTree ~₹900
    "RAMCOCEM.NS",  # Ramco Cement ~₹700
    "CASTROLIND.NS",  # Castrol India ~₹180
    "BHEL.NS",  # BHEL ~₹120
    "RBLBANK.NS",  # RBL Bank ~₹250
    "FEDERALBNK.NS",  # Federal Bank ~₹150
    "BANDHANBNK.NS",  # Bandhan Bank ~₹350
    "IDFCFIRSTB.NS",  # IDFC First ~₹70
    "AUBANK.NS",  # AU Bank ~₹600
    "PNB.NS",  # PNB ~₹100
    "UNIONBANK.NS",  # Union Bank ~₹80
    "CANBK.NS",  # Canara Bank ~₹350
    "BPCL.NS",  # BPCL ~₹300
    "IOC.NS",  # IOC ~₹120
]

PRIMARY_TICKER = os.getenv("TICKER", "RELIANCE.NS")

# ============================================
#  CAPITAL & RISK
# ============================================

INITIAL_CAPITAL = float(os.getenv("INITIAL_CAPITAL", 100000))
RISK_PER_TRADE = 0.02
MAX_DAILY_LOSS_PCT = 0.03
MAX_TOTAL_LOSS_PCT = 0.08
MAX_OPEN_POSITIONS = 3

# SL/TP Settings
STOP_LOSS_PCT = 0.018         # 1.8%
TAKE_PROFIT_PCT = 0.03        # 3.0%
TRAILING_STOP_PCT = 0.012

# Time exit
MAX_HOLD_BARS_LOSING = 7
MAX_HOLD_BARS_WINNING = 10

# ============================================
#  MODEL SETTINGS
# ============================================

MODEL_SAVE_DIR = "models/"
MODEL_SAVE_PATH = "models/trained_model.pkl"
SCALER_SAVE_PATH = "models/scaler.pkl"
RETRAIN_INTERVAL_HOURS = 24
LOOKBACK_PERIOD = "5y"
TRAIN_TEST_SPLIT = 0.80

# Target
TARGET_THRESHOLD_PCT = 0.005
TARGET_LOOKAHEAD_DAYS = 3

# Feature Selection
AUTO_FEATURE_SELECTION = True
MAX_FEATURES_TO_KEEP = 15

# ============================================
#  TIGHTENED FILTER SETTINGS
# ============================================

# Confidence — RAISED from 55% to 65%
MIN_CONFIDENCE = 55.0

# ADX — RAISED from 12 to 20 (need stronger trends)
MIN_ADX_FOR_TRADE = 15

# RSI — Must be in NEUTRAL zone (not overbought/oversold)
RSI_BUY_MAX = 65              # Don't buy if RSI > 65
RSI_BUY_MIN = 35              # Don't buy if RSI < 35 (could go lower)
RSI_SELL_MAX = 65             # Don't sell if RSI > 65 (could go higher)
RSI_SELL_MIN = 35             # Don't sell if RSI < 35

# Volatility — Must be in tradeable range
MIN_ATR_PCT = 1.0             # At least 1% daily volatility
MAX_ATR_PCT = 4.0             # Not more than 4% (too risky)

# Volume — Must have decent volume
MIN_VOLUME_RATIO = 0.5        # At least 70% of average volume

# Trend Alignment — Price position relative to moving averages
REQUIRE_TREND_ALIGNMENT = True
MIN_SMA_DISTANCE_PCT = -2.0   # For BUY: price not more than 2% below SMA20

# MACD — Must confirm direction
REQUIRE_MACD_CONFIRMATION = True

# Minimum filters to pass (out of 7)
MIN_FILTERS_TO_PASS = 4       # 6 out of 7 filters (86%)

# ============================================
#  PAPER TRADING SETTINGS
# ============================================

PAPER_TRADING_ENABLED = True
PAPER_TRADE_LOG_PATH = "db/paper_trades.csv"
PAPER_PORTFOLIO_PATH = "db/paper_portfolio.json"
PAPER_SCAN_INTERVAL_SECONDS = 300  # Check every 5 minutes

# ============================================
#  TELEGRAM SETTINGS
# ============================================

TELEGRAM_ENABLED = True
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "YOUR_CHAT_ID_HERE")

# ============================================
#  SCHEDULER SETTINGS
# ============================================

MARKET_OPEN = "09:15"
MARKET_CLOSE = "15:30"
TIMEZONE = "Asia/Kolkata"
SCAN_INTERVAL_MINUTES = 15
RETRAIN_TIME = "16:00"

# ============================================
#  LOGGING
# ============================================

TRADE_LOG_PATH = "db/trade_history.csv"
PERFORMANCE_LOG_PATH = "db/performance.csv"
SIGNAL_LOG_PATH = "db/signals.csv"

# LLM
USE_LLM_VALIDATION = False
LLM_API_URL = os.getenv("LLM_API_URL", "http://localhost:11434/api/generate")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3")


# ============================================
#  FUNDAMENTAL ANALYSIS FILTERS
# ============================================

FUNDAMENTAL_FILTERS = {
    # Debt & Liquidity
    'max_debt_equity': 1.5,          # Debt/Equity < 1.5
    'min_current_ratio': 1.2,        # Current Ratio > 1.2
    
    # Profitability
    'min_roe': 12.0,                 # ROE > 12%
    'min_roa': 6.0,                  # ROA > 6%
    'min_profit_margin': 8.0,        # Profit Margin > 8%
    
    # Growth
    'min_revenue_growth': 5.0,       # Revenue Growth > 5%
    'min_eps_growth': 5.0,           # EPS Growth > 5%
    
    # Ownership
    'min_promoter_holding': 25.0,    # Promoter/Insider > 25%
    'min_institutional_holding': 15.0,  # Institutions > 15%
    
    # Overall
    'min_score_to_trade': 50.0,      # Minimum 50% score to trade
}

# Enable/Disable fundamental filtering
USE_FUNDAMENTAL_FILTER = True
