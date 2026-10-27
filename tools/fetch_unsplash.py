#!/usr/bin/env python3
"""Search Unsplash for Moroccan landscapes and architecture via the official API.
Reads search queries from queries.json and UNSPLASH_ACCESS_KEY from the environment.
Writes unsplash/NN.jpg small previews and unsplash/candidates.json."""
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

KEY = os.environ.get("UNSPLASH_ACCESS_KEY", "").strip()
UA = {
    "User-Agent": "ctvfm-photo-picker/1.0",
    "Accept-Version": "v1",
    "Authorization": "Client-ID " + KEY,
}
MIN_REMAINING_QUOTA = 5

MOROCCO_KEYWORDS = (
    "morocco", "maroc", "marrakech", "marrakesh", "chefchaouen", "chaouen",
    "merzouga", "erg chebbi", "sahara", "atlas", "toubkal", "essaouira",
    "mogador", "fes", "fez", "casablanca", "hassan ii", "ait benhaddou",
    "ait ben haddou", "ouarzazate", "rabat", "tangier", "tanger", "agadir",
    "taghazout", "ouzoud", "meknes", "tetouan", "asilah", "dakhla", "ifrane",
    "todra", "dades", "zagora", "taroudant", "moroccan", "zellij", "riad"
)

FOREIGN_KEYWORDS = (
    "saudi", "riyadh", "jeddah", "alula", "neom", "dubai", "uae", "abu dhabi",
    "egypt", "cairo", "jordan", "petra", "wadi rum", "oman", "turkey", "istanbul",
    "spain", "granada", "sevilla", "cordoba", "india", "rajasthan", "iran",
    "uzbekistan", "california", "arizona", "namibia"
)


def api_get(url, raw=False):
    time.sleep(1.2)
    req = urllib.request.Request(url, headers=UA if not raw else {"User-Agent": UA["User-Agent"]})
    with urllib.request.urlopen(req, timeout=60) as r:
        rem = r.headers.get("X-Ratelimit-Remaining")
        if rem is not None:
            rem_int = int(rem)
            print(f"  [API quota remaining: {rem_int}]")
            if rem_int <= MIN_REMAINING_QUOTA:
                raise RuntimeError(f"Rate limit threshold reached ({rem_int} remaining). Stopping safely.")
        return r.read() if raw else json.load(r)


def evaluate_location(photo, query_str):
    loc = photo.get("location") or {}
    country = (loc.get("country") or "").strip()
    city = (loc.get("city") or "").strip()
    loc_name = (loc.get("name") or "").strip()
    desc = (photo.get("description") or "").strip()
    alt = (photo.get("alt_description") or "").strip()
    tags_list = [t.get("title", "") for t in (photo.get("tags") or []) if isinstance(t, dict)]
    blob = " ".join([country, city, loc_name, desc, alt, " ".join(tags_list)]).lower()

    suspect = False
    suspect_reason = ""

    if country:
        if country.lower() not in ("morocco", "maroc", "المغرب"):
            suspect = True
            suspect_reason = f"location.country is '{country}'"
    else:
        for fk in FOREIGN_KEYWORDS:
            if re.search(r"\b" + re.escape(fk) + r"\b", blob):
                suspect = True
                suspect_reason = f"mentions non-Moroccan place '{fk}'"
                break
        if not suspect and not any(mk in blob for mk in MOROCCO_KEYWORDS):
            suspect = True
            suspect_reason = "no explicit Moroccan location or keyword in metadata"

    return {
        "country": country,
        "city": city,
        "location_name": loc_name,
        "suspect": suspect,
        "suspect_reason": suspect_reason,
    }


def load_queries():
    qfile = Path("queries.json")
    if qfile.exists():
        return json.loads(qfile.read_text(encoding="utf-8"))
    return [{"query": "Morocco landscape", "group": "landscape", "pages": 1}]


def main():
    if not KEY:
        raise SystemExit("UNSPLASH_ACCESS_KEY environment variable is not set")

    queries = load_queries()
    out, seen = [], set()

    for item in queries:
        q = item["query"] if isinstance(item, dict) else str(item)
        group = item.get("group", "general") if isinstance(item, dict) else "general"
        pages = int(item.get("pages", 1)) if isinstance(item, dict) else 1

        for page in range(1, pages + 1):
            print(f"Searching '{q}' (page {page}/{pages})...")
            try:
                params = urllib.parse.urlencode({
                    "query": q,
                    "per_page": 30,
                    "page": page,
                    "orientation": "landscape",
                    "content_filter": "high",
                })
                d = api_get("https://api.unsplash.com/search/photos?" + params)
            except RuntimeError as quota_err:
                print(quota_err)
                break
            except urllib.error.HTTPError as e:
                print(f"HTTP error on '{q}': {e.code}")
                if e.code in (403, 429):
                    print("Rate limit or permission error reached; stopping search.")
                    break
                continue
            except Exception as e:
                print(f"Search failed for '{q}': {e}")
                break

            for p in d.get("results", []):
                pid = p.get("id")
                w = p.get("width", 0)
                h = p.get("height", 1)
                if not pid or pid in seen or w < 3000:
                    continue
                if w < h * 1.3:
                    continue
                seen.add(pid)
                loc_info = evaluate_location(p, q)
                desc_text = (p.get("alt_description") or p.get("description") or "").replace("\n", " ").strip()[:140]
                out.append({
                    "id": pid,
                    "query": q,
                    "group": group,
                    "w": w,
                    "h": h,
                    "likes": p.get("likes", 0),
                    "desc": desc_text,
                    "by": p.get("user", {}).get("name", "Unknown"),
                    "username": p.get("user", {}).get("username", ""),
                    "page": p.get("links", {}).get("html", f"https://unsplash.com/photos/{pid}"),
                    "raw": p.get("urls", {}).get("raw", ""),
                    "small": p.get("urls", {}).get("small", ""),
                    "download_location": p.get("links", {}).get("download_location", ""),
                    "country": loc_info["country"],
                    "city": loc_info["city"],
                    "location_name": loc_info["location_name"],
                    "suspect": loc_info["suspect"],
                    "suspect_reason": loc_info["suspect_reason"],
                })

    # Sort clean candidates first by likes descending, then suspect ones at the end
    out.sort(key=lambda x: (1 if x["suspect"] else 0, -x["likes"]))
    out = out[:96]

    out_dir = Path("unsplash")
    out_dir.mkdir(exist_ok=True)
    for i, p in enumerate(out):
        fname = f"{i:02d}.jpg"
        fpath = out_dir / fname
        try:
            if not fpath.exists():
                fpath.write_bytes(api_get(p["small"], raw=True))
            p["file"] = fname
        except Exception as e:
            print("skip preview", p["id"], e)

    (out_dir / "candidates.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    clean_count = sum(1 for x in out if not x["suspect"])
    print(f"Saved {len(out)} candidates ({clean_count} verified/clean, {len(out) - clean_count} flagged suspect).")


if __name__ == "__main__":
    main()
