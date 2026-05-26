# ============================================================
# NALOGA 5: gRPC SERVER - Bayesovo iskanje žoge na mizi
# ============================================================
# Server ima mizo z naključnimi dimenzijami in skrito točko (žogo).
# Client ugiba (x, y); server vrne smer ali game_over ob zadetku.
# ============================================================

# ============================================================
# NALOGA 5: gRPC SERVER - Bayesovo iskanje žoge na mizi
# ============================================================

# Uvoz modula za generiranje unikatnih ID-jev iger
import uuid

# Uvoz modula za naključna števila
import random

# Uvoz gRPC knjižnice
import grpc

# Thread pool za več sočasnih klientov
from concurrent import futures

# Generirane protobuf datoteke
import bayes_game_pb2
import bayes_game_pb2_grpc

# Toleranca zadetka:
# če je klient dovolj blizu žoge, štejemo kot zadetek
HIT_TOLERANCE = 1.0


# ============================================================
# RAZRED GameSession
# Hrani stanje ene igre
# ============================================================
class GameSession:

    # Konstruktor nove igre
    def __init__(self):

        # Naključna širina mize med 200 in 1000
        self.width = random.uniform(200, 1000)

        # Naključna višina mize med 200 in 1000
        self.height = random.uniform(200, 1000)

        # Naključna x koordinata žoge
        self.ball_x = random.uniform(0, self.width)

        # Naključna y koordinata žoge
        self.ball_y = random.uniform(0, self.height)

        # Število poskusov klienta
        self.attempts = 0


# ============================================================
# FUNKCIJA _direction
# Določi smer žoge glede na ugibanje klienta
# ============================================================
def _direction(ball_x: float, ball_y: float,
               guess_x: float, guess_y: float) -> int:

    # Razlika po x osi
    dx = ball_x - guess_x

    # Razlika po y osi
    dy = ball_y - guess_y

    # Če je x skoraj enak
    if abs(dx) < 1e-9:

        # Žoga je nad nami
        if dy > 0:
            return bayes_game_pb2.NORTH

        # Žoga je pod nami
        return bayes_game_pb2.SOUTH

    # Če je y skoraj enak
    if abs(dy) < 1e-9:

        # Žoga je desno
        if dx > 0:
            return bayes_game_pb2.EAST

        # Žoga je levo
        return bayes_game_pb2.WEST

    # Žoga je zgoraj desno
    if dx > 0 and dy > 0:
        return bayes_game_pb2.NORTHEAST

    # Žoga je spodaj desno
    if dx > 0 and dy < 0:
        return bayes_game_pb2.SOUTHEAST

    # Žoga je spodaj levo
    if dx < 0 and dy < 0:
        return bayes_game_pb2.SOUTHWEST

    # Sicer je zgoraj levo
    return bayes_game_pb2.NORTHWEST


# ============================================================
# gRPC SERVICER
# Implementacija RPC metod
# ============================================================
class BayesGameServicer(bayes_game_pb2_grpc.BayesGameServicer):

    # Konstruktor servicerja
    def __init__(self):

        # Slovar vseh aktivnih iger
        # ključ = game_id
        # vrednost = GameSession
        self.games: dict[str, GameSession] = {}

    # ========================================================
    # RPC METODA: StartGame
    # Začne novo igro
    # ========================================================
    def StartGame(self, request, context):

        # Generiramo unikaten ID igre
        game_id = str(uuid.uuid4())

        # Ustvarimo novo sejo igre
        session = GameSession()

        # Shranimo igro v slovar
        self.games[game_id] = session

        # Izpis informacij na serverju
        print(
            f"[{game_id[:8]}] Nova igra: "
            f"miza {session.width:.0f}x{session.height:.0f}, "
            f"žoga ({session.ball_x:.1f}, {session.ball_y:.1f})"
        )

        # Vrnemo game_id klientu
        return bayes_game_pb2.StartGameResponse(
            game_id=game_id
        )

    # ========================================================
    # RPC METODA: MakeGuess
    # Klient pošlje ugibanje
    # ========================================================
    def MakeGuess(self, request, context):

        # Preberemo ID igre
        game_id = request.game_id

        # Če igra ne obstaja
        if game_id not in self.games:

            # Nastavimo gRPC napako
            context.set_code(grpc.StatusCode.NOT_FOUND)

            # Opis napake
            context.set_details(
                "Neznana igra – najprej pokliči StartGame"
            )

            # Vrni prazen odgovor
            return bayes_game_pb2.GuessResponse()

        # Dobimo trenutno sejo igre
        session = self.games[game_id]

        # Povečamo število poskusov
        session.attempts += 1

        # Preberemo ugibanje klienta
        gx, gy = request.x, request.y

        # Izračun evklidske razdalje do žoge
        dist = (
            (gx - session.ball_x) ** 2 +
            (gy - session.ball_y) ** 2
        ) ** 0.5

        # Če smo dovolj blizu
        if dist <= HIT_TOLERANCE:

            # Izpis zadetka
            print(
                f"[{game_id[:8]}] "
                f"ZADETEK v {session.attempts} poskusih!"
            )

            # Odstranimo igro iz slovarja
            del self.games[game_id]

            # Vrni odgovor o koncu igre
            return bayes_game_pb2.GuessResponse(

                # Igre je konec
                game_over=True,

                # Koliko poskusov je bilo
                attempts=session.attempts,

                # Ni več smeri
                direction=bayes_game_pb2.UNKNOWN,
            )

        # Izračunamo smer žoge
        direction = _direction(
            session.ball_x,
            session.ball_y,
            gx,
            gy
        )

        # Izpis poskusa na serverju
        print(
            f"[{game_id[:8]}] "
            f"Poskus {session.attempts}: "
            f"({gx:.1f}, {gy:.1f}) → "
            f"{bayes_game_pb2.Direction.Name(direction)}"
        )

        # Vrni odgovor klientu
        return bayes_game_pb2.GuessResponse(

            # Igre še ni konec
            game_over=False,

            # Trenutno število poskusov
            attempts=session.attempts,

            # Smer žoge
            direction=direction,
        )


# ============================================================
# FUNKCIJA serve
# Zažene gRPC server
# ============================================================
def serve():

    # Ustvarimo gRPC server
    server = grpc.server(

        # Thread pool za več klientov
        futures.ThreadPoolExecutor(max_workers=10)
    )

    # Registriramo servis
    bayes_game_pb2_grpc.add_BayesGameServicer_to_server(
        BayesGameServicer(),
        server
    )

    # Poslušamo na portu 50052
    server.add_insecure_port("[::]:50052")

    # Zaženemo server
    server.start()

    # Izpis statusa
    print("Bayes gRPC server teče na portu 50052...")

    # Server teče neskončno
    server.wait_for_termination()


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":

    # Zaženemo server
    serve()