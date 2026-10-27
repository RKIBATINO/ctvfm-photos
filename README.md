# CTVFM Ambient Photos

Curated 1920×1080 background photography for the Smart TV screensaver and launcher, served from `photos/` with pre-calculated text-band brightness (`d`) in `photos/index.json` and full attribution in [`docs/PHOTO-CREDITS.md`](docs/PHOTO-CREDITS.md).

## Direct Raw URL Base (for TV Apps)

```text
https://raw.githubusercontent.com/<owner>/<repo>/main/photos/
```

- Index file: `https://raw.githubusercontent.com/<owner>/<repo>/main/photos/index.json`
- Photo file: `https://raw.githubusercontent.com/<owner>/<repo>/main/photos/<id>.jpg`

---

## 1. Repository Secret Setup (`UNSPLASH_ACCESS_KEY`)

1. Open your repository on GitHub and go to **Settings → Secrets and variables → Actions**.
2. Click **New repository secret**.
3. Set **Name** to `UNSPLASH_ACCESS_KEY`.
4. Paste your Unsplash Application **Access Key** into **Secret** and click **Add secret**.

---

## 2. How to Add New Photos via Unsplash Search

1. **Edit search queries (optional):**
   Update `queries.json` with any Moroccan cities, landmarks, or landscapes you want to search.
2. **Run Candidate Search:**
   - Either run locally:
     ```bash
     python tools/fetch_unsplash.py
     ```
   - Or on GitHub: go to **Actions → Fetch Unsplash candidates → Run workflow**. This saves small previews and `candidates.json` to the orphan branch `bg-unsplash` without bloating `main`.
3. **Add chosen entries to `picks.json`:**
   Copy the desired candidate object into `picks.json`:
   ```json
   {
     "n": 51,
     "id": "exampleId12",
     "by": "Photographer Name",
     "page": "https://unsplash.com/photos/exampleId12",
     "raw": "https://images.unsplash.com/photo-...",
     "desc": "Description of the landmark",
     "group": "architecture"
   }
   ```
4. **Download, Calculate Brightness (`d`), and Publish:**
   - On GitHub: go to **Actions → Fetch photos and build index → Run workflow**.
   - Or locally:
     ```bash
     python tools/fetch_photos.py
     python tools/make_index.py
     python tools/make_credits.py
     ```

---

## 3. How to Add Your Own Personal Photo

1. Crop/resize your photo to **1920×1080** JPEG (`q=82` recommended) and name it with ASCII letters, digits, hyphens, or underscores (e.g., `my-morocco-photo.jpg`).
2. Place the file inside the `photos/` folder.
3. Add an entry to `picks.json`:
   ```json
   {
     "n": 52,
     "id": "my-morocco-photo",
     "file": "my-morocco-photo.jpg",
     "by": "Owner",
     "credit": "Personal Archive",
     "page": "",
     "raw": "",
     "desc": "Custom photo",
     "group": "custom"
   }
   ```
4. Run `python tools/make_index.py` and `python tools/make_credits.py` to automatically compute the brightness factor `d` for its text bands and update `photos/index.json` and `docs/PHOTO-CREDITS.md`.
5. Commit and push `photos/my-morocco-photo.jpg`, `photos/index.json`, `picks.json`, and `docs/PHOTO-CREDITS.md` to `main`.
