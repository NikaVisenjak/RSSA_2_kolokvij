"""
gRPC STREŽNIK z mTLS (Mutual TLS) avtentikacijo — Naloga 3

Varnostni mehanizmi:
1. Strežnik se identificira klientu z lastnim certifikatom (server.crt)
2. Strežnik zahteva klientov certifikat in ga preveri (require_client_auth)
3. Identiteta klienta je zaščitena — vidna SAMO strežniku znotraj TLS tunela
4. Vsa komunikacija je šifrirana (TLS 1.2+)
5. Certifikati so podpisani s skupnim CA

Arhitektura zaščite identitete klienta:
  [Klient] ──TLS handshake──> [Strežnik]
              ^
              |__ Klientov certifikat se prenese ZNOTRAJ šifriranega tunela
                  (po tem ko je TLS tunel vzpostavljen)
                  => Tretje osebe vidijo SAMO šifrirane pakete, ne certifikata!
"""

import grpc
import uuid
import hashlib
import logging
import os
import sys
from concurrent import futures
from datetime import datetime, timezone
from cryptography import x509
from cryptography.hazmat.backends import default_backend

# Dodamo pot do generiranih proto datotek
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import secure_service_pb2
import secure_service_pb2_grpc

# Nastavitev logiranja
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [SERVER] %(levelname)s %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger(__name__)

CERTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "certs")
SERVER_PORT = 50051

# ─────────────────────────────────────────────
# Pomožne funkcije
# ─────────────────────────────────────────────

def load_cert(filename):
    with open(os.path.join(CERTS_DIR, filename), "rb") as f:
        return f.read()


def get_cert_fingerprint(cert_pem: bytes) -> str:
    """Vrne SHA-256 fingerprint certifikata."""
    cert = x509.load_pem_x509_certificate(cert_pem, default_backend())
    fp = cert.fingerprint(__import__("cryptography.hazmat.primitives.hashes", fromlist=["SHA256"]).SHA256()).hex()
    return ":".join(fp[i:i+2] for i in range(0, len(fp), 2))


def get_client_identity(context) -> str:
    """
    Ekstrahira identiteto klienta iz TLS konteksta.
    
    VARNOST: Ta informacija je dostopna SAMO strežniku — klientov certifikat
    se prenese znotraj šifriranega TLS tunela in je nevidna tretjim osebam.
    """
    peer_cert = context.peer_identities()
    if peer_cert:
        # peer_identities vrne seznam vrednosti Subject Alternative Names
        return ", ".join(str(p) for p in peer_cert) if peer_cert else "neznano"
    
    # Alternativno: iz auth context
    auth_ctx = context.auth_context()
    if "x509_common_name" in auth_ctx:
        names = auth_ctx["x509_common_name"]
        return ", ".join(n.decode() if isinstance(n, bytes) else n for n in names)
    
    return "NEZNANO (certifikat ni priložen)"


# ─────────────────────────────────────────────
# Implementacija gRPC servisov
# ─────────────────────────────────────────────

