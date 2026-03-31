import asyncio
from twikit import Client

async def main():
    client = Client('en-US')
    client.load_cookies('/tmp/openclaw/uploads/twikit_cookies.json')
    
    user = await client.get_user_by_screen_name('RobelAlema63562')
    tweets = await user.get_tweets('Tweets', count=5)
    for tweet in tweets:
        print(f"ID: {tweet.id}")
        print(f"Text: {tweet.text}")
        print(f"Has media: {len(tweet.media) if hasattr(tweet, 'media') and tweet.media else 'No'}")
        print("---")

asyncio.run(main())
