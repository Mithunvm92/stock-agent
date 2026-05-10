# Trading Strategy

## RSI Strategy (Default)

### Buy Signal (RSI < 30)
- Stock is oversold
- Price likely to bounce up
- **Action: BUY 1 share**

### Sell Signal (RSI > 70)
- Stock is overbought
- Price likely to drop
- **Action: SELL 1 share**

### Hold (RSI 30-70)
- No clear signal
- **Action: WAIT**

---

## Stocks to Trade
1. RELIANCE.NS
2. TCS.NS
3. HDFCBANK.NS
4. SBIN.NS
5. KOTAKBANK.NS

---

## How It Works
1. Bot checks every 5 minutes
2. Downloads 60 days of price data
3. Calculates RSI (14-period)
4. If RSI < 30 → BUY
5. If RSI > 70 → SELL
6. Otherwise → HOLD

---

## Risk Management
- Only 1 share per trade
- Paper trading by default (DRY_RUN=true)
- Set DRY_RUN=false in .env for live trading
