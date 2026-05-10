"""
Auto-authenticate with Zerodha.
Requires manual login once to get request_token, then exchange for access_token.
"""
import os
from dotenv import load_dotenv

load_dotenv()

def get_login_url():
    """Get Zerodha login URL."""
    from kiteconnect import KiteConnect
    api_key = os.getenv("ZERODHA_API_KEY", "")
    if not api_key:
        print("Set ZERODHA_API_KEY in .env")
        return None
    kite = KiteConnect(api_key=api_key)
    return kite.login_url()


def generate_access_token(request_token):
    """Generate access token from request token."""
    from kiteconnect import KiteConnect
    
    api_key = os.getenv("ZERODHA_API_KEY", "")
    api_secret = os.getenv("ZERODHA_API_SECRET", "")
    
    if not api_key or not api_secret or not request_token:
        print("Missing api_key, api_secret, or request_token")
        return None
    
    kite = KiteConnect(api_key=api_key)
    
    try:
        data = kite.generate_session(request_token, api_secret=api_secret)
        access_token = data["access_token"]
        return access_token
    except Exception as e:
        print(f"Error: {e}")
        return None


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--url":
            url = get_login_url()
            if url:
                print(f"Login URL: {url}")
                print("\n1. Visit the URL")
                print("2. Login with Zerodha credentials")
                print("3. Copy the request_token from redirect URL")
                print("4. Run: python brokers/auto_auth.py <request_token>")
        else:
            # Use provided request token
            request_token = sys.argv[1]
            token = generate_access_token(request_token)
            if token:
                print(f"✅ Access Token: {token}")
                print(f"\nAdd to .env:")
                print(f"ZERODHA_ACCESS_TOKEN={token}")
    else:
        url = get_login_url()
        if url:
            print(f"Login URL: {url}")
            print("\nUsage: python brokers/auto_auth.py --url")
            print("   or: python brokers/auto_auth.py <request_token>")
