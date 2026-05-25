# ============================================================
# NALOGA 3: Preverjanje in popravljanje DER objektov
# ============================================================
# House ASN.1 definicija:
#   House ::= SEQUENCE {
#     rooms   INTEGER (1..4),
#     windows INTEGER (5..8),
#     doors   INTEGER (7..11),
#     sockets INTEGER (9..13)
#   }
#
# DER (Distinguished Encoding Rules) format bajt po bajt:
#
# SEQUENCE tag: 0x30
# INTEGER  tag: 0x02
#
# Format vsakega polja:
#   [TAG byte] [LENGTH byte] [VALUE byte(s)]
#
# Primer: INTEGER vrednost 3:
#   0x02  0x01  0x03
#   ^TAG  ^LEN  ^VAL
#
# Celotna SEQUENCE:
#   0x30 [skupna dolžina vsebine]
#   0x02 0x01 [rooms]
#   0x02 0x01 [windows]
#   0x02 0x01 [doors]
#   0x02 0x01 [sockets]
# ============================================================

from pyasn1.type import univ, namedtype, constraint
from pyasn1.codec.der.encoder import encode as der_encode
from pyasn1.codec.der.decoder import decode as der_decode
from pyasn1.error import SubstrateUnderrunError, PyAsn1Error

# -------------------------------------------------------
# Definicija House ASN.1 objekta
# -------------------------------------------------------
class House(univ.Sequence):
    componentType = namedtype.NamedTypes(
        namedtype.NamedType(
            'rooms',
            univ.Integer().subtype(
                # ValueRangeConstraint(min, max) - definira veljavni razpon
                subtypeSpec=constraint.ValueRangeConstraint(1, 4)
            )
        ),
        namedtype.NamedType(
            'windows',
            univ.Integer().subtype(
                subtypeSpec=constraint.ValueRangeConstraint(5, 8)
            )
        ),
        namedtype.NamedType(
            'doors',
            univ.Integer().subtype(
                subtypeSpec=constraint.ValueRangeConstraint(7, 11)
            )
        ),
        namedtype.NamedType(
            'sockets',
            univ.Integer().subtype(
                subtypeSpec=constraint.ValueRangeConstraint(9, 13)
            )
        ),
    )

# -------------------------------------------------------
# Funkcija za preverjanje DER bajt-po-bajt (ročno)
# -------------------------------------------------------
def analyze_der_bytes(data: bytes, label: str = ""):
    """
    Ročna analiza DER struktury bajt po bajt.
    Pomaga ugotoviti kje so napake v kodiranju.
    """
    print(f"\n=== Analiza {label} ===")
    print(f"Hex: {data.hex()}")
    print(f"Bajti: {list(data)}")
    
    i = 0  # indeks trenutnega bajta
    
    # 1. bajt mora biti SEQUENCE tag (0x30 = 48)
    if i < len(data):
        tag = data[i]
        print(f"\n[{i}] TAG: 0x{tag:02x}", end=" ")
        if tag == 0x30:
            print("✓ (SEQUENCE)")
        else:
            print(f"✗ (Pričakovan 0x30 za SEQUENCE, dobili {hex(tag)})")
        i += 1
    
    # 2. bajt je dolžina vsebine SEQUENCE
    if i < len(data):
        seq_len = data[i]
        print(f"[{i}] SEQUENCE dolžina: {seq_len}")
        i += 1
    
    # Preberi vsako INTEGER polje
    field_names = ['rooms (1-4)', 'windows (5-8)', 'doors (7-11)', 'sockets (9-13)']
    field_ranges = [(1,4), (5,8), (7,11), (9,13)]
    
    for idx, (fname, (fmin, fmax)) in enumerate(zip(field_names, field_ranges)):
        if i >= len(data):
            print(f"  NAPAKA: Manjka polje {fname}")
            break
            
        # INTEGER tag
        tag = data[i]
        print(f"\n[{i}] TAG: 0x{tag:02x}", end=" ")
        if tag == 0x02:
            print("✓ (INTEGER)")
        else:
            print(f"✗ (Pričakovan 0x02 za INTEGER)")
        i += 1
        
        # Dolžina
        if i < len(data):
            length = data[i]
            print(f"[{i}] Dolžina: {length}")
            i += 1
        
        # Vrednost
        if i < len(data) and length:
            value = int.from_bytes(data[i:i+length], byteorder='big', signed=True)
            valid = fmin <= value <= fmax
            print(f"[{i}] Vrednost: {value} {'✓' if valid else f'✗ (mora biti {fmin}..{fmax})'}")
            i += length

