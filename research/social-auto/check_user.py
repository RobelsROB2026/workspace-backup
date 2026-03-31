import asyncio
from twikit import Client

async def main():
    client = Client('en-US')
    client.load_cookies('/tmp/openclaw/uploads/twikit_cookies.json')
    try:
        user = await client.get_user_by_screen_name('barryhauler')
        print(f"Found: {user.name}")
    except Exception as e:
        print("Error:", e)

asyncio.run(main())
