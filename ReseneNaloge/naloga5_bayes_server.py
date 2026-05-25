# ============================================================
# NALOGA 5: gRPC SERVER - Bayesovo iskanje žoge na mizi
# ============================================================
# Server ima mizo z naključnimi dimenzijami in skrito točko (žogo).
# Client ugiba (x, y); server vrne smer ali game_over ob zadetku.
# ============================================================

import uuid
import random
import grpc
from concurrent import futures

import bayes_game_pb2
import bayes_game_pb2_grpc

HIT_TOLERANCE = 1.0  # zadetek, če je ugibanje blizu žoge (float bisekcija)


class GameSession:
    """Stanje ene igre: dimenzije mize in pozicija žoge."""

    def __init__(self):
        self.width = random.uniform(200, 1000)
        self.height = random.uniform(200, 1000)
        self.ball_x = random.uniform(0, self.width)
        self.ball_y = random.uniform(0, self.height)
        self.attempts = 0


def _direction(ball_x: float, ball_y: float, guess_x: float, guess_y: float) -> int:
    """Vrne enum smeri: kje je žoga glede na ugibanje."""
    dx = ball_x - guess_x
    dy = ball_y - guess_y

    if abs(dx) < 1e-9:
        return bayes_game_pb2.NORTH if dy > 0 else bayes_game_pb2.SOUTH
    if abs(dy) < 1e-9:
        return bayes_game_pb2.EAST if dx > 0 else bayes_game_pb2.WEST
    if dx > 0 and dy > 0:
        return bayes_game_pb2.NORTHEAST
    if dx > 0 and dy < 0:
        return bayes_game_pb2.SOUTHEAST
    if dx < 0 and dy < 0:
        return bayes_game_pb2.SOUTHWEST
    return bayes_game_pb2.NORTHWEST


class BayesGameServicer(bayes_game_pb2_grpc.BayesGameServicer):
    def __init__(self):
        self.games: dict[str, GameSession] = {}

    def StartGame(self, request, context):
        game_id = str(uuid.uuid4())
        session = GameSession()
        self.games[game_id] = session
        print(
            f"[{game_id[:8]}] Nova igra: miza {session.width:.0f}x{session.height:.0f}, "
            f"žoga ({session.ball_x:.1f}, {session.ball_y:.1f})"
        )
        return bayes_game_pb2.StartGameResponse(game_id=game_id)

    def MakeGuess(self, request, context):
        game_id = request.game_id
        if game_id not in self.games:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Neznana igra – najprej pokliči StartGame")
            return bayes_game_pb2.GuessResponse()

        session = self.games[game_id]
        session.attempts += 1
        gx, gy = request.x, request.y

        dist = ((gx - session.ball_x) ** 2 + (gy - session.ball_y) ** 2) ** 0.5
        if dist <= HIT_TOLERANCE:
            print(f"[{game_id[:8]}] ZADETEK v {session.attempts} poskusih!")
            del self.games[game_id]
            return bayes_game_pb2.GuessResponse(
                game_over=True,
                attempts=session.attempts,
                direction=bayes_game_pb2.UNKNOWN,
            )

        direction = _direction(session.ball_x, session.ball_y, gx, gy)
        print(
            f"[{game_id[:8]}] Poskus {session.attempts}: ({gx:.1f}, {gy:.1f}) → "
            f"{bayes_game_pb2.Direction.Name(direction)}"
        )
        return bayes_game_pb2.GuessResponse(
            game_over=False,
            attempts=session.attempts,
            direction=direction,
        )


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    bayes_game_pb2_grpc.add_BayesGameServicer_to_server(BayesGameServicer(), server)
    server.add_insecure_port("[::]:50052")
    server.start()
    print("Bayes gRPC server teče na portu 50052...")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
