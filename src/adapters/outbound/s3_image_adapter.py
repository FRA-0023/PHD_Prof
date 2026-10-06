import boto3
from botocore.exceptions import ClientError
from pathlib import Path
from src.ports.outbound.image_host_port import IImageHostClient

class S3ImageAdapter(IImageHostClient):
    """
    Adapter per caricare immagini su Cloudflare R2 o bucket AWS S3-compatibili.
    """
    def __init__(self, endpoint_url: str, access_key: str, secret_key: str, bucket_name: str, public_domain: str):
        self.bucket_name = bucket_name
        # Assicuriamo che public_domain finisca senza slash
        self.public_domain = public_domain.rstrip('/') if public_domain else ""
        
        self.s3 = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            # R2 usa una region vuota o auto, ma boto3 spesso richiede un valore fittizio
            region_name='auto' 
        )

    def upload_image(self, file_path: Path, object_name: str) -> str:
        """
        Esegue l'upload di un'immagine e restituisce l'URL finale offuscato.
        """
        try:
            mime_type = "image/png"
            if file_path.suffix.lower() in [".jpg", ".jpeg"]:
                mime_type = "image/jpeg"
                
            self.s3.upload_file(
                str(file_path),
                self.bucket_name,
                object_name,
                ExtraArgs={"ContentType": mime_type}
            )
            return f"{self.public_domain}/{object_name}"
        except ClientError as e:
            print(f"    [Cloudflare R2] Errore di caricamento per {object_name}: {e}")
            raise RuntimeError(f"Impossibile caricare l'immagine {object_name} su R2.") from e
