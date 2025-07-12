# instagram_profile_scraper.py
"""
Instagram Profile Scraper & Parser
=================================
Collects **public** profile data for one or more Instagram usernames, profile
URLs, or pre‑downloaded HTML files.  
Now includes **bio text and all external links** (e.g. stake.com, YouTube)
exposed on the profile page.

Extracted fields (top‑level keys)
---------------------------------
* `username`, `full_name`, `is_verified`, `profile_pic_url`
* `followers`, `following`, `posts`
* `biography` (plain text bio)
* `external_url` – the single clickable link IG lets the user set
* `bio_links` – every http(s) link we can spot inside the bio & clickable link
* `og_*`, `meta_description`, `canonical_url` for SEO/OG reference
* `raw.graphql_user` – the full GraphQL user blob for anything else you need

Input options & examples
------------------------
```bash
# Live scrape with Jet proxy (pretty printed)
python instagram_profile_scraper.py -u champagnepapi \
       -p '250621Ev04e-resi-any:5PjDM1IoS0JSr2c@proxy-jet.io:1010' --pretty

# Parse pre‑saved HTML (offline)
python instagram_profile_scraper.py --html response.html --pretty

# Bulk usernames via file + multi‑proxy list
python instagram_profile_scraper.py -i usernames.txt -p proxies.txt --pretty
```

Install requirements
~~~~~~~~~~~~~~~~~~~~
```bash
pip install requests beautifulsoup4 lxml
```
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from itertools import cycle
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple, Union

import requests
from bs4 import BeautifulSoup, SoupStrainer

################################################################################
# CONSTANTS                                                                     
################################################################################

HEADERS_DEFAULT = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

META_MAP = {
    "og:title": "og_title",
    "og:description": "og_description",
    "og:image": "profile_pic_url",
    "og:url": "canonical_url",
    "description": "meta_description",
}

COUNT_PATTERN = re.compile(
    r"(\d+[\d\.,]*)([KM]?) Followers,\s*(\d+[\d\.,]*)([KM]?) Following,\s*([\d\.,]+) Posts",
    re.IGNORECASE,
)

HTTP_LINK_RE = re.compile(r'https?://[^\s\'"`]+', re.I)

################################################################################
# PROXY ROTATOR                                                                 
################################################################################

class ProxyRotator:
    def __init__(self, proxies: List[str]):
        cleaned = [p.strip() for p in proxies if p and p.strip()]
        self._iter = cycle(cleaned or [None])

    def next(self) -> Optional[str]:
        return next(self._iter)

################################################################################
# UTILS                                                                         
################################################################################

def _build_requests_proxy(proxy: Optional[str]) -> Optional[Dict[str, str]]:
    if not proxy:
        return None
    if not re.match(r"^(?:\w+:\w+@)?[^:]+:\d+$", proxy):
        raise ValueError(f"Invalid proxy format: {proxy}")
    return {"http": f"http://{proxy}", "https": f"http://{proxy}"}


def _to_number(value: str, suffix: str) -> int:
    num = float(value.replace(",", ""))
    factor = {"K": 1_000, "M": 1_000_000}.get(suffix.upper(), 1)
    return int(num * factor)


def _extract_first_json_blob(text: str) -> Optional[str]:
    start = text.find("{")
    if start == -1:
        return None
    depth, in_str, prev = 0, False, ""
    for idx, ch in enumerate(text[start:], start=start):
        if ch == "\"" and prev != "\\":
            in_str = not in_str
        elif not in_str:
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start : idx + 1]
        prev = ch
    return None

################################################################################
# NETWORK / FILE I/O                                                            
################################################################################

def fetch_html(url: str, session: requests.Session, proxy: Optional[str]) -> str:
    resp = session.get(url, proxies=_build_requests_proxy(proxy), timeout=(5, 15))
    resp.raise_for_status()
    return resp.text


def load_html_file(path: Union[str, Path]) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
        return fh.read()

################################################################################
# PARSING                                                                       
################################################################################

def _extract_external_links_from_html(html: str) -> List[str]:
    """Grab all http(s) links that *aren’t* internal instagram.com URLs."""
    links = []
    for tag in BeautifulSoup(html, "lxml", parse_only=SoupStrainer("a")).find_all("a"):
        href = tag.get("href")
        if href and href.startswith("http") and "instagram.com" not in href:
            links.append(href.split("?", 1)[0])
    return list(dict.fromkeys(links))  # dedupe while preserving order


def parse_profile_html(html: str) -> Dict[str, Union[str, int, Dict, List[str]]]:
    """Return a dict of extracted profile data."""
    soup = BeautifulSoup(html, "lxml", parse_only=SoupStrainer(["meta", "script"]))
    data: Dict[str, Union[str, int, Dict, List[str]]] = {}

    # 1) Open‑Graph & meta
    for tag in soup.find_all("meta"):
        k = tag.get("property") or tag.get("name")
        if k in META_MAP:
            data[META_MAP[k]] = tag.get("content", "")

    # 2) Follower counts from description
    desc = data.get("og_description") or data.get("meta_description")
    if desc and (m := COUNT_PATTERN.search(desc.replace("·", ","))):
        f, f_suf, fg, fg_suf, p = m.groups()
        data["followers"], data["following"], data["posts"] = (
            _to_number(f, f_suf),
            _to_number(fg, fg_suf),
            int(p.replace(",", "")),
        )

    # 3) JSON‑LD schema blocks
    for s in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            js = json.loads(s.string or "{}")
            if js.get("@type") == "Person":
                data.setdefault("full_name", js.get("name"))
                data.setdefault("description", js.get("description"))
                data.setdefault("profile_pic_url", js.get("image"))
        except json.JSONDecodeError:
            pass

    # 4) Embedded JS payloads (GraphQL)
    for s in soup.find_all("script"):
        txt = s.string or ""
        if "window._sharedData" in txt or "relayPrefetch" in txt:
            blob = _extract_first_json_blob(txt)
            if not blob:
                continue
            try:
                payload = json.loads(blob)
            except json.JSONDecodeError:
                continue

            user = {}
            if "entry_data" in payload:
                user = (
                    payload["entry_data"].get("ProfilePage", [{}])[0]
                    .get("graphql", {})
                    .get("user", {})
                )
            elif payload.get("data", {}).get("user"):
                user = payload["data"]["user"]

            if user:
                data.update(
                    {
                        "username": user.get("username"),
                        "full_name": user.get("full_name"),
                        "followers": user.get("edge_followed_by", {}).get("count"),
                        "following": user.get("edge_follow", {}).get("count"),
                        "posts": user.get("edge_owner_to_timeline_media", {}).get("count"),
                        "is_verified": user.get("is_verified"),
                        "biography": user.get("biography"),
                        "external_url": user.get("external_url"),
                    }
                )
                data.setdefault("raw", {})["graphql_user"] = user

    # 5) Fallback link scraping (bio anchors)
    data["bio_links"] = sorted(
        set(
            [data.get("external_url")] if data.get("external_url") else []
            + _extract_external_links_from_html(html)
        )
    )

    return {k: v for k, v in data.items() if v not in (None, [], "")}

################################################################################
# SCRAPE TARGET                                                                 
################################################################################

def scrape_target(target: str, session: requests.Session, rotator: ProxyRotator) -> Dict:
    target = target.strip()
    if not target:
        return {}

    # Local HTML file
    if Path(target).is_file() and target.lower().endswith(".html"):
        html = load_html_file(target)
        out = parse_profile_html(html)
        out["source"] = f"file://{Path(target).resolve()}"
        return out

    # Live fetch
    url = target if target.startswith("http") else f"https://www.instagram.com/{target.lstrip('@')}/"
    proxy = rotator.next()
    html = fetch_html(url, session, proxy)
    out = parse_profile_html(html)
    out.update({"url": url, "proxy": proxy})
    return out

################################################################################
# CLI                                                                           
################################################################################

def _load_list(arg: Union[str, Iterable[str], None]) -> List[str]:
    if arg is None:
        return []
    if isinstance(arg, (list, tuple, set)):
        return list(arg)
    if os.path.isfile(arg):
        with open(arg, "r", encoding="utf-8") as fh:
            return [ln.strip() for ln in fh if ln.strip()]
    return [arg]


def main(argv: Optional[List[str]] = None) -> None:
    p = argparse.ArgumentParser(description="Scrape or parse Instagram profile data to JSON")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--username", "-u")
    g.add_argument("--url")
    g.add_argument("--html")
    g.add_argument("--input", "-i", help="File with usernames/URLs/HTML paths or '-' for STDIN")

    p.add_argument("--proxy-list", "-p")
    p.add_argument("--cookie")
    p.add_argument("--user-agent", "--ua")
    p.add_argument("--pretty", action="store_true")

    a = p.parse_args(argv)

    targets = (
        [ln.strip() for ln in sys.stdin if ln.strip()] if a.input == "-" else _load_list(a.input)
        if a.input
        else [a.url] if a.url else [a.html] if a.html else [a.username]
    )

    rotator = ProxyRotator(_load_list(a.proxy_list))
    sess = requests.Session(); sess.headers.update(HEADERS_DEFAULT)
    if a.user_agent: sess.headers["User-Agent"] = a.user_agent
    if a.cookie: sess.headers["Cookie"] = a.cookie

    for tgt in targets:
        try:
            res = scrape_target(tgt, sess, rotator)
            print(json.dumps(res, indent=2 if a.pretty else None, ensure_ascii=False))
        except KeyboardInterrupt:
            break
        except Exception as exc:
            print(json.dumps({"target": tgt, "error": str(exc)}), file=sys.stderr)


if __name__ == "__main__":
    main()
