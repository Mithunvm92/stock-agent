from dotenv import load_dotenv
load_dotenv()

import os
import time
from kiteconnect import KiteConnect


class ZerodhaBroker:
    def __init__(self, auto_auth=True):
        self.api_key = os.getenv("ZERODHA_API_KEY", "")
        self.access_token = os.getenv("ZERODHA_ACCESS_TOKEN", "")
        
        if not self.api_key:
            raise ValueError("ZERODHA_API_KEY not set in .env")
        
        self.kite = KiteConnect(api_key=self.api_key)
        
        # Auto-authenticate if no valid token
        if not self.access_token and auto_auth:
            print("⚠️ No access token, attempting auto-auth...")
            self._auto_authenticate()
        
        if self.access_token:
            self.kite.set_access_token(self.access_token)
    
    def _auto_authenticate(self):
        """Auto-authenticate using credentials from .env."""
        try:
            from brokers.auto_auth import auto_auth
            token = auto_auth()
            if token:
                self.access_token = token
                self.kite.set_access_token(self.access_token)
                print("✅ Auto-authenticated!")
        except Exception as e:
            print(f"❌ Auto-auth failed: {e}")
            raise
    
    def place_market_order(self, symbol, transaction_type, quantity):
        """Place a market order."""
        return self.kite.place_order(
            variety="regular",
            exchange="NSE",
            trading_symbol=symbol,
            transaction_type=transaction_type.upper(),
            quantity=quantity,
            order_type="MARKET",
            product="CNC"
        )
    
    def place_limit_order(self, symbol, transaction_type, quantity, price):
        """Place a limit order."""
        return self.kite.place_order(
            variety="regular",
            exchange="NSE",
            trading_symbol=symbol,
            transaction_type=transaction_type.upper(),
            quantity=quantity,
            order_type="LIMIT",
            price=price,
            product="CNC"
        )
    
    def get_positions(self):
        """Get open positions."""
        return self.kite.positions()["net"]
    
    def get_orders(self):
        """Get order history."""
        return self.kite.orders()
    
    def get_quote(self, symbol):
        """Get quote for a symbol."""
        return self.kite.quote(symbol)
    
    def get_profile(self):
        """Get user profile."""
        return self.kite.profile()
    
    def cancel_order(self, order_id, variety="regular"):
        """Cancel an order."""
        return self.kite.cancel_order(order_id, variety=variety)
