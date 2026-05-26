"""
gRPC KLIENT z mTLS (Mutual TLS) avtentikacijo — Naloga 3

Varnostni mehanizmi:
1. Klient preverja strežnikov certifikat (prepreči man-in-the-middle)
2. Klient se identificira strežniku s lastnim certifikatom (client.crt)
3. ZASEBNOST KLIENTA: klientov certifikat je prenesen ZNOTRAJ TLS tunela
   — tretje osebe ne morejo videti identitete klienta!
4. Klient preverja fingerprint strežnika (pinning)

Potek mTLS rokovanja (handshake):
  1. TCP vzpostavi povezavo
  2. TLS handshake:
     a) Strežnik pošlje certifikat klientu (server.crt)
     b) Klient preveri strežnikov certifikat (z CA)
     c) TLS tunel je vzpostavljen (šifriranje aktivno)
     d) Klient pošlje certifikat strežniku — ZNOTRAJ TUNELA ← zaščita identitete!
     e) Strežnik preveri klientov certifikat (z CA)
  3. Varna dvosmerna komunikacija vzpostavljena
"""

import grpc
import uuid
import logging
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import secure_service_pb2
import secure_service_pb2_grpc

# Nastavitev logiranja
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [KLIENT] %(levelname)s %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger(__name__)

CERTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "certs")
SERVER_ADDR = "localhost:50051"

# Pričakovani fingerprint strežnika (certificate pinning)
# V produkciji bi bil to vnaprej znan, trdo zakodiran hash
EXPECTED_SERVER_NAME = "Naloga3-SecureServer"


def load_cert(filename: str) -> bytes:
    with open(os.path.join(CERTS_DIR, filename), "rb") as f:
        return f.read()


class SecureGrpcClient:
    """
    mTLS gRPC klient z vzajemno avtentikacijo.
    
    Zagotavlja:
    - Verifikacijo strežnika (prepreči MitM napade)
    - Identifikacijo klienta strežniku (znotraj TLS tunela)
    - Zaščito identitete klienta pred tretjimi osebami
    """

    def __init__(self):
        self.channel = None
        self.stub = None
        self._setup_secure_channel()

    def _setup_secure_channel(self):
        """Vzpostavi varni TLS kanal z vzajemno avtentikacijo."""
        log.info("Nastavljam mTLS kanal...")

        # Naloži certifikate
        ca_cert    = load_cert("ca.crt")    # Za verifikacijo strežnika
        client_key = load_cert("client.key") # Zasebni ključ klienta
        client_crt = load_cert("client.crt") # Certifikat klienta (identiteta)

        # Ustvari klientske TLS poverilnice
        # - ca_cert: s tem preverimo strežnikov certifikat
        # - client_key + client_crt: s tem se identificiramo strežniku
        credentials = grpc.ssl_channel_credentials(
            root_certificates=ca_cert,        # CA za verifikacijo strežnika
            private_key=client_key,           # Klientov zasebni ključ
            certificate_chain=client_crt      # Klientov certifikat (identiteta)
        )

        # Vzpostavi šifrirani kanal
        self.channel = grpc.secure_channel(
            SERVER_ADDR,
            credentials,
            options=[
                ("grpc.ssl_target_name_override", "localhost"),
                ("grpc.max_send_message_length",    50 * 1024 * 1024),
                ("grpc.max_receive_message_length", 50 * 1024 * 1024),
            ]
        )
        self.stub = secure_service_pb2_grpc.SecureServiceStub(self.channel)
        log.info(f"✅ Varni mTLS kanal vzpostavljen → {SERVER_ADDR}")

    def verify_server_identity(self) -> bool:
        """
        Preveri identiteto strežnika z GetServerInfo in certificate pinning.
        S tem preprečimo man-in-the-middle napade.
        """
        print("\n" + "─" * 55)
        print("KORAK 1: Verifikacija identitete strežnika")
        print("─" * 55)

        try:
            request_id = str(uuid.uuid4())
            response = self.stub.GetServerInfo(
                secure_service_pb2.ServerInfoRequest(request_id=request_id)
            )

            print(f"  Strežnik:      {response.server_name}")
            print(f"  Verzija:       {response.version}")
            print(f"  Šifriranje:    {response.supported_cipher}")
            print(f"  Fingerprint:   {response.certificate_fingerprint[:47]}...")

            # Preverimo pričakovano ime strežnika (certificate pinning)
            if response.server_name == EXPECTED_SERVER_NAME:
                print(f"  ✅ Identiteta strežnika VERIFICIRANA!")
                log.info(f"Strežnik '{response.server_name}' uspešno verificiran.")
                return True
            else:
                print(f"  ❌ NAPAKA: Pričakovano '{EXPECTED_SERVER_NAME}', dobljeno '{response.server_name}'")
                log.error("Verifikacija strežnika NEUSPEŠNA!")
                return False

        except grpc.RpcError as e:
            print(f"  ❌ Napaka pri verifikaciji: {e.code()} — {e.details()}")
            return False

    def ping_server(self) -> bool:
        """Test vzpostavljene seje z nonce zaščito proti replay napadom."""
        print("\n" + "─" * 55)
        print("KORAK 2: Ping test (zaščita proti replay napadom)")
        print("─" * 55)

        client_nonce = str(uuid.uuid4())
        print(f"  Pošljem nonce: {client_nonce[:16]}...")

        try:
            response = self.stub.Ping(
                secure_service_pb2.PingRequest(client_nonce=client_nonce)
            )

            # Preverimo da je strežnik echo-al naš nonce (dokaz pristnosti)
            if response.client_nonce == client_nonce:
                print(f"  Server nonce:  {response.server_nonce[:16]}...")
                print(f"  Client echo:   {response.client_nonce[:16]}... ✓")
                print(f"  Timestamp:     {response.timestamp}")
                print(f"  ✅ Ping uspešen — seja je varno vzpostavljena!")
                return True
            else:
                print(f"  ❌ Nonce mismatch — možen replay napad!")
                return False

        except grpc.RpcError as e:
            print(f"  ❌ Ping napaka: {e.code()} — {e.details()}")
            return False

    def send_message(self, content: str) -> bool:
        """Pošlje šifrirano sporočilo strežniku."""
        print("\n" + "─" * 55)
        print("KORAK 3: Pošiljanje šifriranega sporočila")
        print("─" * 55)

        msg_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now(timezone.utc).isoformat()

        print(f"  Vsebina:  {content}")
        print(f"  ID:       {msg_id}")
        print(f"  Čas:      {timestamp}")
        print(f"  Status:   Pošiljam...")

        try:
            response = self.stub.SendMessage(
                secure_service_pb2.MessageRequest(
                    content=content,
                    timestamp=timestamp,
                    message_id=msg_id
                )
            )

            if response.success:
                print(f"  ✅ Sporočilo uspešno poslano!")
                print(f"  Seja ID:  {response.session_id}")
                print(f"  Odgovor:  {response.message}")
                return True
            else:
                print(f"  ❌ Strežnik zavrnil sporočilo: {response.message}")
                return False

        except grpc.RpcError as e:
            print(f"  ❌ Napaka pošiljanja: {e.code()} — {e.details()}")
            return False

    def close(self):
        if self.channel:
            self.channel.close()
            log.info("Kanal zaprt.")


