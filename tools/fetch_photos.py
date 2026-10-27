#!/usr/bin/env python3
"""Download the chosen Unsplash photos (picks.json) cropped to 1920x1080 by Unsplash's
image service (w=1920&h=1080&fit=crop&crop=entropy&q=82&fm=jpg), and register each download
via the Unsplash /download endpoint as required by the API guidelines.
Skips existing files, retries transient errors, and stops safely before rate-limit exhaustion."""
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

KEY = os.environ.get("UNSPLASH_ACCESS_KEY", "").strip()
UA_API = {
    "User-Agent": "ctvfm-photo-fetcher/1.0",
    "Accept-Version": "v1",
    "Authorization": "Client-ID " + KEY,
}
UA_CDN = {"User-Agent": "ctvfm-photo-fetcher/1.0"}
CROP_PARAMS = "w=1920&h=1080&fit=crop&crop=entropy&q=82&fm=jpg"
MIN_REMAINING_QUOTA = 3


def fetch_with_retry(url, headers, retries=3, timeout=120):
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            time.sleep(1.0 * attempt)
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read(), r.headers
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code in (403, 429):
                raise
            print(f"  HTTP {e.code} on attempt {attempt}/{retries} for {url[:60]}...")
        except Exception as e:
            last_err = e
            print(f"  Error on attempt {attempt}/{retries}: {e}")
    raise last_err


def trigger_download(item):
    if not KEY:
        return None
    dl_url = item.get("download_location") or f"https://api.unsplash.com/photos/{item['id']}/download"
    _, headers = fetch_with_retry(dl_url, UA_API, retries=2, timeout=30)
    rem = headers.get("X-Ratelimit-Remaining")
    return int(rem) if rem is not None else None


def main():
    picks_path = Path("picks.json")
    if not picks_path.exists():
        raise SystemExit("picks.json not found")

    picks = json.loads(picks_path.read_text(encoding="utf-8"))
    out = Path("photos")
    out.mkdir(exist_ok=True)

    downloaded = 0
    skipped = 0

    for p in picks:
        pid = p["id"]
        f = out / f"{pid}.jpg"
        if f.exists() and f.stat().st_size > 10000:
            skipped += 1
            continue

        # 1. Check / trigger Unsplash download endpoint first (if KEY is set) so we respect rate limits
        if KEY:
            try:
                rem = trigger_download(p)
            except urllib.error.HTTPError as e:
                if e.code in (403, 429):
                    print(f"Rate limit reached (HTTP {e.code}) before downloading {pid}. Stopping safely.")
                    break
                rem = None
            except Exception as e:
                print(f"Warning: download tracking failed for {pid}: {e}")
                rem = None
        else:
            rem = None

        # 2. Download the 1920x1080 cropped image from images.unsplash.com CDN
        raw_url = p["raw"]
        sep = "&" if "?" in raw_url else "?"
        img_url = raw_url + sep + CROP_PARAMS
        try:
            data, _ = fetch_with_retry(img_url, UA_CDN, retries=3, timeout=120)
            f.write_bytes(data)
            downloaded += 1
            quota_str = f" (API quota remaining: {rem})" if rem is not None else ""
            print(f"ok {pid} ({len(data) // 1024} KB){quota_str}")
        except Exception as e:
            print(f"FAILED to download {pid}: {e}")
            continue

        if rem is not None and rem <= MIN_REMAINING_QUOTA:
            print(f"API quota low ({rem} remaining <= {MIN_REMAINING_QUOTA}). Stopping safely; re-run next hour to continue.")
            break

    print(f"Done: {downloaded} downloaded, {skipped} already present, {len(picks)} total in picks.json.")


if __name__ == "__main__":
    main()
