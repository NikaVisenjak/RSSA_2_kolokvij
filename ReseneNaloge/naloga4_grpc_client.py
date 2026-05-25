# ============================================================
# NALOGA 4: gRPC CLIENT - igra ugibanja
# ============================================================

import grpc
import guessing_game_pb2
import guessing_game_pb2_grpc

def play_game(stub, a: int, b: int, num_rounds: int = 5):
    """
    Igra ugibanja: client pošlje meje, server žreba in preveri.
    
    stub: gRPC stub objekt - "proxy" za klicanje serverjevih metod
          Izgleda kot lokalni objekt, ampak klici gredo čez mrežo!
    """
    print(f"\n=== Začenjamo igro: a={a}, b={b}, {num_rounds} krogov ===")
    
    for round_num in range(1, num_rounds + 1):
        # Pošljemo GameRequest na server
        # To je kot klic lokalne funkcije, ampak gre čez mrežo
        request = guessing_game_pb2.GameRequest(a=a, b=b)
        
        try:
            # stub.PlayGame() kliče serverjev PlayGame() RPC
            # Blokirajoč klic - čaka na odgovor serverja
            result = stub.PlayGame(request)
            
            print(f"  Krog {round_num}: "
                  f"Skrivno={result.secret_number}, "
                  f"{'ZADEL ✓' if result.correct else 'ZGREŠIL ✗'} | "
                  f"Točke: Jaz={result.player_score}, Server={result.server_score}")
                  
        except grpc.RpcError as e:
            # RpcError se sproži pri gRPC napakah (connection refused, timeout...)
            print(f"  gRPC napaka: {e.code()}: {e.details()}")
            break
    
    print(f"  Končni rezultat: Jaz={result.player_score}, "
          f"Server={result.server_score}/{result.total_games} iger")

def interactive_guess(stub, a: int, b: int):
    """
    Interaktivno ugibanje: user vnese ugibanje, server vrne rezultat.
    """
    print(f"\n=== Interaktivno ugibanje: a={a}, b={b} ===")
    print(f"Ugibajte število med {a} in {b}!")
    
    while True:
        try:
            guess = int(input(f"Vaše ugibanje ({a}-{b}): "))
        except ValueError:
            print("Prosim vnesite celo število!")
            continue
        
        # Pošljemo ugibanje na server
        request = guessing_game_pb2.GuessRequest(a=a, b=b, guess=guess)
        result = stub.SubmitGuess(request)
        
        if result.correct:
            print(f"  ✓ PRAVILNO! Točke: Jaz={result.player_score}, Server={result.server_score}")
            break
        else:
            print(f"  ✗ Napačno! Skrivno={result.secret_number}. "
                  f"Točke: Jaz={result.player_score}, Server={result.server_score}")
            
            odgovor = input("Igraj znova? (d/n): ")
            if odgovor.lower() != 'd':
                break

def main():
    # Ustvarimo insecure channel do serverja
    # "localhost:50051" = naslov serverja
    # insecure_channel = brez TLS/SSL (za razvoj OK, v produkciji NE!)
    channel = grpc.insecure_channel("localhost:50051")
    
    # Stub je "klient stub" - objekt ki omogoča klicanje serverjevih metod
    # Generiran avtomatično iz .proto datoteke
    stub = guessing_game_pb2_grpc.GuessingGameStub(channel)
    
    # Zaženemo avtomatsko igro
    play_game(stub, a=1, b=100, num_rounds=5)
    
    # Zaženemo interaktivno igro
    interactive_guess(stub, a=1, b=10)
    
    # Zapremo channel ko smo končali
    channel.close()

if __name__ == "__main__":
    main()
