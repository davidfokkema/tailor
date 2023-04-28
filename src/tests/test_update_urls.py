import json
import platform
import urllib.request

RELEASE_API_URL = (
    "https://api.github.com/repos/davidfokkema/tailor/releases/latest"
    # "https://api.github.com/repos/davidfokkema/tailor/releases/tags/v1.7.0"
    # "https://api.github.com/repos/davidfokkema/tailor/releases/tags/v1.5.0"
)

r = urllib.request.urlopen(RELEASE_API_URL)
release_info = json.loads(r.read())
latest_version = release_info["name"]
asset_urls = [a["browser_download_url"] for a in release_info["assets"]]

for url in asset_urls:
    print(url)
system, machine = platform.system(), platform.machine()
# asset_urls = {}
# system = "linux"
# machine = "x86_64"
try:
    match system, machine:
        case ("Darwin", "arm64"):
            download_url = next(
                (u for u in asset_urls if "apple_silicon.dmg" in u), None
            ) or next(u for u in asset_urls if ".dmg" in u)
        case ("Darwin", "x86_64"):
            download_url = next(
                (u for u in asset_urls if "intel.dmg" in u), None
            ) or next(u for u in asset_urls if ".dmg" in u)
        case ("Windows", *machine):
            download_url = next(v for k, v in asset_urls.items() if ".msi" in k)
        case default:
            # platform not yet supported
            download_url = None
except StopIteration:
    # the iterator in the next()-statement was empty, so no updates available
    download_url = None

print(f"{download_url=}")
