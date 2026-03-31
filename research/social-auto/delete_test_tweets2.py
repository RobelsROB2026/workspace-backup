import asyncio
from twikit import Client

async def main():
    client = Client('en-US')
    client.load_cookies('/tmp/openclaw/uploads/twikit_cookies.json')
    
    test_tweet_ids = [
        "2031378046574342230", # Text-only curveball
    ]
    
    for tweet_id in test_tweet_ids:
        try:
            await client.delete_tweet(tweet_id)
            print(f"Deleted tweet {tweet_id}")
        except Exception as e:
            print(f"Failed to delete {tweet_id}: {e}")

asyncio.run(main())
