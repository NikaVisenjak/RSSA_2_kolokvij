# ============================================================
# NALOGA 4: gRPC SERVER - igra ugibanja
# ============================================================
# gRPC = Google Remote Procedure Call
# Deluje tako:
#   1. Definiramo vmesnik v .proto datoteki
#   2. Generiramo Python kodo iz .proto:
#      python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. guessing_game.proto
#   3. Server implementira metode iz .proto
#   4. Client kliče te metode kot da so lokalne funkcije
# ============================================================

import grpc          # gRPC knjižnica
import random        # za naključno žrebanje števila
from concurrent import futures  # za thread pool (gRPC je večniten)

# Uvozimo generirano kodo iz .proto datoteke
# (generirano z protoc ukazom)
import guessing_game_pb2        # definicije sporočil (messages)
import guessing_game_pb2_grpc   # definicije servisov (servicer razredi)

# -------------------------------------------------------
# Stanje igre - skupno za vse klice (globalni objekt)
# V produkciji bi bil to DB ali session store
# -------------------------------------------------------
class GameState:
    def __init__(self):
        self.player_score = 0  # skupne točke igralca
        self.server_score = 0  # skupne točke serverja
        self.total_games  = 0  # skupno število odigranih iger

# Globalna instanca - deli stanje med vsemi RPC klici
game_state = GameState()

# -------------------------------------------------------
# Implementacija serverja - podedujemo od generiranega razreda
# GuessingGameServicer je abstraktni razred generiran iz .proto
# -------------------------------------------------------
class GuessingGameServicer(guessing_game_pb2_grpc.GuessingGameServicer):
    
    def PlayGame(self, request, context):
        """
        RPC metoda: server sam žrebi število in preverja.
        request: GameRequest objekt (vsebuje a in b)
        context: gRPC kontekst (metapodatki, status...)
        """
        a = request.a  # spodnja meja
        b = request.b  # zgornja meja
        
        # Validacija vhodnih podatkov
        if a >= b:
            # set_code postavi gRPC error status
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("a mora biti manjši od b")
            return guessing_game_pb2.GameResult()  # prazen odgovor
        
        # Server žreba naključno število med a in b (vključno)
        secret = random.randint(a, b)
        
        # Za demonstracijo: server si "izmisli" ugibanje
        # V pravi igri bi client poslal ugibanje ločeno
        player_guess = (a + b) // 2  # sredinska vrednost kot "ugibanje"
        
        correct = (player_guess == secret)
        
        # Posodobimo točke
        game_state.total_games += 1
        if correct:
            game_state.player_score += 1
        else:
            game_state.server_score += 1
        
        # Vrnemo GameResult protobuf sporočilo
        return guessing_game_pb2.GameResult(
            correct       = correct,
            secret_number = secret,
            player_score  = game_state.player_score,
            server_score  = game_state.server_score,
            total_games   = game_state.total_games,
        )
    
    def SubmitGuess(self, request, context):
        """
        RPC metoda: client pošlje svojo ugibanje.
        """
        a     = request.a
        b     = request.b
        guess = request.guess
        
        # Server žreba skrivno število
        secret = random.randint(a, b)
        correct = (guess == secret)
        
        game_state.total_games += 1
        if correct:
            game_state.player_score += 1
        else:
            game_state.server_score += 1
        
        return guessing_game_pb2.GameResult(
            correct       = correct,
            secret_number = secret,
            player_score  = game_state.player_score,
            server_score  = game_state.server_score,
            total_games   = game_state.total_games,
        )

# -------------------------------------------------------
# Zagon serverja
# -------------------------------------------------------
def serve():
    # ThreadPoolExecutor: gRPC server z max 10 vzporednimi niti
    # Vsak RPC klic dobi svojo nit iz poola
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    
    # Registriramo našo implementacijo v server
    guessing_game_pb2_grpc.add_GuessingGameServicer_to_server(
        GuessingGameServicer(),  # naša implementacija
        server                    # server objekt
    )
    
    # Server posluša na portu 50051 (standardni gRPC port)
    # "[::]:50051" = posluša na vseh mrežnih vmesnikih (IPv4 in IPv6)
    server.add_insecure_port("[::]:50051")  # insecure = brez TLS
    
    server.start()
    print("gRPC server teče na portu 50051...")
    
    # wait_for_termination() blokira dokler server ne dobi SIGTERM/SIGINT
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
