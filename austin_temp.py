import urllib.request
import json

url = "https://api.open-meteo.com/v1/forecast?latitude=30.2672&longitude=-97.7431&current=temperature_2m&temperature_unit=fahrenheit"

with urllib.request.urlopen(url) as response:
    data = json.loads(response.read())

temp = data["current"]["temperature_2m"]
print(f"Austin, TX: {temp}°F")
