import requests
import os
from datetime import datetime
from config.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_ENABLED


class TelegramAlert:
    """
    Send trading alerts to Telegram.
    
    Setup:
    1. Create a bot with @BotFather on Telegram
    2. Get the bot token
    3. Start a chat with your bot
    4. Get your chat ID from https://api.telegram.org/bot<TOKEN>/getUpdates
    5. Set environment variables:
       export TELEGRAM_BOT_TOKEN="your_token"
       export TELEGRAM_CHAT_ID="your_chat_id"
    """

    def __init__(self):
        self.token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.enabled = TELEGRAM_ENABLED and self.token != "YOUR_BOT_TOKEN_HERE"
        self.base_url = f"https://api.telegram.org/bot{self.token}"

    def send_message(self, message, parse_mode="HTML"):
        """Send a message to Telegram"""
        if not self.enabled:
            print(f"📱 [Telegram Disabled] {message[:100]}...")
            return False

        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode
            }
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                print(f"📱 Telegram sent ✅")
                return True
            else:
                print(f"📱 Telegram error: {response.text}")
                return False
                
        except Exception as e:
            print(f"📱 Telegram error: {e}")
            return False

    def send_signal_alert(self, signal_data, ticker):
        """Send a trading signal alert"""
        if signal_data['signal'] == "HOLD":
            return  # Don't send HOLD signals

        emoji = "🟢" if signal_data['signal'] == "BUY" else "🔴"
        
        message = f"""
{emoji} <b>TRADING SIGNAL</b> {emoji}

<b>Stock:</b> {ticker}
<b>Signal:</b> {signal_data['signal']}
<b>Price:</b> ₹{signal_data['price']:.2f}
<b>Confidence:</b> {signal_data['confidence']:.1f}%

<b>Entry:</b> ₹{signal_data['price']:.2f}
<b>Stop Loss:</b> ₹{signal_data['stop_loss']:.2f}
<b>Target:</b> ₹{signal_data['take_profit']:.2f}
<b>Risk:Reward:</b> 1:{signal_data['risk_reward']}

<b>Reason:</b> {signal_data['reason']}
<b>Filters:</b> {signal_data['filters_passed']}/{signal_data['total_filters']} passed

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return self.send_message(message)

    def send_scan_results(self, results):
        """Send scan results summary"""
        if not results:
            return

        # Filter only actionable signals
        actionable = [r for r in results if r.get('signal') in ['BUY', 'SELL']]
        
        if not actionable:
            message = f"""
📊 <b>MARKET SCAN COMPLETE</b>

Scanned: {len(results)} stocks
Signals: No actionable signals found

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        else:
            signals_text = ""
            for r in sorted(actionable, key=lambda x: x.get('confidence', 0), reverse=True)[:5]:
                emoji = "🟢" if r.get('signal') == 'BUY' else "🔴"
                signals_text += f"\n{emoji} <b>{r.get('ticker', '?')}</b>: {r.get('signal')} @ {r.get('confidence', 0):.1f}%"
                signals_text += f"\n   Entry: ₹{r.get('price', 0):.2f} | SL: ₹{r.get('stop_loss', 0):.2f} | TP: ₹{r.get('take_profit', 0):.2f}"

            message = f"""
📊 <b>MARKET SCAN COMPLETE</b>

Scanned: {len(results)} stocks
Signals Found: {len(actionable)}

<b>TOP OPPORTUNITIES:</b>
{signals_text}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return self.send_message(message)

    def send_trade_executed(self, ticker, signal, price, shares, stop_loss, take_profit):
        """Alert when a trade is executed"""
        emoji = "📈" if signal == "BUY" else "📉"
        
        message = f"""
{emoji} <b>TRADE EXECUTED</b>

<b>Stock:</b> {ticker}
<b>Action:</b> {signal}
<b>Price:</b> ₹{price:.2f}
<b>Shares:</b> {shares}
<b>Value:</b> ₹{price * shares:,.2f}

<b>Stop Loss:</b> ₹{stop_loss:.2f}
<b>Take Profit:</b> ₹{take_profit:.2f}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return self.send_message(message)

    def send_trade_closed(self, ticker, pnl, pnl_pct, reason):
        """Alert when a trade is closed"""
        emoji = "✅" if pnl >= 0 else "❌"
        
        message = f"""
{emoji} <b>TRADE CLOSED</b>

<b>Stock:</b> {ticker}
<b>P&L:</b> ₹{pnl:+,.2f} ({pnl_pct:+.1f}%)
<b>Reason:</b> {reason}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return self.send_message(message)

    def send_daily_summary(self, trades_today, pnl_today, capital):
        """Send end-of-day summary"""
        emoji = "📈" if pnl_today >= 0 else "📉"
        
        message = f"""
{emoji} <b>DAILY SUMMARY</b>

<b>Trades Today:</b> {trades_today}
<b>P&L Today:</b> ₹{pnl_today:+,.2f}
<b>Current Capital:</b> ₹{capital:,.2f}

⏰ {datetime.now().strftime('%Y-%m-%d')}
"""
        return self.send_message(message)

    def send_startup(self):
        """Send startup notification"""
        message = f"""
🚀 <b>TRADING BOT STARTED</b>

System initialized and ready.
Monitoring market for signals.

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return self.send_message(message)

    def send_shutdown(self):
        """Send shutdown notification"""
        message = f"""
🛑 <b>TRADING BOT STOPPED</b>

System has been shut down.

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return self.send_message(message)

    def send_error(self, error_msg):
        """Send error notification"""
        message = f"""
⚠️ <b>ERROR ALERT</b>

{error_msg}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return self.send_message(message)

    def send_retrain_complete(self, accuracy, features_used):
        """Send retraining notification"""
        message = f"""
🤖 <b>MODEL RETRAINED</b>

<b>Accuracy:</b> {accuracy:.1f}%
<b>Features:</b> {features_used}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return self.send_message(message)
