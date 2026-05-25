"""
Vaja 1: gRPC Klient
Pošlje sporočilo strežniku in izpiše odgovor z velikimi črkami.
"""

import grpc
import naloga1_pb2
import naloga1_pb2_grpc

PORT = 50051


def run_client():
    # Vzpostavi (nezavarovano) povezavo s strežnikom
    with grpc.insecure_channel(f"localhost:{PORT}") as channel:
        # Ustvari stub — lokalni "proxy" za klic strežnikovih metod
        stub = naloga1_pb2_grpc.Naloga1Stub(channel)

        print("Vpiši sporočilo (za izhod: 'quit'):")
        while True:
            besedilo = input("> ").strip()
            if besedilo.lower() in ("quit", "exit", "izhod"):
                break
            if not besedilo:
                continue

            # Ustvari Sporocilo objekt in ga pošlji strežniku
            zahteva = naloga1_pb2.Sporocilo(text=besedilo)
            odgovor = stub.PosljiSporocilo(zahteva)

            print(f"  Strežnik odgovoril: '{odgovor.text}'")


if __name__ == "__main__":
    run_client()