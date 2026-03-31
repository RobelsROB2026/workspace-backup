import asyncio
from twikit import Client

async def main():
    client = Client('en-US')
    client.load_cookies('/tmp/openclaw/uploads/twikit_cookies.json')
    
    print("Uploading video...")
    media_id = await client.upload_media(
        '/tmp/openclaw/uploads/ballad_barry_hauler.mp4',
        wait_for_completion=True,
        media_category='tweet_video'
    )
    print(f"Uploaded! Media ID: {media_id}")

asyncio.run(main())
