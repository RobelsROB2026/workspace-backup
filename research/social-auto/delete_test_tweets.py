import asyncio
from twikit import Client

async def main():
    client = Client('en-US')
    client.load_cookies('/tmp/openclaw/uploads/twikit_cookies.json')
    
    # Clean up the test tweets that didn't have media
    test_tweet_ids = [
        "2032096366155968874", # Testing API wrapper integration
        "2031893357018919364", # Text-only Barry fever dream
        "2031870675539890533", # Text-only wrench
        "2031764809973211468"  # Text-only ghosts
    ]
    
    for tweet_id in test_tweet_ids:
        try:
            await client.delete_tweet(tweet_id)
            print(f"Deleted tweet {tweet_id}")
        except Exception as e:
            print(f"Failed to delete {tweet_id}: {e}")

asyncio.run(main())
