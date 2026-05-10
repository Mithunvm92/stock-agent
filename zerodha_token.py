#!/usr/bin/env python3
"""
Zerodha Access Token Generator
Run this to generate access token from request token.
"""
import os
import sys

def generate_access_token(api_key, api_secret, request_token):
    """Generate access token from request token."""
    from kiteconnect import KiteConnect
    
    kite = KiteConnect(api_key=api_key)
    
    try:
        data = kite.generate_session(request_token, api_secret=api_secret)
        access_token = data["access_token"]
        print(f"\n✅ Access Token Generated!")
        print(f"Access Token: {access_token}")
        print(f"\nAdd to .env:")
        print(f"ZERODHA_API_KEY={api_key}")
        print(f"ZERODHA_ACCESS_TOKEN={access_token}")
        return access_token
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def main():
    if len(sys.argv) < 4:
        print("Usage: python zerodha_token.py <api_key> <api_secret> <request_token>")
        print("\nSteps:")
        print("1. Go to https://developers.zerodha.com & create app")
        print("2. Get api_key and api_secret")
        print("3. Visit: https://kite.zerodha.com/connect?api_key=YOUR_KEY")
        print("4. Login and get request_token from redirect URL")
        print("5. Run: python zerodha_token.py YOUR_KEY YOUR_SECRET request_token")
        sys.exit(1)
    
    api_key = sys.argv[1]
    api_secret = sys.argv[2]
    request_token = sys.argv[3]
    
    generate_access_token(api_key, api_secret, request_token)

if __name__ == "__main__":
    main()