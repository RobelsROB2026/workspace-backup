import asyncio
from twikit import Client

async def main():
    client = Client('en-US')
    client.load_cookies('/tmp/openclaw/uploads/twikit_cookies.json')
    
    media_id = "2032098389970522112"
    
    media_entities = [
        {'media_id': media_id, 'tagged_users': []}
    ]
    
    print("Calling create_tweet gql...")
    response, _ = await client.gql.create_tweet(
        is_note_tweet=False,
        text='Barry fever dream 🚛 #truckersoftiktok #barryhauler #trucking',
        media_entities=media_entities,
        poll_uri=None,
        reply_to=None,
        attachment_url=None,
        community_id=None,
        share_with_followers=False,
        richtext_options=None,
        edit_tweet_id=None,
        limit_mode=None
    )
    print(response)

asyncio.run(main())
