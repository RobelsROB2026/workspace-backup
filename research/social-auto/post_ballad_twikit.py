import asyncio
from twikit import Client

async def main():
    client = Client('en-US')
    client.load_cookies('/tmp/openclaw/uploads/twikit_cookies.json')
    
    media_id = '2032307708100014083'
    caption = "\"The road don't talk back, but she listens.\" \n\nMeet Barry Hauler, a truckin' man with a deep country drawl and a past that's just rolled back into town. From lonely desert highways to the jungles of 'Nam with Colonel Quawk, his story's got mystery, grit, and a whole lotta missing bananas.\n\nY'all best listen close. 🚛🛣️\n\n#TruckingLife #RoadWarrior #Trucking #BigRig"
    
    print("Creating tweet with media_id:", media_id)
    tweet = await client.create_tweet(
        text=caption,
        media_ids=[media_id]
    )
    print(f"Successfully posted! Tweet ID: {tweet.id}")
    print(f"URL: https://x.com/RobelAlema63562/status/{tweet.id}")

asyncio.run(main())
