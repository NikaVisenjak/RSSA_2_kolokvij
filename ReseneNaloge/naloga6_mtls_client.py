# ============================================================
# NALOGA 6: gRPC CLIENT z mTLS varnostjo
# ============================================================
# Client se mora identificirati s certifikatom (podpisanim s CA)
# Njegova identiteta je SKRITA (šifrirana v TLS)
# ============================================================

import grpc
import secure_service_pb2
import secure_service_pb2_grpc

def send_secure_message(message: str):
    """
    Pošlje šifrirano sporočilo serverju z mTLS avtentikacijo.
    """
    # Naložimo clientove certifikate
    with open('certs/client.key', 'rb') as f:
        client_key = f.read()   # clientov zasebni ključ (SKRIVNOST!)
    with open('certs/client.crt', 'rb') as f:
        client_cert = f.read()  # clientov certifikat
    with open('certs/ca.crt', 'rb') as f:
        ca_cert = f.read()      # CA certifikat (za preverjanje serverja)
    
    # Ustvarimo SSL credentials za CLIENT
    # ssl_channel_credentials(root_certs, private_key, cert_chain)
    client_credentials = grpc.ssl_channel_credentials(
        # CA certifikat: s tem preverimo ali je SERVER legitimen
        # (Ali je serverjev certifikat podpisan s to CA?)
        root_certificates=ca_cert,
        
        # Clientov zasebni ključ: za dokazovanje identitete serverju
        private_key=client_key,
        
        # Clientov certifikat: server ga bo preveril z CA
        certificate_chain=client_cert,
    )
    
    # secure_channel namesto insecure_channel!
    # Vsi podatki so zdaj šifrirani z AES (dogovorjeno med TLS handshake)
    channel = grpc.secure_channel("localhost:50053", client_credentials)
    
    stub = secure_service_pb2_grpc.SecureServiceStub(channel)
    
    try:
        print(f"Pošiljam varno sporočilo: '{message}'")
        response = stub.SendMessage(
            secure_service_pb2.SecureRequest(message=message)
        )
        
        print(f"\nOdgovor serverja:")
        print(f"  Sporočilo:     {response.reply}")
        print(f"  Identificiran kot: {response.client_id}")
        print(f"  mTLS uspešen:  {response.authenticated}")
        
    except grpc.RpcError as e:
        # PERMISSION_DENIED: certifikat ni bil sprejet
        # UNAVAILABLE: server ne teče
        # SSL_ERROR: problem s certifikati
        print(f"gRPC napaka: {e.code()}: {e.details()}")
    
    finally:
        channel.close()

if __name__ == "__main__":
    print("=== Varni gRPC Client (mTLS) ===")
    print("Identiteta klienta je skrita - šifrirana v TLS!\n")
    send_secure_message("Tajna misija: dostavi čokolado!")
