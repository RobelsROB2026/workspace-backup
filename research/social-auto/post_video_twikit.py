
import asyncio
import json
import os
import sys
from twikit import Client

PREP_FILE = os.path.expanduser("~/research/social-auto/barry_prepped_post.json")
STATE_FILE = os.path.expanduser("~/research/social-auto/barry_video_state.json")
COOKIES_FILE = "/tmp/openclaw/uploads/twikit_cookies.json"

async def main():
    if not os.path.exists(PREP_FILE):
        print("Error: No prepped post found.")
        return

    with open(PREP_FILE, "r") as f:
        prepped = json.load(f)

    vid_id = prepped["id"]
    local_path = prepped["local_path"]
    caption = prepped["caption"]

    print(f"Posting to X via twikit: {local_path}")

    client = Client('en-US')
    
    # Load cookies
    with open(COOKIES_FILE, 'r') as f:
        cookies = json.load(f)
    
    # Twikit expects a specific format or we can use set_cookies
    # Looking at twikit docs, we can use client.set_cookies(cookies)
    client.set_cookies(cookies)

    try:
        # Upload media
        # twikit.Client.upload_media(file, media_type='video/mp4')
        media_id = await client.upload_media(local_path, media_type='video/mp4')
        print(f"Media uploaded. ID: {media_id}")

        # Create tweet
        tweet = await client.create_tweet(text=caption, media_ids=[media_id])
        print(f"Tweet created successfully! ID: {tweet.id}")

        # Update state
        state = {"posted_drive_ids": []}
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r") as f:
                state = json.load(f)
        
        if vid_id not in state["posted_drive_ids"]:
            state["posted_drive_ids"].append(vid_id)
            with open(STATE_FILE, "w") as f:
                json.dump(state, f, indent=2)

        # Cleanup
        os.remove(PREP_FILE)
        print("Done.")

    except Exception as e:
        print(f"Failed to post via twikit: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
