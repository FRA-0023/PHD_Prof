# Cloudflare R2 & Image Storage Architecture

This guide provides a comprehensive, beginner-friendly walkthrough for configuring **Cloudflare R2** (an S3-compatible, zero-egress object storage service) to host and render high-resolution architectural diagrams extracted from academic slides directly into Notion.

---

## 1. Why External Cloud Storage?

Notion's REST API enforces strict constraints on direct image block creation:
- **File Attachment Limits**: Uploading binary image blobs directly via Notion's internal block upload endpoints is restricted to 2 MB, frequently suffers from socket write timeouts, and lacks CDN caching.
- **300 DPI High-Resolution Extraction**: Academic slide decks (equations, architecture diagrams, benchmark graphs) require high rendering fidelity (300 DPI, typically 400 KB–1.5 MB per cropped asset).
- **Public CDN Addressing**: By uploading extracted diagrams to Cloudflare R2 and referencing them via public CDN URLs (`type: "external"`), Notion embeds the images instantly without bandwidth load or payload validation rejections.
- **Zero Egress Fees**: Unlike AWS S3 or Google Cloud Storage, Cloudflare R2 charges **\$0.00 for outbound data egress**, making it ideal for continuous, high-volume academic image hosting on the generous free tier (10 GB storage, 10M read operations/month).

---

## 2. Diagram Extraction & Storage Pipeline

```
[ PDF Slide ]
      │
      ▼
[ Gemini Vision ] ─── (Identifies figures: figure://slide_X?crop=ymin,xmin,ymax,xmax)
      │
      ▼
[ PyMuPDF 300 DPI ] ── (Crops high-res bitmap locally)
      │
      ▼
[ Deterministic SHA-256 ] ── (hash(doc_hash + slide_num + crop_sig)[:16])
      │
      ▼
[ S3 / Cloudflare R2 ] ──── (Uploads to notion/universita/{course_slug}/{hash}.png)
      │
      ▼
[ Notion Block Builder ] ── (Renders native Notion "image" block with public CDN URL)
```

### Deterministic Fingerprinting & Skip Logic
- Each diagram is assigned a deterministic 16-character SHA-256 fingerprint computed from its document hash, slide number, and crop boundary coordinates.
- **Pre-Upload HEAD Check**: Before extracting or uploading, `S3ImageAdapter.image_exists()` issues an S3 `HEAD` request to Cloudflare R2. If the asset already exists remotely, the entire extraction and upload phase is bypassed in 0 ms.
- **Local Staging Cache**: If the file is already cached in `staging/figures/`, disk re-reading is avoided.

---

## 3. Step-by-Step Cloudflare R2 Setup (Beginner's Guide)

Follow these exact steps in the Cloudflare dashboard to obtain all required environment variables, even if you have never used Cloudflare before.

