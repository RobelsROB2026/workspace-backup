import asyncio
from twikit import Client

async def main():
    client = Client('en-US')
    client.load_cookies('/tmp/openclaw/uploads/twikit_cookies.json')
    
    # Optional: fetch the current user's profile to verify login
    user = await client.user()
    print(f"Logged in as: {user.screen_name} (ID: {user.id})")

asyncio.run(main())
