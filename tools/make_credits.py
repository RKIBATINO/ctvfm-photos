#!/usr/bin/env python3
"""Generate docs/PHOTO-CREDITS.md from picks.json in the exact upstream table format."""
import argparse
import json
from pathlib import Path

UTM = "?utm_source=ctvfm_tv_screensaver&utm_medium=referral"


def with_utm(url: str) -> str:
    if not url or "unsplash.com" not in url or "utm_source=" in url:
        return url
    sep = "&" if "?" in url else "?"
    return url + sep + "utm_source=ctvfm_tv_screensaver&utm_medium=referral"


def generate_credits(picks_path: Path, out_path: Path):
    picks = json.loads(picks_path.read_text(encoding="utf-8"))
    bundled = [p for p in picks if p.get("bundled")]
    if not bundled:
        bundled = picks[:5]

    lines = [
        "# Photo credits",
        "",
        "The photos are not credited on screen; they are credited here.",
        "",
    ]

    if bundled:
        bundled_str = " ".join(f"`{p.get('file') or (p['id'] + '.jpg')}`" for p in bundled)
        lines.extend([
            "## Bundled with the apps (offline fallback)",
            "",
            "Five of the hosted photos below, copied into `assets/backgrounds/`:",
            bundled_str,
            "",
        ])

    lines.extend([
        "## Hosted set (`photos/`)",
        "",
        f"From [Unsplash](https://unsplash.com/{UTM}), under the [Unsplash License](https://unsplash.com/license).",
        "",
        "| File | Photographer | Source |",
        "|---|---|---|",
    ])

    for p in picks:
        fname = p.get("file") or f"{p['id']}.jpg"
        by = p.get("by", "Unknown").replace("|", "-")
        page = with_utm(p.get("page", f"https://unsplash.com/photos/{p['id']}"))
        lines.append(f"| `photos/{fname}` | {by} | [unsplash]({page}) |")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {len(picks)} photo credits to {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate docs/PHOTO-CREDITS.md from picks.json")
    parser.add_argument("--picks", default="picks.json", help="Path to picks.json")
    parser.add_argument("--out", default="docs/PHOTO-CREDITS.md", help="Output markdown path")
    args = parser.parse_args()
    generate_credits(Path(args.picks), Path(args.out))


if __name__ == "__main__":
    main()
