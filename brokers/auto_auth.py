"""
Auto-authenticate with Zerodha before market hours.
Run this script daily before trading starts to refresh access token.
"""
import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

from kiteconnect import KiteConnect


def get_login_url(api_key):
    """Generate login URL for Zerodha."""
    kite = KiteConnect(api_key=api_key)
    return kite.login_url()


def generate_access_token(api_key, api_secret, request_token):
    """Generate access token from request token."""
    kite = KiteConnect(api_key=api_key)
    data = kite.generate_session(request_token, api_secret=api_secret)
    return data["access_token"]


def auto_auth():
    """Auto-authenticate and update .env with new access token."""
    api_key = os.getenv("ZERODHA_API_KEY")
    api_secret = os.getenv("ZERODHA_API_SECRET")
    user_id = os.getenv("ZERODHA_USER_ID")
    password = os.getenv("ZERODHA_PASSWORD")
    totp_secret = os.getenv("ZERODHA_TOTP_SECRET")
    
    if not all([api_key, api_secret, user_id, password, totp_secret]):
        print("❌ Missing credentials in .env")
        print("Need: ZERODHA_API_KEY, ZERODHA_API_SECRET, ZERODHA_USER_ID, ZERODHA_PASSWORD, ZERODHA_TOTP_SECRET")
        return None
    
    try:
        # Import TOTP
        import pyotp
        
        kite = KiteConnect(api_key=api_key)
        twofa = pyotp.TOTP(totp_secret)
        
        # Generate session
        data = kite.generate_session(
            user_id,
            password=password,
            twofa_code=twofa.now()
        )
        
        access_token = data["access_token"]
        print(f"✅ Access token generated!")
        
        # Save to .env
        with open('.env', 'a') as f:
            f.write(f"\nZERODHA_ACCESS_TOKEN={access_token}")
        
        # Also set in environment
        os.environ["ZERODHA_ACCESS_TOKEN"] = access_token
        
        return access_token
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def check_market_time():
    """Check if market is open (weekday 9:15-15:30 IST)."""
    import pytz
    
    IST = pytz.timezone('Asia/Kolkata')
    now = datetime.now(IST)
    
    # Market hours: Mon-Fri, 9:15 AM - 3:30 PM
    is_weekday = now.weekday() < 5
    is_market_hours = 9*60+15 <= now.hour*60 + now.minute <= 15*60+30
    
    return is_weekday and is_market_hours


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--url":
        api_key = os.getenv("ZERODHA_API_KEY", "")
        if api_key:
            url = get_login_url(api_key)
            print(f"Login URL: {url}")
        else:
            print("Set ZERODHA_API_KEY in .env first")
    else:
        token = auto_auth()
        if token:
            print(f"Access Token: {token}")
