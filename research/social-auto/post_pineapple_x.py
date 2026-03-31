import asyncio
from twikit import Client

async def main():
    client = Client('en-US')
    client.load_cookies('/tmp/openclaw/uploads/twikit_cookies.json')
    
    media_id = await client.upload_media(
        '/tmp/openclaw/uploads/pineapple.mp4',
        wait_for_completion=True,
        media_category='tweet_video'
    )
    
    caption = "they said Barry couldn't hit a curveball. 50 years of shifting gears gives you one hell of an arm. 🚛⚾🍍\n\n#trucking #barryhauler #truckerlife"
    
    print("Creating tweet with media_id:", media_id)
    tweet = await client.create_tweet(
        text=caption,
        media_ids=[media_id]
    )
    print(f"Successfully posted to X! Tweet ID: {tweet.id}")
    print(f"URL: https://x.com/barryhauler/status/{tweet.id}")

asyncio.run(main())