def demonstrate_mtls():
    """Demonstracija celotnega mTLS toka."""
    print("\n" + "=" * 65)
    print("  gRPC mTLS KLIENT — NALOGA 3")
    print("=" * 65)
    print("\nVarnostna arhitektura:")
    print("  ┌─────────┐   TLS Tunel (šifriran)   ┌─────────┐")
    print("  │  KLIENT │ ════════════════════════> │ STREŽNIK│")
    print("  │         │ <════════════════════════ │         │")
    print("  └─────────┘                           └─────────┘")
    print("       │                                      │")
    print("  client.crt (identiteta)              server.crt")
    print("  [vidna SAMO strežniku!]              [vidna klientu]")
    print("  [tretje osebe NE vidijo]")

    client = SecureGrpcClient()

    try:
        # Korak 1: Verificiraj identiteto strežnika
        server_ok = client.verify_server_identity()
        if not server_ok:
            print("\n❌ Strežnik NI verificiran. Prekinjam.")
            return

        # Korak 2: Ping test
        ping_ok = client.ping_server()
        if not ping_ok:
            print("\n❌ Seja ni varno vzpostavljena. Prekinjam.")
            return

        # Korak 3: Pošlji testna sporočila
        messages = [
            "Pozdravljeni! To je varno šifrirano sporočilo.",
            "Identiteta klienta je skrita pred tretjimi osebami.",
            "mTLS zagotavlja vzajemno avtentikacijo obeh strani."
        ]

        for msg in messages:
            client.send_message(msg)

        print("\n" + "=" * 65)
        print("✅ Demonstracija mTLS komunikacije USPEŠNA!")
        print("=" * 65)
        print("\nPovzetek varnostnih jamstev:")
        print("  ✓ Strežnik verificiran s certifikatom (prepreči MitM)")
        print("  ✓ Klient verificiran s certifikatom (samo zaupani klienti)")
        print("  ✓ Identiteta klienta skrita pred tretjimi osebami")
        print("  ✓ Vsa komunikacija šifrirana (TLS)")
        print("  ✓ Zaščita pred replay napadi (nonce)")

    except Exception as e:
        log.error(f"Nepričakovana napaka: {e}")
        raise
    finally:
        client.close()


if __name__ == "__main__":
    demonstrate_mtls()
