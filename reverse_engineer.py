# reverse_engineer.py  ─ tested 2025-07-13
from curl_cffi import requests
import itertools, re
import json

PROXIES = itertools.cycle([
    "http://250621Ev04e-resi-any:5PjDM1IoS0JSr2c@proxy-jet.io:1010",
    # …add more strings here
])

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
      "AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/138.0.0.0 Safari/537.36")

def new_session():
    s = requests.Session()
    p = next(PROXIES)
    s.proxies = {"http": p, "https": p}
    s.headers.update({
        "User-Agent": UA,
        "Accept": "application/json",
        "x-ig-app-id": "936619743392459",   # **must match web app** :contentReference[oaicite:3]{index=3}
        "x-asbd-id": "359341",              # tiny feature flag :contentReference[oaicite:4]{index=4}
    })

    # one cheap GET to IG home gives csrftoken + LSD
    r = s.get("https://www.instagram.com/", timeout=10)
    r.raise_for_status()

    # csrftoken cookie → mirror into header
    s.headers["x-csrftoken"] = s.cookies.get("csrftoken")

    # LSD token is buried in the html:  '"LSD",[],{"token":"<VALUE>"...'
    lsd = re.search(r'"LSD",\[\],\{"token":"(.*?)"', r.text).group(1)
    s.headers["x-fb-lsd"] = lsd
    return s

def fetch_profile(username, session=None):
    session = session or new_session()
    url = (
        "https://www.instagram.com/api/v1/users/web_profile_info/"
        f"?username={username}"
    )
    r = session.get(url, timeout=10)
    r.raise_for_status()
    return r.json()["data"]["user"]

if __name__ == "__main__":
    sess = new_session()
    with open("response.json", "w", encoding="utf-8") as f:
        json.dump(fetch_profile("champagnepapi", sess), f, indent=2, ensure_ascii=False)
    print(fetch_profile("champagnepapi", sess)["edge_followed_by"]["count"])
