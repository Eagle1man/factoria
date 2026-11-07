"""Генерация самоподписанных сертификатов: HTTPS и OPC UA.

Сертификаты создаются на месте, в репозиторий не попадают.
"""
from __future__ import annotations

import ipaddress
from datetime import datetime, timedelta, timezone
from pathlib import Path

from asyncua.crypto.cert_gen import generate_self_signed_app_certificate
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509 import DNSName, UniformResourceIdentifier
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID


def _key() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def generate_https_pair(out: Path, host: str = "localhost") -> tuple[Path, Path]:
    """PEM-пара для uvicorn. Возвращает (cert, key)."""
    out.mkdir(parents=True, exist_ok=True)
    key = _key()
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, host)])
    now = datetime.now(timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(days=1))
        .not_valid_after(now + timedelta(days=365))
        .add_extension(
            x509.SubjectAlternativeName(
                [DNSName(host), x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]
            ),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )
    cert_path = out / f"{host}.crt"
    key_path = out / f"{host}.key"
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    key_path.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        )
    )
    return cert_path, key_path


def generate_opcua_pair(
    out: Path, name: str, uri: str, server: bool
) -> tuple[Path, Path]:
    """DER-пара для OPC UA. Возвращает (cert, key).

    DER обязателен: asyncua читает ключ через load_der_private_key.
    """
    out.mkdir(parents=True, exist_ok=True)
    key = _key()
    usage = ExtendedKeyUsageOID.SERVER_AUTH if server else ExtendedKeyUsageOID.CLIENT_AUTH
    cert = generate_self_signed_app_certificate(
        key,
        uri,
        {"commonName": name},
        [UniformResourceIdentifier(uri), DNSName("localhost")],
        extended=[usage],
        days=365,
    )
    cert_path = out / f"{name}.cert.der"
    key_path = out / f"{name}.key.der"
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.DER))
    key_path.write_bytes(
        key.private_bytes(
            serialization.Encoding.DER,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    return cert_path, key_path
