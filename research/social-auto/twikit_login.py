
import asyncio
import json
import os
import sys
from twikit import Client

COOKIES_FILE = "/tmp/openclaw/uploads/twikit_cookies.json"
USERNAME = "barryhauler"
EMAIL = "robake2006@gmail.com"
PASSWORD = "BarryHauler2026!"

async def main():
    client = Client('en-US')
    
    print(f"Attempting twikit login for {USERNAME}...")
    try:
        await client.login(
            auth_info_1=USERNAME,
            auth_info_2=EMAIL,
            password=PASSWORD
        )
        print("Login successful!")
        
        # Save cookies for next time
        client.save_cookies(COOKIES_FILE)
        print(f"Cookies saved to {COOKIES_FILE}")
        
    except Exception as e:
        print(f"Login failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
