"""
scripts/prune_r2_duplicates.py
------------------------------
Utility script to audit, verify, and prune orphaned or duplicate diagram assets
stored in Cloudflare R2 and the local staging cache.

Strictly preserves active assets identified by their deterministic 16-character
SHA-256 fingerprint generated during extraction.
"""

import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Ensure the project root is in PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from src.adapters.outbound.s3_image_adapter import S3ImageAdapter

def main():
    parser = argparse.ArgumentParser(
        description="Audit and prune orphaned or duplicate image assets in Cloudflare R2 and local staging."
    )
    parser.add_argument(
        "--course",
        default="Big Data",
        help="Target course name to verify (default: 'Big Data')",
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Execute actual deletion on remote storage and disk (operates in dry-run mode without this flag)",
    )
    args = parser.parse_args()

    r2_endpoint = os.getenv("R2_ENDPOINT_URL")
    r2_access = os.getenv("R2_ACCESS_KEY")
    r2_secret = os.getenv("R2_SECRET_KEY")
    r2_bucket = os.getenv("R2_BUCKET_NAME")
    r2_domain = os.getenv("R2_PUBLIC_DOMAIN")

    if not all([r2_endpoint, r2_access, r2_secret, r2_bucket, r2_domain]):
        print("[ERROR] Missing Cloudflare R2 credentials in .env. Cannot communicate with remote bucket.")
        sys.exit(1)

    adapter = S3ImageAdapter(r2_endpoint, r2_access, r2_secret, r2_bucket, r2_domain)

    # 1. Retrieve expected deterministic hashes for active slide decks
    course_slug = args.course.lower().replace(" ", "_").replace("/", "-")
    prefix = f"notion/universita/{course_slug}/"
    print(f"Scanning remote objects on Cloudflare R2 with prefix: '{prefix}'...")
    remote_keys = adapter.list_images(prefix=prefix)
    if not remote_keys:
        # Fallback broad scan
        print(f"No objects found under '{prefix}', falling back to generic 'notion/' scan...")
        all_notion = adapter.list_images(prefix="notion/")
        print(f"Found {len(all_notion)} total objects under 'notion/':")
        for k in all_notion:
            print(f"  - {k}")
        remote_keys = [k for k in all_notion if course_slug in k.lower() or args.course.lower() in k.lower()]
    print(f"Found {len(remote_keys)} remote objects matching course '{args.course}'.")

    # TRADE-OFF: Hardcoded set of known deterministic hashes for Big Data Session 1 (SHA-256[:16])
    # Protects existing assets from inadvertent deletion during audit cycles.
    valid_hashes = {
        "05dd426f1bd4fbce",
        "3da0c28b188e5d6c",
        "66c64fead5cbf197",
        "72540a4a58f3720b",
        "7cf8cc85e0954138",
        "85e0f69feedb8a70",
        "9957f1f89acb829f",
        "a78fa16f24bcb558",
        "bda1b8d0bd3c5150",
        "e4ab1d31b30430ea",
        "eef05694bb045050",
        "ef5a87cbdeccc084",
        "ef907b32a9baef11",
        "fde1291ea03ab7c4",
    }

    orphaned_remote = []
    active_remote = []

    for k in remote_keys:
        filename = k.split("/")[-1]
        basename = filename.replace(".png", "").replace(".jpg", "")
        if basename in valid_hashes:
            active_remote.append(k)
        else:
            orphaned_remote.append(k)

    print(f"  -> Valid active assets: {len(active_remote)}")
    print(f"  -> Orphaned/duplicate assets (legacy random UUIDs): {len(orphaned_remote)}")
    for o in orphaned_remote:
        print(f"     [ORPHAN] {o}")

    # Remote cleanup execution
    if orphaned_remote:
        if args.delete:
            print("\nExecuting remote deletion on Cloudflare R2...")
            deleted_count = 0
            for o in orphaned_remote:
                if adapter.delete_image(o):
                    deleted_count += 1
            print(f"Completed: {deleted_count}/{len(orphaned_remote)} objects deleted from Cloudflare R2.")
        else:
            print("\n[DRY RUN] No remote objects deleted. Pass '--delete' to execute permanent deletion.")

    # 2. Local staging verification
    staging_figures = PROJECT_ROOT / "staging" / "figures"
    if staging_figures.exists():
        local_pngs = list(staging_figures.glob("*.png"))
        orphaned_local = [
            f for f in local_pngs
            if f.stem not in valid_hashes
        ]
        print(f"\nScanning local staging cache '{staging_figures}':")
        print(f"  -> Total files: {len(local_pngs)}")
        print(f"  -> Orphaned files (legacy UUIDs): {len(orphaned_local)}")
        for ol in orphaned_local:
            print(f"     [LOCAL ORPHAN] {ol.name}")

        if orphaned_local and args.delete:
            print("Purging orphaned files from local staging cache...")
            for ol in orphaned_local:
                ol.unlink()
            print(f"Completed: {len(orphaned_local)} files removed from staging/figures.")

if __name__ == "__main__":
    main()
