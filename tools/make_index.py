#!/usr/bin/env python3
"""Generate photos/index.json with fields {"f", "c", "d"} from picks.json and photos/<id>.jpg.
Computes per-photo brightness factor d in [0.72, 1.00] from the luminance of the top (33%)
and bottom (25%) text bands on screen using Pillow:
    m = max(mean_luminance(top_33%), mean_luminance(bottom_25%)) / 255.0
    d = round(clamp(1.226 - 0.638 * m, 0.72, 1.00), 2)
"""
import argparse
import json
from pathlib import Path
from PIL import Image, ImageStat


def compute_d(image_path: Path) -> float:
    with Image.open(image_path) as img:
        gray = img.convert("L")
        w, h = gray.size
        top_band = gray.crop((0, 0, w, int(h * 0.33)))
        bot_band = gray.crop((0, int(h * 0.75), w, h))
        mean_top = ImageStat.Stat(top_band).mean[0] / 255.0
        mean_bot = ImageStat.Stat(bot_band).mean[0] / 255.0
        m = max(mean_top, mean_bot)
        d = max(0.72, min(1.00, 1.226 - 0.638 * m))
        return round(d, 2)


def build_index(picks_path: Path, photos_dir: Path, out_path: Path):
    picks = json.loads(picks_path.read_text(encoding="utf-8"))
    entries = []
    seen = set()

    for p in picks:
        pid = p["id"]
        fname = p.get("file") or f"{pid}.jpg"
        if fname in seen:
            continue
        fpath = photos_dir / fname
        if not fpath.exists():
            print(f"Warning: skipping {fname} (file not found in {photos_dir})")
            continue
        seen.add(fname)
        by = p.get("by", "Unknown").strip()
        credit = p.get("credit") or f"{by} · Unsplash"
        d = compute_d(fpath)
        entries.append({
            "f": fname,
            "c": credit,
            "d": d,
        })

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(entries, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"Wrote {len(entries)} entries to {out_path}")


def calibrate(photos_dir: Path, orig_index_path: Path):
    orig = [p for p in json.loads(orig_index_path.read_text(encoding="utf-8")) if not p["f"].startswith("morocco_")]
    exact = 0
    diffs = []
    for p in orig:
        fpath = photos_dir / p["f"]
        if not fpath.exists():
            continue
        calc_d = compute_d(fpath)
        orig_d = p["d"]
        if calc_d == orig_d:
            exact += 1
        else:
            diffs.append((p["f"], orig_d, calc_d, round(calc_d - orig_d, 2)))

    print(f"Calibration on {len(orig)} photos: {exact}/{len(orig)} exact matches (0.00 diff).")
    if diffs:
        print("Differences found:")
        for fname, od, cd, delta in diffs:
            print(f"  {fname}: original={od:.2f}, calculated={cd:.2f} (diff={delta:+.2f})")


def main():
    parser = argparse.ArgumentParser(description="Generate photos/index.json from picks.json and photos/")
    parser.add_argument("--picks", default="picks.json", help="Path to picks.json")
    parser.add_argument("--photos", default="photos", help="Directory containing 1920x1080 .jpg files")
    parser.add_argument("--out", default="photos/index.json", help="Output index.json path")
    parser.add_argument("--calibrate", help="Compare calculated d against an existing index.json")
    args = parser.parse_args()

    if args.calibrate:
        calibrate(Path(args.photos), Path(args.calibrate))
    else:
        build_index(Path(args.picks), Path(args.photos), Path(args.out))


if __name__ == "__main__":
    main()
