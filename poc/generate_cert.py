"""Self-signed TLS sertifikasi olustur (HTTPS / mobil PWA testi icin).

Cikti:
  poc/certs/server.key
  poc/certs/server.crt

LAN IP'sini de SAN'a (Subject Alternative Names) ekler ki telefon
192.168.x.y:8765 ile baglanabilsin.

Kullanim:
    python generate_cert.py [--ip 192.168.1.164]
"""

from __future__ import annotations

import argparse
import datetime as dt
import ipaddress
import socket
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

OUT_DIR = Path(__file__).parent / "certs"


def detect_lan_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", default=None, help="LAN IP (default: otomatik tespit)")
    parser.add_argument("--days", type=int, default=365)
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    lan_ip = args.ip or detect_lan_ip()
    print(f"LAN IP: {lan_ip}")

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, "diksiyon.local"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Istanbul Turkcesi Diksiyon"),
    ])
    san_list = [
        x509.DNSName("localhost"),
        x509.DNSName("diksiyon.local"),
        x509.IPAddress(ipaddress.ip_address("127.0.0.1")),
    ]
    try:
        san_list.append(x509.IPAddress(ipaddress.ip_address(lan_ip)))
    except ValueError:
        pass

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(dt.datetime.now(dt.timezone.utc))
        .not_valid_after(dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=args.days))
        .add_extension(x509.SubjectAlternativeName(san_list), critical=False)
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(key, hashes.SHA256())
    )

    key_path = OUT_DIR / "server.key"
    crt_path = OUT_DIR / "server.crt"
    with open(key_path, "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))
    with open(crt_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    print(f"Yazildi:")
    print(f"  {key_path}")
    print(f"  {crt_path}")
    print(f"\nGecerli adresler:")
    print(f"  https://localhost:8765/static/")
    print(f"  https://{lan_ip}:8765/static/")
    print(f"\nNot: Self-signed sertifika oldugu icin telefon ve tarayici 'guvenli degil' uyarisi verir.")
    print("     'Gelismis -> Devam et' diyerek gecebilirsin (sadece kendi gelistirme ortaminda).")


if __name__ == "__main__":
    main()
