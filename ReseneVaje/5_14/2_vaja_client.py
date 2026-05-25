"""
Vaja 2: gRPC Klient — demonstrira vse 4 rpc metode:
  1. SendOne  - pošlji eno število
  2. GetOne   - zahtevaj določeno število po indeksu
  3. SendMore - pošlji več števil naenkrat (client-side streaming)
  4. GetAll   - prejmi vsa shranjena števila (server-side streaming)
"""

import grpc
import naloga2_pb2
import naloga2_pb2_grpc

PORT = 50052


def generator_stevil(stevila: list):
    """
    Generator za SendMore (client-side streaming).
    Vrača Stevilo objekte enega za drugim.
    """
    for s in stevila:
        yield naloga2_pb2.Stevilo(vrednost=s)


def run_client():
    with grpc.insecure_channel(f"localhost:{PORT}") as channel:
        stub = naloga2_pb2_grpc.Naloga2Stub(channel)

        # ── 1. SendOne ────────────────────────────────────────────────────
        print("=" * 45)
        print("1. SendOne — pošlji posamezna števila")
        print("=" * 45)
        for vrednost in [3.14, 2.71, 1.41, 1.73]:
            stub.SendOne(naloga2_pb2.Stevilo(vrednost=vrednost))
            print(f"   Poslano: {vrednost}")

        # ── 2. GetOne ─────────────────────────────────────────────────────
        print("\n" + "=" * 45)
        print("2. GetOne — zahtevaj po indeksu")
        print("=" * 45)
        for i in [0, 2]:
            odgovor = stub.GetOne(naloga2_pb2.Indeks(i=i))
            print(f"   seznam[{i}] = {odgovor.vrednost:.4f}")

        # ── 3. SendMore (client-side streaming) ───────────────────────────
        print("\n" + "=" * 45)
        print("3. SendMore — pošlji stream števil")
        print("=" * 45)
        nova_stevila = [10.0, 20.5, 30.75]
        print(f"   Pošiljam: {nova_stevila}")
        # Pošljemo generator (iterator) — gRPC bo sam iteriral
        stub.SendMore(generator_stevil(nova_stevila))
        print("   Strežnik shranil vsa števila.")

        # ── 4. GetAll (server-side streaming) ─────────────────────────────
        print("\n" + "=" * 45)
        print("4. GetAll — prejmi vse vrednosti (stream)")
        print("=" * 45)
        # stub.GetAll vrne iterator; beremo ga z for zanko
        vse = list(stub.GetAll(naloga2_pb2.Empty()))
        print(f"   Prejetih {len(vse)} vrednosti:")
        for i, s in enumerate(vse):
            print(f"   [{i}] {s.vrednost:.4f}")


if __name__ == "__main__":
    run_client()