# -------------------------------------------------------
# Funkcija za popravljanje in validacijo House objekta
# -------------------------------------------------------
def verify_and_fix_house(filename: str):
    """
    Prebere DER datoteko, poskusi dekodirati in preveri vrednosti.
    Če so vrednosti zunaj obsega, jih popravi na veljavne.
    """
    print(f"\n{'='*50}")
    print(f"Preverjam: {filename}")
    
    # Preberemo raw bajte iz datoteke
    try:
        with open(filename, 'rb') as f:  # 'rb' = read binary
            raw_bytes = f.read()
    except FileNotFoundError:
        print(f"Datoteka {filename} ne obstaja - ustvarjam testni primer")
        # Ustvarimo testni DER z namernimi napakami za demonstracijo
        raw_bytes = create_test_der_with_errors()
    
    # Analiziramo bajte ročno
    analyze_der_bytes(raw_bytes, filename)
    
    # Poskusimo dekodirati z pyasn1
    print(f"\n--- Dekodiranje z pyasn1 ---")
    try:
        # der_decode vrne (objekt, preostali_bajti)
        house, remainder = der_decode(raw_bytes, asn1Spec=House())
        
        print("Dekodirano uspešno!")
        print(f"  rooms:   {int(house['rooms'])}")
        print(f"  windows: {int(house['windows'])}")
        print(f"  doors:   {int(house['doors'])}")
        print(f"  sockets: {int(house['sockets'])}")
        
        # Preverimo constraint-e ročno (pyasn1 jih ne vedno uveljavlja)
        errors = []
        if not (1 <= int(house['rooms']) <= 4):
            errors.append(f"rooms={int(house['rooms'])} ni v [1..4]")
        if not (5 <= int(house['windows']) <= 8):
            errors.append(f"windows={int(house['windows'])} ni v [5..8]")
        if not (7 <= int(house['doors']) <= 11):
            errors.append(f"doors={int(house['doors'])} ni v [7..11]")
        if not (9 <= int(house['sockets']) <= 13):
            errors.append(f"sockets={int(house['sockets'])} ni v [9..13]")
        
        if errors:
            print(f"\nNAPAKE V VREDNOSTIH:")
            for e in errors:
                print(f"  ✗ {e}")
            return house, False
        else:
            print("  ✓ Vse vrednosti so v veljavnem obsegu!")
            return house, True
            
    except PyAsn1Error as e:
        print(f"Napaka pri dekodiranju: {e}")
        return None, False

# -------------------------------------------------------
# Ustvari pravilno kodiran House DER (za referenco)
# -------------------------------------------------------
def create_correct_house(rooms=2, windows=6, doors=9, sockets=11):
    """
    Ustvari pravilno kodiran House ASN.1 DER objekt.
    Vrednosti morajo biti v veljavnih obsegih!
    """
    house = House()
    house['rooms']   = rooms    # 1..4
    house['windows'] = windows  # 5..8
    house['doors']   = doors    # 7..11
    house['sockets'] = sockets  # 9..13
    
    encoded = der_encode(house)
    print(f"\nPravilen DER (rooms={rooms}, windows={windows}, "
          f"doors={doors}, sockets={sockets}):")
    print(f"  Hex: {encoded.hex()}")
    print(f"  Bajti: {list(encoded)}")
    return encoded

def create_test_der_with_errors():
    """Ustvari DER bajte z namerno napačno vrednostjo za demonstracijo."""
    # Ročno zgradimo napačen DER:
    # rooms=2 (OK), windows=3 (NAPAKA! mora biti 5-8), doors=9 (OK), sockets=11 (OK)
    return bytes([
        0x30, 0x0c,        # SEQUENCE, dolžina 12
        0x02, 0x01, 0x02,  # INTEGER rooms = 2 ✓
        0x02, 0x01, 0x03,  # INTEGER windows = 3 ✗ (mora biti 5-8!)
        0x02, 0x01, 0x09,  # INTEGER doors = 9 ✓
        0x02, 0x01, 0x0b,  # INTEGER sockets = 11 ✓
    ])

if __name__ == "__main__":
    # Prikažemo pravilno kodiranje za referenco
    print("=== Referenčni pravilni DER objekt ===")
    correct_der = create_correct_house(rooms=2, windows=6, doors=9, sockets=11)
    
    # Preverimo house1.txt in house2.txt (DER je binaren, ne txt!)
    # V resnici bi bili to .der datoteke
    for fname in ["house1.der", "house2.der"]:
        verify_and_fix_house(fname)
    
    # Demonstracija ročne analize napačnega objekta
    print("\n\n=== Demonstracija analize napačnega DER ===")
    bad_der = create_test_der_with_errors()
    analyze_der_bytes(bad_der, "napačen primer")
