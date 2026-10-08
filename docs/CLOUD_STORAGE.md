# Cloudflare R2 & Image Storage Architecture

This guide details the optional cloud storage integration used by PHD Prof to extract, host, and render high-resolution architectural diagrams into Notion.

---

## 1. Why External Cloud Storage?

Notion's REST API enforces strict constraints on file uploads:
- File attachments sent directly via API blocks are restricted to 2 MB and frequently encounter upload timeouts or payload validation rejections.
- To maintain publication-quality slide notes, PHD Prof extracts diagrams at 300 DPI (often 400 KB–1.5 MB each).
- By hosting figures on an S3-compatible object store (such as Cloudflare R2), Notion blocks reference fast, persistent public CDN URLs (`type: "external"`), guaranteeing 100% reliability and zero bandwidth load on Notion servers.

---

## 2. Extraction & Upload Pipeline

```
[ PDF Slide ]
      │
      ▼
[ Gemini Vision ] ─── (Emits figure://slide_X?crop=ymin,xmin,ymax,xmax)
      │
      ▼
[ PyMuPDF 300 DPI ] ── (Crops high-res bitmap locally)
      │
      ▼
[ Deterministic SHA-256 ] ── (hash(doc_hash + slide_num + crop_box)[:16])
      │
      ▼
[ S3 / Cloudflare R2 ] ──── (Uploads to notion/universita/{course_slug}/{hash}.png)
      │
      ▼
[ Notion Block Builder ] ── (Renders native Notion "image" block with CDN URL)
```

### Deterministic Hashing & Idempotency
- Each figure is assigned a deterministic 16-character SHA-256 signature computed from `f"{doc_hash}_{slide_num}_{crop_sig}"`.
- **Pre-Upload HEAD Check**: Before performing extraction or upload, `S3ImageAdapter.image_exists()` queries Cloudflare R2 via an S3 `HEAD` request. If the image already exists remotely, both rendering and uploading are skipped instantly.
- **Local Staging Cache**: If the image exists on disk in `staging/figures/`, rendering is bypassed, saving CPU cycles.

---

## 3. Configuration via `.env`

Add your Cloudflare R2 credentials to `.env`:

```env
R2_ENDPOINT_URL=https://<account-id>.r2.cloudflarestorage.com
R2_ACCESS_KEY=<your-cloudflare-r2-access-key-id>
R2_SECRET_KEY=<your-cloudflare-r2-secret-access-key>
R2_BUCKET_NAME=phd-prof-assets
R2_PUBLIC_DOMAIN=https://pub-xxxxxx.r2.dev
```

*(Note: If any of these variables are omitted, PHD Prof gracefully continues without image extraction, replacing diagram markers with structured callouts).*

---

## 4. Duplicate Pruning Utility (`scripts/prune_r2_duplicates.py`)

During iterative runs or historical migrations, orphaned files or older non-deterministic UUIDs may accumulate in the bucket.

A dedicated pruning script is available in `scripts/`:

```bash
# Dry run: scans bucket and local staging, lists duplicates without deleting
python scripts/prune_r2_duplicates.py --course "Big Data"

# Execution mode: safely deletes orphaned duplicates from both R2 and local staging
python scripts/prune_r2_duplicates.py --course "Big Data" --delete
```
