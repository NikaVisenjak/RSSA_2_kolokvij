"""
Vaja 1: gRPC Strežnik
Prejme sporočilo (Sporocilo) in ga vrne z velikimi črkami.
"""

import grpc
from concurrent import futures
import naloga1_pb2
import naloga1_pb2_grpc

PORT = 50051


# Implementacija service-a Naloga1
class Naloga1Servicer(naloga1_pb2_grpc.Naloga1Servicer):

    def PosljiSporocilo(self, request, context):
        """
        Prejme Sporocilo, vrne isto sporočilo z velikimi črkami.
        """
        print(f"[STREŽNIK] Prejeto: '{request.text}'")
        odgovor = request.text.upper()
        print(f"[STREŽNIK] Pošiljam nazaj: '{odgovor}'")
        return naloga1_pb2.Sporocilo(text=odgovor)


def run_server():
    # Ustvari gRPC strežnik z nitnim threadpool-om
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # Registriraj service na strežnik
    naloga1_pb2_grpc.add_Naloga1Servicer_to_server(Naloga1Servicer(), server)

    # Poslušaj na portu
    server.add_insecure_port(f"[::]:{PORT}")
    server.start()
    print(f"[STREŽNIK] Zagnan na portu {PORT}. Čakam na sporočila...")

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("\n[STREŽNIK] Ustavljam...")
        server.stop(0)


if __name__ == "__main__":
    run_server()