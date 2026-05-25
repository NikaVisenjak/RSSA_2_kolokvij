# ============================================================
# NALOGA 6: gRPC SERVER z mTLS varnostjo
# ============================================================
# mTLS = mutual TLS (obojestransko preverjanje certifikatov)
#
# TLS HANDSHAKE z mTLS:
#   1. Client -> Server: "Zdravo, podpiram TLS x.x"
#   2. Server -> Client: serverjev certifikat (server.crt)
#   3. Client preveri: Ali je server.crt podpisan s CA ki mu zaupam?
#   4. Server -> Client: "Pokaži mi svoj certifikat!" (to je mTLS!)
#   5. Client -> Server: clientov certifikat (client.crt)
#   6. Server preveri: Ali je client.crt podpisan s CA ki ji zaupam?
#   7. Vzpostavi se šifriran kanal - VSE je šifrirano!
#
# Identiteta klienta je SKRITA ker:
#   - client.crt se pošlje ŠELE po vzpostavitvi TLS šifriranja
#   - Pasivni opazovalec (man-in-the-middle) vidi samo šifrirane bajte
#   - Ne more ugotoviti kdo je klient!
# ============================================================

import grpc
from concurrent import futures

import secure_service_pb2
import secure_service_pb2_grpc

# -------------------------------------------------------
# Implementacija serverja
# -------------------------------------------------------
class SecureServicer(secure_service_pb2_grpc.SecureServiceServicer):
    
    def SendMessage(self, request, context):
        """
        Obdela varno sporočilo od authenticiranega klienta.
        context vsebuje metadata o TLS seji, vključno s 
        clientovim certifikatom.
        """
        # Pridobimo identiteto klienta iz TLS certifikata
        # auth_context() vrne avtentikacijske podatke TLS seje
        auth_context = context.auth_context()
        
        # x509_common_name je CN (Common Name) iz clientovega certifikata
        # To je identiteta klienta - preverjena s CA!
        client_cn = "neznan"
        if 'x509_common_name' in auth_context:
            # Vrne bytes, dekodiramo v string
            client_cn = auth_context['x509_common_name'][0].decode()
        
        print(f"Sporočilo od klienta '{client_cn}': {request.message}")
        
        return secure_service_pb2.SecureResponse(
            reply         = f"Prejel sem tvoje sporočilo: '{request.message}'",
            client_id     = client_cn,      # serverju je identiteta znana
            authenticated = True,           # oba sva se uspešno identificirala
        )

# -------------------------------------------------------
# Nalaganje certifikatov in zagon serverja
# -------------------------------------------------------
def serve():
    # Naložimo serverjev zasebni ključ in certifikat
    with open('certs/server.key', 'rb') as f:
        server_key = f.read()   # bytes - zasebni ključ
    with open('certs/server.crt', 'rb') as f:
        server_cert = f.read()  # bytes - serverjev certifikat
    with open('certs/ca.crt', 'rb') as f:
        ca_cert = f.read()      # bytes - CA certifikat (za preverjanje clientov)
    
    # Ustvarimo SSL credentials za SERVER
    # ssl_server_credentials(private_key_cert_chain_pairs, root_certificates, require_client_auth)
    server_credentials = grpc.ssl_server_credentials(
        # Lista tuplev (zasebni_ključ, certifikat) - server se identificira s tem
        private_key_certificate_chain_pairs=[(server_key, server_cert)],
        
        # CA certifikat za PREVERJANJE CLIENTOV
        # Server bo zavrnil kliente ki niso podpisani s to CA
        root_certificates=ca_cert,
        
        # require_client_auth=True -> mTLS! Server ZAHTEVA clientov certifikat
        # Brez tega bi bil samo navaden TLS (server se identificira, client ne)
        require_client_auth=True
    )
    
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    secure_service_pb2_grpc.add_SecureServiceServicer_to_server(
        SecureServicer(), server
    )
    
    # add_secure_port namesto add_insecure_port!
    # Razlika: secure_port zahteva SSL credentials
    server.add_secure_port("[::]:50053", server_credentials)
    
    server.start()
    print("Varni gRPC server teče na portu 50053 (mTLS)")
    print("Zahteva: server.crt + client.crt podpisana s skupno CA")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
