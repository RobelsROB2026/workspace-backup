import asyncio
from twikit import Client

async def main():
    client = Client('en-US')
    client.load_cookies('/tmp/openclaw/uploads/twikit_cookies.json')
    
    # Let's get our own user object
    user = await client.get_user_by_screen_name('RobelAlema63562')
    print(f"Logged in / Found user: {user.name} (@{user.screen_name})")
    
    # Try fetching timeline to see if auth is valid
    tweets = await client.get_latest_timeline()
    print(f"Successfully fetched timeline, got {len(tweets)} tweets.")

asyncio.run(main())
