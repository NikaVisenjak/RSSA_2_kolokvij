"""
Vaja 2: gRPC Strežnik — seznam števil s 4 rpc metodami
  SendOne  : shrani eno število
  GetOne   : vrne število na danem indeksu
  SendMore : shrani stream števil (client-side streaming)
  GetAll   : vrne vse shranjene številke kot stream (server-side streaming)
"""

import grpc
from concurrent import futures
import naloga2_pb2
import naloga2_pb2_grpc

PORT = 50052


class Naloga2Servicer(naloga2_pb2_grpc.Naloga2Servicer):

    def __init__(self):
        # Skupni seznam števil (zaščiten pred sočasnimi dostopi z lock-om)
        self.seznam = []

    # ── 1. SendOne ────────────────────────────────────────────────────────
    def SendOne(self, request, context):
        """Prejme eno število, ga doda v seznam, vrne Empty."""
        self.seznam.append(request.vrednost)
        print(f"[SendOne]  Shranjena vrednost: {request.vrednost:.4f}  "
              f"| Seznam: {[f'{x:.2f}' for x in self.seznam]}")
        return naloga2_pb2.Empty()

    # ── 2. GetOne ─────────────────────────────────────────────────────────
    def GetOne(self, request, context):
        """Prejme indeks i, vrne seznam[i]."""
        i = request.i
        if i < 0 or i >= len(self.seznam):
            context.abort(
                grpc.StatusCode.OUT_OF_RANGE,
                f"Indeks {i} je izven obsega (dolžina seznama: {len(self.seznam)})"
            )
        vrednost = self.seznam[i]
        print(f"[GetOne]   Zahtevani indeks {i} → vrednost {vrednost:.4f}")
        return naloga2_pb2.Stevilo(vrednost=vrednost)

    # ── 3. SendMore (client-side streaming) ───────────────────────────────
    def SendMore(self, request_iterator, context):
        """
        Prejme stream števil od klienta.
        request_iterator je iterator — beremo ga z for zanko.
        """
        nova = []
        for stevilo in request_iterator:
            nova.append(stevilo.vrednost)
            self.seznam.append(stevilo.vrednost)
        print(f"[SendMore] Shranjenih {len(nova)} novih vrednosti: "
              f"{[f'{x:.2f}' for x in nova]}")
        return naloga2_pb2.Empty()

    # ── 4. GetAll (server-side streaming) ─────────────────────────────────
    def GetAll(self, request, context):
        """
        Vrne vse vrednosti kot stream.
        Ker je to server-side streaming, definiramo generator (yield).
        """
        print(f"[GetAll]   Pošiljam {len(self.seznam)} vrednosti...")
        for vrednost in self.seznam:
            yield naloga2_pb2.Stevilo(vrednost=vrednost)


def run_server():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    naloga2_pb2_grpc.add_Naloga2Servicer_to_server(Naloga2Servicer(), server)
    server.add_insecure_port(f"[::]:{PORT}")
    server.start()
    print(f"[STREŽNIK] Zagnan na portu {PORT}.")

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == "__main__":
    run_server()