### Step 3.1: Log in and Access R2
1. Navigate to the [Cloudflare Dashboard](https://dash.cloudflare.com/) and log in (or create a free account).
2. In the left-hand navigation sidebar, click **Storage & Databases** $\rightarrow$ **R2** (or **R2 Object Storage**).
3. If prompted to activate R2 for the first time, click **Get Started** or **Purchase R2**.  
   *(Note: Cloudflare requires adding a payment method for identity verification, but includes 10 GB of storage and millions of requests per month 100% free; you will not be billed unless you exceed those limits).*

---

### Step 3.2: Create an R2 Bucket (`R2_BUCKET_NAME`)
1. In the R2 Overview page, click the blue button **"Create bucket"**.
2. **Bucket name**: Enter a unique lowercase identifier, for example: `phd-prof-assets`.
3. **Location**: Choose **Automatic** (or select a specific region close to your workstation, e.g. *Western Europe*).
4. Click **"Create bucket"**.
5. Save this name for your configuration:
   ```env
   R2_BUCKET_NAME=phd-prof-assets
   ```

---

### Step 3.3: Obtain S3 API Endpoint & Account ID (`R2_ENDPOINT_URL`)
1. From the bucket view, click on the **Settings** tab (or check the right-hand panel of the main R2 page under **Account details**).
2. Look for the card titled **Bucket Details** or **Account Details**.
3. Locate the entry named **S3 API**. It follows this exact format:
   ```
   https://<ACCOUNT_ID>.r2.cloudflarestorage.com
   ```
   *(Where `<ACCOUNT_ID>` is a 32-character hexadecimal string representing your Cloudflare account).*
4. Save this URL **without trailing slash and without the bucket name**:
   ```env
   R2_ENDPOINT_URL=https://<ACCOUNT_ID>.r2.cloudflarestorage.com
   ```

> [!WARNING]
> Do NOT append your bucket name to `R2_ENDPOINT_URL` (e.g. `...cloudflarestorage.com/phd-prof-assets` is **incorrect**). The S3 SDK automatically appends the bucket name to the base account endpoint.

---

### Step 3.4: Generate Access and Secret Keys (`R2_ACCESS_KEY` & `R2_SECRET_KEY`)
To allow PHD Prof to upload figures to your bucket, generate dedicated S3 credentials:

1. In the left navigation menu, return to the main **R2** page (under *Storage & Databases*).
2. In the right-hand sidebar under **Account details**, click **"Manage R2 API Tokens"** (or click the **Manage API Tokens** button near the top right).
3. Click the blue button **"Create API token"**.
4. Configure the token permissions:
   - **Token name**: Enter a descriptive name, e.g. `phd-prof-uploader`.
   - **Permissions**: Select **Object Read & Write** (this allows uploading images, checking existing assets via `HEAD`, and pruning duplicates).
   - **Specify bucket(s)**: Choose either **Apply to all buckets** or **Apply to specific buckets only** and select your newly created bucket (`phd-prof-assets`).
   - **TTL (Expiration)**: Leave as **Forever** (or set your desired expiration date).
   - **Client IP filtering**: Leave empty.
5. Click **"Create API Token"** at the bottom of the page.
6. Cloudflare will now display a secret credential confirmation screen:
   - **Access Key ID**: A 32-character hexadecimal string $\rightarrow$ maps to `R2_ACCESS_KEY`.
   - **Secret Access Key**: A 64-character alphanumeric string $\rightarrow$ maps to `R2_SECRET_KEY`.

> [!CAUTION]
> The **Secret Access Key** is displayed **ONLY ONCE**. If you close or refresh this tab without copying it, you cannot retrieve it and will need to generate a new token. Copy both values immediately into your local `.env`.

---

### Step 3.5: Enable Public Access (`R2_PUBLIC_DOMAIN`)
By default, all Cloudflare R2 buckets are private. If public access is not enabled, Notion will receive `403 Forbidden` errors when loading image blocks.

You have two options to enable public CDN delivery:

#### Option A: Free `r2.dev` Subdomain (Easiest & Recommended)
1. In the Cloudflare dashboard, navigate back to **R2** $\rightarrow$ click your bucket (`phd-prof-assets`).
2. Click the **"Settings"** tab at the top.
3. Scroll down to the **"Public access"** section.
4. Under the **R2.dev subdomain** card, click **"Allow Access"** (or **"Connect r2.dev"**).
5. A confirmation modal will appear warning that objects in the bucket will be publicly accessible. Type `allow` and confirm.
6. Cloudflare will generate a public domain URL in this format:
   ```
   https://pub-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.r2.dev
   ```
7. Copy this complete URL (including `https://` and without trailing slash):
   ```env
   R2_PUBLIC_DOMAIN=https://pub-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.r2.dev
   ```

#### Option B: Custom Domain (Optional Vanity URL)
If you manage a custom domain on Cloudflare (e.g. `yourdomain.com`):
1. In the same **Public access** section under bucket Settings, click **"Connect Domain"**.
2. Enter a subdomain, such as `assets.yourdomain.com`.
3. Cloudflare automatically sets up the DNS CNAME record and provisioned TLS certificate.
4. Set:
   ```env
   R2_PUBLIC_DOMAIN=https://assets.yourdomain.com
   ```

---

## 4. Environment Variables Reference Cheat Sheet

| `.env` Variable | Cloudflare UI Location | Example Format |
| :--- | :--- | :--- |
| `R2_ENDPOINT_URL` | R2 Overview $\rightarrow$ Account Details $\rightarrow$ S3 API | `https://a1b2c3d4e5f607182930415263748590.r2.cloudflarestorage.com` |
| `R2_ACCESS_KEY` | Manage R2 API Tokens $\rightarrow$ Access Key ID | `e4f5a6b7c8d90123456789abcdef0123` |
| `R2_SECRET_KEY` | Manage R2 API Tokens $\rightarrow$ Secret Access Key | `9876543210fedcba9876543210fedcba9876543210fedcba9876543210fedcba` |
| `R2_BUCKET_NAME` | Name specified when clicking "Create bucket" | `phd-prof-assets` |
| `R2_PUBLIC_DOMAIN` | Bucket Settings $\rightarrow$ Public Access $\rightarrow$ R2.dev subdomain | `https://pub-1234567890abcdef1234567890abcdef.r2.dev` |

### Complete `.env` Snippet

Add these five lines to your root `.env` file:

```env
# Cloudflare R2 / S3 Image Storage
R2_ENDPOINT_URL=https://a1b2c3d4e5f607182930415263748590.r2.cloudflarestorage.com
R2_ACCESS_KEY=e4f5a6b7c8d90123456789abcdef0123
R2_SECRET_KEY=9876543210fedcba9876543210fedcba9876543210fedcba9876543210fedcba
R2_BUCKET_NAME=phd-prof-assets
R2_PUBLIC_DOMAIN=https://pub-1234567890abcdef1234567890abcdef.r2.dev
```

*(Note: If any of these five variables are omitted or commented out, PHD Prof will continue processing slides without crashing, gracefully falling back to text callouts instead of diagram extraction).*

---

## 5. Verification & Connectivity Testing

To verify that your credentials, endpoint, and bucket permissions are working without processing an entire lecture:

Execute the duplicate audit utility in **dry-run mode**:

```bash
python scripts/prune_r2_duplicates.py --course "Big Data"
```

### Expected Successful Output:
```
Scanning remote objects on Cloudflare R2 with prefix: 'notion/universita/big_data/'...
Found 14 remote objects matching course 'Big Data'.
  -> Valid active assets: 14
  -> Orphaned/duplicate assets (legacy random UUIDs): 0

[DRY RUN] No remote objects deleted. Pass '--delete' to execute permanent deletion.
```

If your configuration is correct, the script connects via S3 API, lists existing keys, and prints the inventory in under a second.

---

## 6. Common Issues & Troubleshooting

| Error Symptom | Cause | Verified Fix |
| :--- | :--- | :--- |
| `[ERROR] Missing Cloudflare R2 credentials in .env` | One of the 5 variables is missing or blank in `.env`. | Ensure all 5 variables are uncommented in `.env`. |
| `ClientError: 403 Forbidden` during upload | Invalid `R2_ACCESS_KEY` or `R2_SECRET_KEY`, or token lacks Write permission. | Regenerate a token with **Object Read & Write** permissions under *Manage R2 API Tokens*. |
| `ClientError: 404 NoSuchBucket` | The bucket name in `.env` does not match the name created in Cloudflare. | Verify spelling in `R2_BUCKET_NAME` against the Cloudflare bucket list. |
| Broken image icons in Notion | `R2_PUBLIC_DOMAIN` is not set or bucket public access is disabled. | In Cloudflare bucket Settings, enable **R2.dev subdomain** access and paste the public URL into `R2_PUBLIC_DOMAIN`. |
| `EndpointConnectionError` | `R2_ENDPOINT_URL` has trailing paths (e.g. includes bucket name) or lacks `https://`. | Set `R2_ENDPOINT_URL=https://<ACCOUNT_ID>.r2.cloudflarestorage.com` without any trailing slashes. |

---

## 7. Storage Maintenance & Pruning Utility

Over time or during testing, legacy or orphaned assets might remain in the bucket. The maintenance utility [`scripts/prune_r2_duplicates.py`](file:///scripts/prune_r2_duplicates.py) safely cleans up obsolete assets:

```bash
# 1. Audit current storage (dry-run, no changes made)
python scripts/prune_r2_duplicates.py --course "Big Data"

# 2. Safely purge orphaned images from both Cloudflare R2 and local staging/figures
python scripts/prune_r2_duplicates.py --course "Big Data" --delete
```
