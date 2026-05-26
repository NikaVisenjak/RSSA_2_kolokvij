"""
Generiranje PKI infrastrukture za mTLS gRPC komunikacijo.

Struktura:
- CA (Certificate Authority) - korenski certifikat
- Server certifikat (podpisan s CA)
- Client certifikat (podpisan s CA) — identiteta klienta je zaščitena
  ker je vidna SAMO strežniku znotraj TLS tunela, ne tretjim osebam.
"""

import os
import datetime
from cryptography import x509
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

CERTS_DIR = os.path.join(os.path.dirname(__file__), "certs")
os.makedirs(CERTS_DIR, exist_ok=True)


def generate_private_key():
    """Generira RSA 4096-bit zasebni ključ."""
    return rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096,
        backend=default_backend()
    )


def save_private_key(key, path, password=None):
    """Shrani zasebni ključ (opcijsko z geslom)."""
    encryption = (
        serialization.BestAvailableEncryption(password.encode())
        if password
        else serialization.NoEncryption()
    )
    with open(path, "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=encryption
        ))
    print(f"  ✓ Zasebni ključ shranjen: {path}")


def save_certificate(cert, path):
    """Shrani certifikat."""
    with open(path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    print(f"  ✓ Certifikat shranjen: {path}")


def create_ca():
    """Ustvari korenski CA certifikat."""
    print("\n[1/3] Generiranje CA (Certificate Authority)...")
    key = generate_private_key()

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "SI"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Ljubljana"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Naloga3 CA"),
        x509.NameAttribute(NameOID.COMMON_NAME, "Naloga3 Root CA"),
    ])

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow())
        .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=3650))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .add_extension(
            x509.KeyUsage(
                digital_signature=True, key_cert_sign=True, crl_sign=True,
                content_commitment=False, key_encipherment=False,
                data_encipherment=False, key_agreement=False,
                encipher_only=False, decipher_only=False
            ),
            critical=True
        )
        .sign(key, hashes.SHA256(), default_backend())
    )

    save_private_key(key, os.path.join(CERTS_DIR, "ca.key"))
    save_certificate(cert, os.path.join(CERTS_DIR, "ca.crt"))
    return key, cert


def create_server_cert(ca_key, ca_cert):
    """Ustvari strežniški certifikat, podpisan s CA."""
    print("\n[2/3] Generiranje strežniškega certifikata...")
    key = generate_private_key()

    subject = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "SI"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Ljubljana"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Naloga3 Server"),
        x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
    ])

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(ca_cert.subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow())
        .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.IPAddress(__import__("ipaddress").ip_address("127.0.0.1")),
            ]),
            critical=False
        )
        .add_extension(
            x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]),
            critical=False
        )
        .add_extension(
            x509.KeyUsage(
                digital_signature=True, key_encipherment=True,
                content_commitment=False, data_encipherment=False,
                key_agreement=False, key_cert_sign=False,
                crl_sign=False, encipher_only=False, decipher_only=False
            ),
            critical=True
        )
        .sign(ca_key, hashes.SHA256(), default_backend())
    )

    save_private_key(key, os.path.join(CERTS_DIR, "server.key"))
    save_certificate(cert, os.path.join(CERTS_DIR, "server.crt"))
    return key, cert


def create_client_cert(ca_key, ca_cert):
    """
    Ustvari klientov certifikat, podpisan s CA.
    
    VARNOST: Identiteta klienta je zaščitena ker:
    - Certifikat je prenesen ZNOTRAJ TLS tunela (po TLS handshake)
    - Tretje osebe vidijo samo šifrirane podatke
    - Samo strežnik (z zasebnim ključem) lahko dešifrira in vidi klientov certifikat
    """
    print("\n[3/3] Generiranje klientovega certifikata...")
    print("  ℹ  Identiteta klienta bo vidna SAMO strežniku (zaščitena znotraj TLS tunela)")
    key = generate_private_key()

    subject = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "SI"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Ljubljana"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Naloga3 Client"),
        x509.NameAttribute(NameOID.COMMON_NAME, "naloga3-client-secret"),  # ta vrednost je skrita
    ])

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(ca_cert.subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow())
        .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(
            x509.ExtendedKeyUsage([ExtendedKeyUsageOID.CLIENT_AUTH]),
            critical=False
        )
        .add_extension(
            x509.KeyUsage(
                digital_signature=True, key_encipherment=True,
                content_commitment=False, data_encipherment=False,
                key_agreement=False, key_cert_sign=False,
                crl_sign=False, encipher_only=False, decipher_only=False
            ),
            critical=True
        )
        .sign(ca_key, hashes.SHA256(), default_backend())
    )

    save_private_key(key, os.path.join(CERTS_DIR, "client.key"))
    save_certificate(cert, os.path.join(CERTS_DIR, "client.crt"))
    return key, cert


def print_fingerprints():
    """Izpiše fingerprinte certifikatov za preverjanje."""
    print("\n" + "="*60)
    print("CERTIFIKATNI FINGERPRINTI (SHA-256):")
    print("="*60)
    for name, path in [("CA", "ca.crt"), ("Server", "server.crt"), ("Client", "client.crt")]:
        full_path = os.path.join(CERTS_DIR, path)
        with open(full_path, "rb") as f:
            cert = x509.load_pem_x509_certificate(f.read(), default_backend())
        fp = cert.fingerprint(hashes.SHA256()).hex()
        fp_fmt = ":".join(fp[i:i+2] for i in range(0, len(fp), 2))
        print(f"  {name:8s}: {fp_fmt[:47]}...")


if __name__ == "__main__":
    print("="*60)
    print("  mTLS PKI INFRASTRUKTURA — NALOGA 3")
    print("="*60)

    ca_key, ca_cert = create_ca()
    create_server_cert(ca_key, ca_cert)
    create_client_cert(ca_key, ca_cert)

    print_fingerprints()

    print("\n" + "="*60)
    print("✅ Vsi certifikati so generirani v mapi: certs/")
    print("="*60)
    print("\nGenerirana datoteke:")
    for f in sorted(os.listdir(CERTS_DIR)):
        size = os.path.getsize(os.path.join(CERTS_DIR, f))
        print(f"  {f:20s} ({size} B)")
