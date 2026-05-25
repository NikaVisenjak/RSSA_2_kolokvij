"""
Vaja 2: TimeSeries ASN.1 razred
Vaja 3: Pošiljanje na strežnik
Vaja 4: Strežnik
"""

import socket
import sys
from pyasn1.type import univ, namedtype, constraint, char
from pyasn1.codec.der import encoder, decoder

# ─── Vaja 2: ASN.1 razred ────────────────────────────────────────────────────

class SensorValues(univ.SequenceOf):
    """Zaporedje realnih vrednosti."""
    componentType = univ.Real()

class TimeSeries(univ.Sequence):
    """
    TimeSeries ::= SEQUENCE {
        sensorID  INTEGER,
        type      UTF8String,   -- "Temperature" ali "Pressure"
        values    SEQUENCE OF REAL
    }
    """
    componentType = namedtype.NamedTypes(
        namedtype.NamedType("sensorID", univ.Integer()),
        namedtype.NamedType("type",     char.UTF8String().subtype(
            subtypeSpec=constraint.SingleValueConstraint("Temperature", "Pressure")
        )),
        namedtype.NamedType("values",   SensorValues()),
    )


# ─── Vaja 3: Odjemalec ───────────────────────────────────────────────────────

def posji_na_streznik(host: str, port: int, der_data: bytes) -> str:
    """Pošlje DER-kodirane podatke na strežnik in vrne odgovor."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        s.sendall(der_data)
        s.shutdown(socket.SHUT_WR)  # sporoči konec pošiljanja
        odgovor = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            odgovor += chunk
    return odgovor.decode("utf-8", errors="replace")


def vaja3():
    """Ustvari instanco TimeSeries in jo pošlje na strežnik."""
    print("=== Vaja 3: Pošiljanje ===\n")

    # Instanca
    ts = TimeSeries()
    ts["sensorID"] = 42
    ts["type"]     = "Temperature"

    vrednosti = SensorValues()
    for i, v in enumerate([21.5, 22.0, 22.3, 21.8, 23.1,
                            22.7, 21.9, 22.5, 23.0, 22.2]):
        vrednosti[i] = univ.Real(v)
    ts["values"] = vrednosti

    print(f"  sensorID : {ts['sensorID']}")
    print(f"  type     : {ts['type']}")
    print(f"  values   : {[float(ts['values'][i]) for i in range(len(ts['values']))]}")

    # Kodiranje
    der = encoder.encode(ts)
    print(f"\n  DER (hex): {der.hex()}")
    print(f"  Dolžina  : {len(der)} bajtov")

    # Kaj se zgodi z Type = "Current"? (neveljavna vrednost)
    print("\n  Poskus Type = 'Current':")
    try:
        bad = TimeSeries()
        bad["sensorID"] = 1
        bad["type"]     = "Current"
        bad["values"]   = SensorValues()
        encoder.encode(bad)
        print("  (brez napake — constraint se preveri šele pri kodiranju)")
    except Exception as e:
        print(f"  ✗ Napaka (pričakovano): {e}")

    # Pošlji na strežnik
    HOST, PORT = "127.0.0.1", 22222
    print(f"\n  Pošiljam na {HOST}:{PORT} ...")
    try:
        odgovor = posji_na_streznik(HOST, PORT, der)
        print(f"  ✅ Odgovor strežnika: {odgovor}")
    except Exception as e:
        print(f"  ✗ Napaka pri pošiljanju: {e}")


# ─── Vaja 4: Strežnik ────────────────────────────────────────────────────────

def vaja4_streznik(host: str = "0.0.0.0", port: int = 22222):
    """
    Strežnik, ki sprejme DER-kodirano sporočilo TimeSeries,
    ga dekodira in odgovori, ali je format pravilen.
    """
    print(f"=== Vaja 4: Strežnik na {host}:{port} ===\n")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((host, port))
        srv.listen(5)
        print(f"  Poslušam ... (Ctrl+C za izhod)\n")

        while True:
            conn, addr = srv.accept()
            with conn:
                print(f"  Povezava od: {addr}")
                data = b""
                while True:
                    chunk = conn.recv(4096)
                    if not chunk:
                        break
                    data += chunk

                print(f"  Prejeto ({len(data)} B): {data.hex()}")

                try:
                    obj, remainder = decoder.decode(data, asn1Spec=TimeSeries())

                    if remainder:
                        raise ValueError("Ostali neprebrani bajti po dekodiranju.")

                    # Validacija omejitev
                    tip = str(obj["type"])
                    if tip not in ("Temperature", "Pressure"):
                        raise ValueError(f"Neveljaven type: '{tip}'")

                    st_vrednosti = len(obj["values"])
                    print(f"  ✅ Format OK!")
                    print(f"     sensorID : {obj['sensorID']}")
                    print(f"     type     : {tip}")
                    print(f"     values   : {st_vrednosti} vrednosti")

                    odgovor = (
                        f"OK: sensorID={obj['sensorID']}, "
                        f"type={tip}, "
                        f"values={st_vrednosti} vrednosti"
                    )

                except Exception as e:
                    print(f"  ✗ Napaka: {e}")
                    odgovor = f"NAPAKA: {e}"

                conn.sendall(odgovor.encode("utf-8"))
                print(f"  Odgovor poslan: {odgovor}\n")


# ─── Vstopna točka ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "streznik":
        vaja4_streznik()
    else:
        # Vaja 2: prikaz razreda
        print("=== Vaja 2: TimeSeries razred ===")
        ts = TimeSeries()
        ts["sensorID"] = 1
        ts["type"]     = "Pressure"
        v = SensorValues()
        for i, val in enumerate([1.0, 2.0, 3.0]):
            v[i] = univ.Real(val)
        ts["values"] = v
        enc = encoder.encode(ts)
        print(f"  Primer DER: {enc.hex()}\n")

        # Vaja 3: pošiljanje
        vaja3()
