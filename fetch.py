import time
from requests import Session

rest = Session()
rest.headers.update(
    {"User-Agent": "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/5320 (KHTML, like Gecko) Chrome/36.0.875.0 Mobile Safari/5320"})

r = rest.get("https://aptos-mainnet-api.bluemove.net/api/launchpads?sort[0]=start_time%3Adesc")
r.raise_for_status()

for launch in r.json()['data']:
    if (int(time.time()) < int(launch['attributes']['start_time'])/1000):
        
        collection = launch['attributes']['collection_name']
        factory = launch['attributes']['module_address']
        creator = launch['attributes']['cap_address']
        type = launch['attributes']['launchpad_name_extension']
        price = int(launch['attributes']['price_per_item'])/(10**8)
        print("Collection:", collection)
        print("  factory:", factory)
        print("  creator:", creator)
        print("  type:", type)
        print("  price:", price)