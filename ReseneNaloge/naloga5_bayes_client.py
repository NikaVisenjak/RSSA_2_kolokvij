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

import grpc
import bayes_game_pb2
import bayes_game_pb2_grpc

def play_with_bisection(stub):
    """
    Igra z bisekcijsko strategijo - minimizira število poskusov.
    """
    # --- Začni igro ---
    start_resp = stub.StartGame(bayes_game_pb2.StartGameRequest())
    game_id = start_resp.game_id
    print(f"Igra {game_id} začeta!")
    
    # --- Inicializacija iskalnega prostora ---
    # Ker ne vemo dimenzij mize, začnemo z velikim prostorom
    # Ko dobimo prve napotke, se bo prostor zoužal
    x_min, x_max = 0.0, 2000.0   # začetni x razpon (konzervativna ocena)
    y_min, y_max = 0.0, 2000.0   # začetni y razpon
    
    attempts = 0
    MAX_ATTEMPTS = 100  # varnostna meja
    
    while attempts < MAX_ATTEMPTS:
        # Naslednje ugibanje = SREDINA trenutnega iskalnega prostora
        # To je optimalna strategija - vsaka ugibanje razpolovi prostor
        guess_x = (x_min + x_max) / 2.0
        guess_y = (y_min + y_max) / 2.0
        
        print(f"\nFaza {attempts+1}: Ugibam ({guess_x:.1f}, {guess_y:.1f}) | "
              f"Prostor: x=[{x_min:.0f},{x_max:.0f}], y=[{y_min:.0f},{y_max:.0f}]")
        
        # Pošljemo ugibanje serverju
        resp = stub.MakeGuess(bayes_game_pb2.GuessRequest(
            game_id = game_id,
            x       = guess_x,
            y       = guess_y,
        ))
        
        attempts += 1
        
        if resp.game_over:
            # HIT! Zadeli smo!
            print(f"\n✓ ZADELI! Potrebovali smo {resp.attempts} poskusov!")
            return attempts
        
        # --- Posodobimo iskalni prostor glede na smer ---
        # direction nam pove kje je žoga RELATIVNO NA naše ugibanje
        d = resp.direction
        
        if d == bayes_game_pb2.NORTH:
            # Žoga je NAD nami -> dvignemo spodnjo mejo y
            y_min = guess_y
            print(f"  ↑ SEVER: dvigam y_min na {y_min:.0f}")
            
        elif d == bayes_game_pb2.SOUTH:
            # Žoga je POD nami -> znižamo zgornjo mejo y
            y_max = guess_y
            print(f"  ↓ JUG: znižam y_max na {y_max:.0f}")
            
        elif d == bayes_game_pb2.EAST:
            # Žoga je DESNO -> povečamo spodnjo mejo x
            x_min = guess_x
            print(f"  → VZHOD: dvigam x_min na {x_min:.0f}")
            
        elif d == bayes_game_pb2.WEST:
            # Žoga je LEVO -> znižamo zgornjo mejo x
            x_max = guess_x
            print(f"  ← ZAHOD: znižam x_max na {x_max:.0f}")
            
        elif d == bayes_game_pb2.NORTHEAST:
            # Žoga je DESNO IN ZGORAJ -> oba popravka
            x_min = guess_x
            y_min = guess_y
            print(f"  ↗ SEVERO-VZHOD: x_min={x_min:.0f}, y_min={y_min:.0f}")
            
        elif d == bayes_game_pb2.SOUTHEAST:
            x_min = guess_x
            y_max = guess_y
            print(f"  ↘ JUGO-VZHOD: x_min={x_min:.0f}, y_max={y_max:.0f}")
            
        elif d == bayes_game_pb2.SOUTHWEST:
            x_max = guess_x
            y_max = guess_y
            print(f"  ↙ JUGO-ZAHOD: x_max={x_max:.0f}, y_max={y_max:.0f}")
            
        elif d == bayes_game_pb2.NORTHWEST:
            x_max = guess_x
            y_min = guess_y
            print(f"  ↖ SEVERO-ZAHOD: x_max={x_max:.0f}, y_min={y_min:.0f}")
        
        # Varnostno preverjanje: če se prostor ne zoužuje, je problem
        width  = x_max - x_min
        height = y_max - y_min
        print(f"  Preostali prostor: {width:.0f} x {height:.0f} enot")
    
    print(f"Presegli smo max poskusov ({MAX_ATTEMPTS})")
    return attempts

def main():
    # Povežemo se na Bayes server (port 50052)
    channel = grpc.insecure_channel("localhost:50052")
    stub    = bayes_game_pb2_grpc.BayesGameStub(channel)
    
    print("=== Bayesova igra iskanja žoge ===")
    print("Strategija: iterativna bisekcija iskalnega prostora\n")
    
    total_attempts = play_with_bisection(stub)
    print(f"\nUčinkovitost: zadeli v {total_attempts} korakih")
    
    channel.close()

if __name__ == "__main__":
    main()
