"""
scripts/generate_certificates.py
--------------------------------
Generates a trusted local Root Certificate Authority (CA) and an SSL/TLS
server certificate for PHD Prof (covering phdprof.test, localhost, and 127.0.0.1).
Adheres strictly to RFC 5280 and modern browser TLS requirements.
"""
import os
import sys
import datetime
import ipaddress
import pathlib
import argparse

from cryptography import x509
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

def generate_certificates(cert_dir: pathlib.Path, domain: str = "phdprof.test", force: bool = False) -> None:
    cert_dir.mkdir(parents=True, exist_ok=True)

    ca_key_path = cert_dir / "ca.key"
    ca_crt_path = cert_dir / "ca.crt"
    server_key_path = cert_dir / "server.key"
    server_crt_path = cert_dir / "server.crt"

    if not force and all(p.exists() for p in (ca_key_path, ca_crt_path, server_key_path, server_crt_path)):
        print(f"[OK] I certificati SSL per '{domain}' esistono gia' in: {cert_dir}")
        return

    now = datetime.datetime.now(datetime.timezone.utc)

    # 1. Generate Local Root CA
    print("[*] Generazione della Root CA locale 'PHD Prof Local CA'...")
    ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    ca_name = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "IT"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "PHD Prof"),
        x509.NameAttribute(NameOID.COMMON_NAME, "PHD Prof Local Root CA"),
    ])

    ca_cert = (
        x509.CertificateBuilder()
        .subject_name(ca_name)
        .issuer_name(ca_name)
        .public_key(ca_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(days=1))
        .not_valid_after(now + datetime.timedelta(days=3650))  # 10 years
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_cert_sign=True,
                crl_sign=True,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .add_extension(x509.SubjectKeyIdentifier.from_public_key(ca_key.public_key()), critical=False)
        .sign(ca_key, hashes.SHA256())
    )

    # 2. Generate Server Certificate
    print(f"[*] Generazione del certificato SSL per '{domain}', 'localhost' e '127.0.0.1'...")
    server_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    server_name = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "IT"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "PHD Prof"),
        x509.NameAttribute(NameOID.COMMON_NAME, domain),
    ])

    san_entries = [
        x509.DNSName(domain),
        x509.DNSName(f"*.{domain}"),
        x509.DNSName("localhost"),
        x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
    ]

    server_cert = (
        x509.CertificateBuilder()
        .subject_name(server_name)
        .issuer_name(ca_name)
        .public_key(server_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(days=1))
        .not_valid_after(now + datetime.timedelta(days=730))  # 2 years
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_encipherment=True,
                content_commitment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .add_extension(
            x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]),
            critical=False,
        )
        .add_extension(
            x509.SubjectAlternativeName(san_entries),
            critical=False,
        )
        .add_extension(x509.SubjectKeyIdentifier.from_public_key(server_key.public_key()), critical=False)
        .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()), critical=False)
        .sign(ca_key, hashes.SHA256())
    )

    # 3. Write outputs
    ca_key_path.write_bytes(
        ca_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    ca_crt_path.write_bytes(ca_cert.public_bytes(serialization.Encoding.PEM))

    server_key_path.write_bytes(
        server_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    # Write full chain: server cert + ca cert
    server_crt_path.write_bytes(
        server_cert.public_bytes(serialization.Encoding.PEM) +
        ca_cert.public_bytes(serialization.Encoding.PEM)
    )

    print(f"[OK] Certificati generati con successo in:\n     {cert_dir.resolve()}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate local TLS/SSL certificates for PHD Prof")
    parser.add_argument("--domain", default="phdprof.test", help="Domain name (default: phdprof.test)")
    parser.add_argument("--force", action="store_true", help="Force regeneration of existing certificates")
    args = parser.parse_args()

    project_root = pathlib.Path(__file__).parent.parent
    certs_directory = project_root / "certs"
    generate_certificates(certs_directory, domain=args.domain, force=args.force)
