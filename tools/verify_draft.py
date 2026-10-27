import json
import re
from pathlib import Path
from PIL import Image

draft_dir = Path('C:/Users/MGM/Desktop/ctvfm-photos-draft')
index_path = draft_dir / 'photos' / 'index.json'
credits_path = draft_dir / 'docs' / 'PHOTO-CREDITS.md'
picks_path = draft_dir / 'picks.json'
photos_dir = draft_dir / 'photos'

idx = json.load(open(index_path, encoding='utf-8'))
picks = json.load(open(picks_path, encoding='utf-8'))
credits_txt = credits_path.read_text(encoding='utf-8')

print('=== Test 1: Count check ===')
photo_count = len(list(photos_dir.glob('*.jpg')))
print(f'index.json: {len(idx)}, picks.json: {len(picks)}, photos on disk: {photo_count}')
assert len(idx) == 47 and len(picks) == 47 and photo_count == 47, 'Counts mismatch!'

print('\n=== Test 2: Filename pattern, format, and dimensions ===')
name_pat = re.compile(r'^[A-Za-z0-9_-]+\.jpg$')
filenames = [p['f'] for p in idx]
assert len(filenames) == len(set(filenames)), 'Duplicate filenames found in index.json!'
for fn in filenames:
    assert name_pat.match(fn), f'Invalid filename: {fn}'
    fpath = photos_dir / fn
    assert fpath.exists(), f'File does not exist on disk: {fn}'
    with Image.open(fpath) as img:
        assert img.size == (1920, 1080), f'Bad size for {fn}: {img.size}'
        assert img.format == 'JPEG', f'Bad format for {fn}: {img.format}'

print('All 47 filenames valid, unique, exist on disk, 1920x1080 JPEG.')

print('\n=== Test 3: Credits coverage ===')
for p in idx:
    assert p['c'], f"Missing credit in index.json for {p['f']}"
    assert f"`photos/{p['f']}`" in credits_txt, f"Missing in PHOTO-CREDITS.md: {p['f']}"

print('All 47 photos have credits in both index.json and PHOTO-CREDITS.md.')

print('\n=== Test 4: Field types and brightness range ===')
d_values = []
for p in idx:
    assert set(p.keys()) == {'f', 'c', 'd'}, f'Unexpected keys in index entry: {p}'
    assert isinstance(p['f'], str) and isinstance(p['c'], str) and isinstance(p['d'], (int, float))
    assert 0.72 <= p['d'] <= 1.00, f"d out of range [0.72, 1.00]: {p['d']} in {p['f']}"
    d_values.append(p['d'])

print(f'd range: min={min(d_values):.2f}, max={max(d_values):.2f}, avg={sum(d_values)/len(d_values):.2f}')

print('\n=== Test 5: photoSet simulation (screensaver / launcher PRNG) ===')
def photoSet(n, period):
    seed = (period % 2147483646) + 1
    pick = []
    for _ in range(1000):
        if len(pick) == min(5, n):
            break
        seed = (seed * 48271) % 2147483647
        k = seed % n
        if k not in pick:
            pick.append(k)
    return pick

for period in range(100):
    selected = photoSet(len(idx), period)
    assert len(selected) == 5, f'photoSet failed to pick 5 items in period {period}'
    for idx_num in selected:
        assert 0 <= idx_num < len(idx)

print('Simulated 100 4-day periods of photoSet: always picks 5 valid unique photos.')
print('\n>>> ALL 5 TEST SUITES PASSED SUCCESSFULLY (100% OK) <<<')
