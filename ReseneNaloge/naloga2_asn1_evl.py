# ============================================================
# NALOGA 2: ASN.1 objekt za EVL Inc.
# ============================================================
# ASN.1 = Abstract Syntax Notation One
# Je standardni jezik za opis podatkovnih struktur neodvisno
# od platforme, programskega jezika in prenosa.
#
# ZAKAJ ASN.1 za to nalogo?
# - Antarktika <-> Japonska: zelo omejena pasovna širina
# - Fax naprava: prenos mora biti kompakten (DER encoding)
# - DER (Distinguished Encoding Rules): binarna, kompaktna oblika
#   ki je standardizirana (vedno enako kodiranje za iste podatke)
#
# SMOTRNA REŠITEV:
# - Vrednosti (3001, 4001...) kodiramo kot ENUMERATED (samo indeks!)
#   namesto celotnega INTEGER -> prihranimo bajte
# - Akcija: BOOLEAN (takoj=TRUE, kasneje=FALSE)
# ============================================================

# pip install pyasn1
from pyasn1.type import univ, namedtype, namedval, constraint
# univ       - osnovni ASN.1 tipi (Integer, Boolean, Sequence...)
# namedtype  - za poimenovana polja v SEQUENCE
# namedval   - za ENUMERATED vrednosti
# constraint - za omejitve vrednosti

# -------------------------------------------------------
# ENUMERATED tip za rakete
# ENUMERATED je kot enum v Pythonu - shranjuje se samo indeks (0,1,2)
# ne pa dejanska vrednost! To prihrani prostor pri prenosu.
# -------------------------------------------------------
class RocketCount(univ.Enumerated):
    # namedValues poveže ime z indeksom
    namedValues = namedval.NamedValues(
        ('rockets_3001', 0),   # indeks 0 = 3001 raket
        ('rockets_4001', 1),   # indeks 1 = 4001 raket
        ('rockets_5003', 2),   # indeks 2 = 5003 raket
    )
    # subtypeSpec omeji veljavne vrednosti na 0, 1 ali 2
    subtypeSpec = univ.Enumerated.subtypeSpec + \
                  constraint.SingleValueConstraint(0, 1, 2)

class BombCount(univ.Enumerated):
    namedValues = namedval.NamedValues(
        ('bombs_1019', 0),
        ('bombs_2003', 1),
        ('bombs_5009', 2),
    )
    subtypeSpec = univ.Enumerated.subtypeSpec + \
                  constraint.SingleValueConstraint(0, 1, 2)

class ChocolateCount(univ.Enumerated):
    namedValues = namedval.NamedValues(
        ('choc_1009', 0),
        ('choc_1499', 1),
        ('choc_2011', 2),
    )
    subtypeSpec = univ.Enumerated.subtypeSpec + \
                  constraint.SingleValueConstraint(0, 1, 2)

# -------------------------------------------------------
# Glavni ASN.1 objekt - SEQUENCE (kot struct v C)
# SEQUENCE vsebuje polja v določenem vrstnem redu
# -------------------------------------------------------
class EVLOrder(univ.Sequence):
    # componentType definira polja SEQUENCE objekta
    componentType = namedtype.NamedTypes(
        # Vsako polje ima ime in tip
        namedtype.NamedType('rockets',    RocketCount()),     # katera vrednost raket
        namedtype.NamedType('bombs',      BombCount()),       # katera vrednost bomb
        namedtype.NamedType('chocolates', ChocolateCount()),  # katera vrednost čokolad
        namedtype.NamedType('immediate',  univ.Boolean()),    # TRUE=takoj, FALSE=kasneje
    )

# -------------------------------------------------------
# Primer uporabe: kodiranje in dekodiranje
# -------------------------------------------------------
if __name__ == "__main__":
    from pyasn1.codec.der.encoder import encode as der_encode
    # der_encode: pretvori ASN.1 objekt v DER bajte
    from pyasn1.codec.der.decoder import decode as der_decode
    # der_decode: pretvori DER bajte nazaj v ASN.1 objekt

    # --- KODIRANJE (Antarktika pošilja) ---
    order = EVLOrder()
    
    # Nastavimo polja po imenu
    order['rockets']    = RocketCount('rockets_4001')   # 4001 raket
    order['bombs']      = BombCount('bombs_2003')        # 2003 bomb
    order['chocolates'] = ChocolateCount('choc_1499')   # 1499 čokolad
    order['immediate']  = univ.Boolean(True)             # akcija takoj!

    # Kodiramo v DER binarni format
    encoded = der_encode(order)
    print(f"DER kodirani bajti (hex): {encoded.hex()}")
    print(f"Velikost sporočila: {len(encoded)} bajtov")
    # PRIMERJAVA: če bi poslali ASCII "4001,2003,1499,true" = 18 bajtov
    # DER bo manjši - to je ključno za fax/omejeno zvezo!

    # --- DEKODIRANJE (Japonska prejme) ---
    # der_decode vrne tuple: (dekodirani_objekt, preostali_bajti)
    decoded_order, remainder = der_decode(encoded, asn1Spec=EVLOrder())
    # asn1Spec pove dekoderju kakšno strukturo pričakuje

    # Izpišemo dekodirane vrednosti
    print("\nDekodirani ukaz:")
    print(f"  Rakete:    {decoded_order['rockets'].prettyPrint()}")
    print(f"  Bombe:     {decoded_order['bombs'].prettyPrint()}")
    print(f"  Čokolade:  {decoded_order['chocolates'].prettyPrint()}")
    print(f"  Takoj:     {bool(decoded_order['immediate'])}")
