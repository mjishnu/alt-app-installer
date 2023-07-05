import requests
import json

product_id = 'XP8BT8DW290MPQ'
# https://apps.microsoft.com/store/detail/windows-terminal/9N0DX20HK701?hl=en-in&gl=in
# https://apps.microsoft.com/store/detail/microsoft-teams/XP8BT8DW290MPQ



# getting cat_id and package name from the api
# details_api = "https://storeedgefd.dsx.mp.microsoft.com/v9.0/products"
# details_api = "https://displaycatalog.mp.microsoft.com/v7.0/products/"
details_api = f"https://storeedgefd.dsx.mp.microsoft.com/v9.0/packageManifests//{product_id}?market=US&locale=en-us&deviceFamily=Windows.Desktop"
# params = {"market": "US", "locale": "en-us","deviceFamily":"Windows.Desktop"}
# data = {"productIds": product_id}
session = requests.Session()
r = session.get(details_api,timeout=20)
data_list = r.text
y = json.loads(data_list)
z = y["Data"]["Versions"][0]["Installers"][0]["InstallerUrl"]
print(type(z),z)
# x = json.loads(z)
with open("r1.json","w") as f:
    json.dump(y,f)