class SecureServiceServicer(secure_service_pb2_grpc.SecureServiceServicer):
    """
    Implementacija varnega gRPC servisa z mTLS avtentikacijo.
    """

    def __init__(self):
        self.server_cert_pem = load_cert("server.crt")
        self.server_fingerprint = get_cert_fingerprint(self.server_cert_pem)
        self.session_store = {}  # Shramba aktivnih sej
        log.info("SecureService inicializiran")
        log.info(f"Strežniški certifikat fingerprint: {self.server_fingerprint[:47]}...")

    def _verify_client(self, context) -> tuple[bool, str]:
        """
        Preveri klientovo identiteto in jo zabeleži (samo interno — ne javno!).
        
        Vrne: (je_verificiran, identiteta_klienta)
        """
        auth_ctx = context.auth_context()
        
        if not auth_ctx:
            log.warning("⚠️  Klient brez TLS konteksta!")
            return False, "BREZ CERTIFIKATA"

        # Ekstrahiraj CN (Common Name) iz klientovega certifikata
        client_id = "NEZNANO"
        if "x509_common_name" in auth_ctx:
            names = auth_ctx["x509_common_name"]
            client_id = ", ".join(n.decode() if isinstance(n, bytes) else n for n in names)
        
        log.info(f"🔐 Klient verificiran | Identiteta (ZAUPNA, vidna samo strežniku): [{client_id}]")
        return True, client_id

    def SendMessage(self, request, context):
        """Sprejme šifrirano sporočilo od verificiranega klienta."""
        verified, client_id = self._verify_client(context)
        
        if not verified:
            context.set_code(grpc.StatusCode.UNAUTHENTICATED)
            context.set_details("Klient ni verificiran — TLS certifikat zahtevan!")
            return secure_service_pb2.MessageResponse()

        session_id = str(uuid.uuid4())[:8]
        self.session_store[session_id] = client_id
        
        log.info(f"📨 Sporočilo prejeto | ID={request.message_id} | Seja={session_id}")
        log.info(f"   Vsebina: {request.content[:50]}{'...' if len(request.content) > 50 else ''}")

        return secure_service_pb2.MessageResponse(
            success=True,
            message=f"Sporočilo varno prejeto in obdelano.",
            server_timestamp=datetime.now(timezone.utc).isoformat(),
            session_id=session_id
        )

    def GetServerInfo(self, request, context):
        """
        Vrne informacije o strežniku za verifikacijo identitete strežnika.
        Klient lahko preveri fingerprint strežnikovega certifikata.
        """
        verified, client_id = self._verify_client(context)
        
        if not verified:
            context.set_code(grpc.StatusCode.UNAUTHENTICATED)
            context.set_details("Nepooblaščen dostop!")
            return secure_service_pb2.ServerInfoResponse()

        log.info(f"ℹ️  GetServerInfo zahteva | RequestID={request.request_id}")

        return secure_service_pb2.ServerInfoResponse(
            server_name="Naloga3-SecureServer",
            version="1.0.0",
            certificate_fingerprint=self.server_fingerprint,
            supported_cipher="TLS_AES_256_GCM_SHA384 / TLS_CHACHA20_POLY1305_SHA256"
        )

    def Ping(self, request, context):
        """
        Ping za test vzpostavljene varne seje.
        Strežnik pošlje nazaj klientov nonce + lasten nonce
        (zaščita pred replay napadi).
        """
        verified, client_id = self._verify_client(context)
        
        if not verified:
            context.set_code(grpc.StatusCode.UNAUTHENTICATED)
            context.set_details("Nepooblaščen ping!")
            return secure_service_pb2.PingResponse()

        server_nonce = str(uuid.uuid4())
        log.info(f"🏓 Ping | ClientNonce={request.client_nonce[:16]}... | ServerNonce={server_nonce[:16]}...")

        return secure_service_pb2.PingResponse(
            server_nonce=server_nonce,
            client_nonce=request.client_nonce,  # Echo nazaj za verifikacijo
            timestamp=datetime.now(timezone.utc).isoformat()
        )


# ─────────────────────────────────────────────
# Zagon strežnika
# ─────────────────────────────────────────────

def serve():
    print("=" * 65)
    print("  gRPC mTLS STREŽNIK — NALOGA 3")
    print("=" * 65)

    # Naloži certifikate
    ca_cert    = load_cert("ca.crt")
    server_key = load_cert("server.key")
    server_crt = load_cert("server.crt")

    # Ustvari SSL/TLS poverilnice z zahtevano klientsko avtentikacijo
    # require_client_auth=True => strežnik bo zahteval klientov certifikat!
    server_credentials = grpc.ssl_server_credentials(
        [(server_key, server_crt)],  # (zasebni ključ, certifikat) strežnika
        root_certificates=ca_cert,   # CA certifikat za verifikacijo klientov
        require_client_auth=True     # ← KLJUČNO: zahteva klientov certifikat
    )

    # Ustvari in konfiguriraj gRPC strežnik
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
        options=[
            ("grpc.max_send_message_length",    50 * 1024 * 1024),
            ("grpc.max_receive_message_length", 50 * 1024 * 1024),
        ]
    )

    # Registriraj servis
    secure_service_pb2_grpc.add_SecureServiceServicer_to_server(
        SecureServiceServicer(), server
    )

    # Dodaj SAMO varen (TLS) port — brez insecure porta!
    addr = f"[::]:{SERVER_PORT}"
    server.add_secure_port(addr, server_credentials)

    server.start()

    print(f"\n✅ Strežnik posluša na: localhost:{SERVER_PORT} (samo mTLS)")
    print(f"\nVarnostne nastavitve:")
    print(f"  • Protokol:          TLS (mutual)")
    print(f"  • Klientska avt.:    ZAHTEVANA (require_client_auth=True)")
    print(f"  • CA certifikat:     certs/ca.crt")
    print(f"  • Strežniški cert:   certs/server.crt")
    print(f"  • Insecure port:     NI (onemogočen)")
    print(f"\nStrežnik čaka na povezave... (Ctrl+C za izhod)\n")
    print("-" * 65)

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        log.info("Strežnik se ustavlja...")
        server.stop(grace=5)
        print("\n✋ Strežnik ustavljen.")


if __name__ == "__main__":
    serve()
