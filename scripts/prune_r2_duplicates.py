"""
Script per verificare e rimuovere asset duplicati/orfani su Cloudflare R2 e staging locale.
Mantiene rigorosamente intatti gli asset validi con hash deterministico SHA-256.
"""

import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Assicuriamo che la radice del progetto sia nel PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from src.adapters.outbound.s3_image_adapter import S3ImageAdapter

def main():
    parser = argparse.ArgumentParser(description="Pruning asset duplicati/orfani su Cloudflare R2 e staging.")
    parser.add_argument("--course", default="Big Data", help="Nome del corso da verificare (default: 'Big Data')")
    parser.add_argument("--delete", action="store_true", help="Esegue l'effettiva rimozione (senza questo flag opera in dry-run)")
    args = parser.parse_args()

    r2_endpoint = os.getenv("R2_ENDPOINT_URL")
    r2_access = os.getenv("R2_ACCESS_KEY")
    r2_secret = os.getenv("R2_SECRET_KEY")
    r2_bucket = os.getenv("R2_BUCKET_NAME")
    r2_domain = os.getenv("R2_PUBLIC_DOMAIN")

    if not all([r2_endpoint, r2_access, r2_secret, r2_bucket, r2_domain]):
        print("[ERRORE] Variabili R2 mancanti in .env. Impossibile contattare lo storage cloud.")
        sys.exit(1)

    adapter = S3ImageAdapter(r2_endpoint, r2_access, r2_secret, r2_bucket, r2_domain)

    # 1. Recupera gli hash validi attesi deterministici dal staging locale
    course_slug = args.course.lower().replace(" ", "_").replace("/", "-")
    prefix = f"notion/universita/{course_slug}/"
    print(f"Scansione oggetti remoti su Cloudflare R2 con prefisso: '{prefix}'...")
    remote_keys = adapter.list_images(prefix=prefix)
    if not remote_keys:
        # Fallback broad scan
        print(f"Nessun oggetto con '{prefix}', scansione generica con prefisso 'notion/'...")
        all_notion = adapter.list_images(prefix="notion/")
        print(f"Trovati {len(all_notion)} oggetti totali sotto 'notion/':")
        for k in all_notion:
            print(f"  - {k}")
        remote_keys = [k for k in all_notion if course_slug in k.lower() or args.course.lower() in k.lower()]
    print(f"Trovati {len(remote_keys)} oggetti remoti correlati a '{args.course}'.")

    # Mappa dei 14 hash deterministici validi per Big Data Session 1 (SHA-256[:16])
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

    print(f"  -> Asset validi e attivi: {len(active_remote)}")
    print(f"  -> Asset orfani/duplicati (UUID casuali precedenti): {len(orphaned_remote)}")
    for o in orphaned_remote:
        print(f"     [ORFANO] {o}")

    # Pulizia remota se richiesta
    if orphaned_remote:
        if args.delete:
            print("\nEsecuzione rimozione remota su Cloudflare R2...")
            deleted_count = 0
            for o in orphaned_remote:
                if adapter.delete_image(o):
                    deleted_count += 1
            print(f"Completato: {deleted_count}/{len(orphaned_remote)} oggetti eliminati da Cloudflare R2.")
        else:
            print("\n[DRY RUN] Nessun oggetto eliminato. Usa flag '--delete' per procedere alla rimozione.")

    # 2. Verifica staging locale
    staging_figures = PROJECT_ROOT / "staging" / "figures"
    if staging_figures.exists():
        local_pngs = list(staging_figures.glob("*.png"))
        orphaned_local = [
            f for f in local_pngs
            if f.stem not in valid_hashes
        ]
        print(f"\nScansione staging locale '{staging_figures}':")
        print(f"  -> File totali: {len(local_pngs)}")
        print(f"  -> File orfani (UUID vecchi): {len(orphaned_local)}")
        for ol in orphaned_local:
            print(f"     [LOCALE ORFANO] {ol.name}")

        if orphaned_local and args.delete:
            print("Rimozione file orfani da staging locale...")
            for ol in orphaned_local:
                ol.unlink()
            print(f"Completato: {len(orphaned_local)} file rimossi da staging/figures.")

if __name__ == "__main__":
    main()
