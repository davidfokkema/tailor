import json
import platform
import urllib.request

RELEASE_API_URL = "https://api.github.com/repos/davidfokkema/tailor/releases/latest"

r = urllib.request.urlopen(RELEASE_API_URL)
release_info = json.loads(r.read())
latest_version = release_info["name"]
asset_urls = {a["name"]: a["browser_download_url"] for a in release_info["assets"]}

for url in asset_urls:
    print(url)

match platform.system(), platform.machine():
    case ("Darwin", "arm64"):
        download_url = next(
            v for k, v in asset_urls.items() if ".dmg" in k and "apple_silicon" in k
        )
    case ("Darwin", "x86_64"):
        download_url = next(
            v for k, v in asset_urls.items() if ".dmg" in k and "intel" in k
        )
    case ("Windows", *machine):
        download_url = next(v for k, v in asset_urls.items() if ".msi" in k)

print(download_url)
