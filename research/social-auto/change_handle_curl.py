import json
import requests
import time

cookies_dict = {}
with open("/tmp/openclaw/uploads/twikit_cookies.json") as f:
    cookies_dict = json.load(f)

# The twitter API requires x-csrf-token
csrf = cookies_dict.get("ct0")

headers = {
    "authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
    "x-csrf-token": csrf,
    "content-type": "application/x-www-form-urlencoded",
    "x-twitter-auth-type": "OAuth2Session",
    "x-twitter-client-language": "en",
    "x-twitter-active-user": "yes"
}

url = "https://x.com/i/api/1.1/account/settings.json"
data = {"screen_name": "barryhauler"}

r = requests.post(url, headers=headers, cookies=cookies_dict, data=data)
print("Status Code:", r.status_code)
print("Response:", r.text)

