# ============================================================
# NALOGA 5: gRPC CLIENT - Bayesovo iskanje z bisekcijo
# ============================================================
# STRATEGIJA: Iterativna bisekcija (binary search v 2D)
#
# Ideja Bayesovega sklepanja:
# - Začnemo z enakomereno porazdelitvijo čez cel prostor
# - Po vsakem namigi posodobimo naše znanje (zoužamo iskalni prostor)
# - Naslednje ugibanje je sredina preostalega prostora
#
# Implementacija: vzdržujemo pravokotnik [x_min, x_max] x [y_min, y_max]
# Po vsaki smeri zoužamo ta pravokotnik:
#   NORTH -> y_min = current_y (žoga je nad nami, dvignemo spodnjo mejo)
#   SOUTH -> y_max = current_y (žoga je pod nami, znižamo zgornjo mejo)
#   EAST  -> x_min = current_x
#   WEST  -> x_max = current_x
#   Diagonale = kombinacija obeh
# ============================================================

# ============================================================
# NALOGA 5: gRPC CLIENT - Bayesovo iskanje z bisekcijo
# ============================================================

# Uvoz gRPC knjižnice
import grpc

# Uvoz protobuf datotek
import bayes_game_pb2
import bayes_game_pb2_grpc


# ============================================================
# FUNKCIJA play_with_bisection
# Igra z uporabo bisekcijske strategije
# ============================================================
def play_with_bisection(stub):

    # --------------------------------------------------------
    # ZAČETEK IGRE
    # --------------------------------------------------------

    # Pokličemo RPC metodo StartGame
    start_resp = stub.StartGame(
        bayes_game_pb2.StartGameRequest()
    )

    # Shranimo ID igre
    game_id = start_resp.game_id

    # Izpis začetka igre
    print(f"Igra {game_id} začeta!")

    # --------------------------------------------------------
    # ZAČETNI ISKALNI PROSTOR
    # --------------------------------------------------------

    # Začetna spodnja meja x
    x_min = 0.0

    # Začetna zgornja meja x
    x_max = 2000.0

    # Začetna spodnja meja y
    y_min = 0.0

    # Začetna zgornja meja y
    y_max = 2000.0

    # Števec poskusov
    attempts = 0

    # Maksimalno število dovoljenih poskusov
    MAX_ATTEMPTS = 100

    # --------------------------------------------------------
    # GLAVNA ZANKA IGRE
    # --------------------------------------------------------
    while attempts < MAX_ATTEMPTS:

        # Sredina trenutnega prostora po x osi
        guess_x = (x_min + x_max) / 2.0

        # Sredina trenutnega prostora po y osi
        guess_y = (y_min + y_max) / 2.0

        # Izpis trenutnega ugibanja
        print(
            f"\nFaza {attempts+1}: "
            f"Ugibam ({guess_x:.1f}, {guess_y:.1f}) | "
            f"Prostor: "
            f"x=[{x_min:.0f},{x_max:.0f}], "
            f"y=[{y_min:.0f},{y_max:.0f}]"
        )

        # ----------------------------------------------------
        # POŠLJEMO UGIBANJE SERVERJU
        # ----------------------------------------------------

        # Kličemo RPC metodo MakeGuess
        resp = stub.MakeGuess(

            # Ustvarimo protobuf zahtevek
            bayes_game_pb2.GuessRequest(

                # ID trenutne igre
                game_id=game_id,

                # Ugibanje po x osi
                x=guess_x,

                # Ugibanje po y osi
                y=guess_y,
            )
        )

        # Povečamo števec poskusov
        attempts += 1

        # ----------------------------------------------------
        # PREVERIMO ALI SMO ZADELI
        # ----------------------------------------------------

        # Če je igre konec
        if resp.game_over:

            # Izpis uspeha
            print(
                f"\n✓ ZADELI! "
                f"Potrebovali smo "
                f"{resp.attempts} poskusov!"
            )

            # Vrni število poskusov
            return attempts

        # ----------------------------------------------------
        # PREBEREMO SMER OD SERVERJA
        # ----------------------------------------------------

        # Smer žoge glede na naše ugibanje
        d = resp.direction

        # ----------------------------------------------------
        # POSODOBIMO ISKALNI PROSTOR
        # ----------------------------------------------------

        # Če je žoga severno
        if d == bayes_game_pb2.NORTH:

            # Dvignemo spodnjo y mejo
            y_min = guess_y

            # Izpis spremembe
            print(
                f"  ↑ SEVER: "
                f"dvigam y_min na {y_min:.0f}"
            )

        # Če je žoga južno
        elif d == bayes_game_pb2.SOUTH:

            # Spustimo zgornjo y mejo
            y_max = guess_y

            # Izpis spremembe
            print(
                f"  ↓ JUG: "
                f"znižam y_max na {y_max:.0f}"
            )

        # Če je žoga vzhodno
        elif d == bayes_game_pb2.EAST:

            # Dvignemo spodnjo x mejo
            x_min = guess_x

            # Izpis spremembe
            print(
                f"  → VZHOD: "
                f"dvigam x_min na {x_min:.0f}"
            )

        # Če je žoga zahodno
        elif d == bayes_game_pb2.WEST:

            # Spustimo zgornjo x mejo
            x_max = guess_x

            # Izpis spremembe
            print(
                f"  ← ZAHOD: "
                f"znižam x_max na {x_max:.0f}"
            )

        # Če je žoga severovzhodno
        elif d == bayes_game_pb2.NORTHEAST:

            # Dvignemo spodnjo x mejo
            x_min = guess_x

            # Dvignemo spodnjo y mejo
            y_min = guess_y

            # Izpis spremembe
            print(
                f"  ↗ SEVERO-VZHOD: "
                f"x_min={x_min:.0f}, "
                f"y_min={y_min:.0f}"
            )

        # Če je žoga jugovzhodno
        elif d == bayes_game_pb2.SOUTHEAST:

            # Dvignemo spodnjo x mejo
            x_min = guess_x

            # Spustimo zgornjo y mejo
            y_max = guess_y

            # Izpis spremembe
            print(
                f"  ↘ JUGO-VZHOD: "
                f"x_min={x_min:.0f}, "
                f"y_max={y_max:.0f}"
            )

        # Če je žoga jugozahodno
        elif d == bayes_game_pb2.SOUTHWEST:

            # Spustimo zgornjo x mejo
            x_max = guess_x

            # Spustimo zgornjo y mejo
            y_max = guess_y

            # Izpis spremembe
            print(
                f"  ↙ JUGO-ZAHOD: "
                f"x_max={x_max:.0f}, "
                f"y_max={y_max:.0f}"
            )

        # Če je žoga severozahodno
        elif d == bayes_game_pb2.NORTHWEST:

            # Spustimo zgornjo x mejo
            x_max = guess_x

            # Dvignemo spodnjo y mejo
            y_min = guess_y

            # Izpis spremembe
            print(
                f"  ↖ SEVERO-ZAHOD: "
                f"x_max={x_max:.0f}, "
                f"y_min={y_min:.0f}"
            )

        # ----------------------------------------------------
        # IZRAČUN PREOSTALEGA PROSTORA
        # ----------------------------------------------------

        # Širina preostalega prostora
        width = x_max - x_min

        # Višina preostalega prostora
        height = y_max - y_min

        # Izpis velikosti prostora
        print(
            f"  Preostali prostor: "
            f"{width:.0f} x {height:.0f} enot"
        )

    # --------------------------------------------------------
    # Če presežemo maksimalno število poskusov
    # --------------------------------------------------------

    print(
        f"Presegli smo "
        f"max poskusov ({MAX_ATTEMPTS})"
    )

    # Vrni število poskusov
    return attempts


# ============================================================
# FUNKCIJA main
# ============================================================
def main():

    # Ustvarimo povezavo na gRPC server
    channel = grpc.insecure_channel(
        "localhost:50052"
    )

    # Ustvarimo stub objekt
    stub = bayes_game_pb2_grpc.BayesGameStub(channel)

    # Izpis naslova
    print("=== Bayesova igra iskanja žoge ===")

    # Izpis strategije
    print(
        "Strategija: "
        "iterativna bisekcija iskalnega prostora\n"
    )

    # Zaženemo igro
    total_attempts = play_with_bisection(stub)

    # Končni izpis uspešnosti
    print(
        f"\nUčinkovitost: "
        f"zadeli v {total_attempts} korakih"
    )

    # Zapremo povezavo
    channel.close()


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":

    # Zaženemo klienta
    main()