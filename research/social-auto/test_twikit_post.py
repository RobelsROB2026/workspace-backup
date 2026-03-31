import asyncio
from twikit import Client

async def main():
    client = Client('en-US')
    client.load_cookies('/tmp/openclaw/uploads/twikit_cookies.json')
    
    # Try posting a simple text tweet
    tweet = await client.create_tweet(text='Testing API wrapper integration 🚛')
    print(f"Successfully posted! Tweet ID: {tweet.id}")

asyncio.run(main())
