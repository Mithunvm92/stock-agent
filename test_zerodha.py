"""Quick test and token generator."""
import os
from kiteconnect import KiteConnect

# Your credentials
API_KEY = "yy5no3jj0ynnc49f"
API_SECRET = "your_api_secret_here"  # Replace this!

def get_login_url():
    kite = KiteConnect(api_key=API_KEY)
    return kite.login_url()

def test_token(request_token):
    kite = KiteConnect(api_key=API_KEY)
    try:
        data = kite.generate_session(request_token, api_secret=API_SECRET)
        access_token = data["access_token"]
        
        # Test the token
        kite.set_access_token(access_token)
        profile = kite.profile()
        
        print("✅ SUCCESS!")
        print(f"User: {profile["user_name"]}")
        print(f"Email: {profile["email"]}")
        print(f"Access Token: {access_token}")
        return access_token
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        test_token(sys.argv[1])
    else:
        print("Usage: python test_zerodha.py <request_token>")
        print(f"Login URL: {get_login_url()}")
