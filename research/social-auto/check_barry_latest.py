import asyncio
from twikit import Client

async def main():
    client = Client('en-US')
    client.load_cookies('/tmp/openclaw/uploads/twikit_cookies.json')
    
    user = await client.get_user_by_screen_name('barryhauler')
    tweets = await user.get_tweets('Tweets', count=1)
    for tweet in tweets:
        print(f"https://x.com/barryhauler/status/{tweet.id}")

asyncio.run(main())
