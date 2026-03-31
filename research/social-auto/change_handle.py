import asyncio
from twikit import Client

async def main():
    client = Client('en-US')
    client.load_cookies('/tmp/openclaw/uploads/twikit_cookies.json')
    
    # manual POST
    url = "https://x.com/i/api/1.1/account/settings.json"
    payload = {"screen_name": "barryhauler"}
    try:
        res = await client.post(url, data=payload)
        print("Response:", res.json())
    except Exception as e:
        print("Error:", e)

asyncio.run(main())
