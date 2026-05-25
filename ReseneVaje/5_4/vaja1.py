"""
Vaja 1: ASN.1 razredi z pyasn1
"""

from pyasn1.type import univ, namedtype, constraint, char

# ─── (a) DanVTednu ───────────────────────────────────────────────────────────
# Subtype od UTF8String, ker "č" (šumnik) zahteva UTF-8 encoding.
# VisibleString / IA5String ne podpirata neangleških znakov!

class DanVTednu(char.UTF8String):
    subtypeSpec = constraint.ConstraintsUnion(
        constraint.SingleValueConstraint(
            "ponedeljek", "torek", "sreda", "četrtek", "petek", "sobota", "nedelja"
        )
    )


# ─── (b) Datum ───────────────────────────────────────────────────────────────
# Sequence treh poimenovanih integerjev (brez omejitev)

class Datum(univ.Sequence):
    componentType = namedtype.NamedTypes(
        namedtype.NamedType("leto",   univ.Integer()),
        namedtype.NamedType("mesec",  univ.Integer()),
        namedtype.NamedType("dan",    univ.Integer()),
    )


# ─── (c) Datum2 ──────────────────────────────────────────────────────────────
# Najprej ločeni razredi z omejitvami, nato Sequence

class Leto(univ.Integer):
    subtypeSpec = constraint.ValueRangeConstraint(0, 2026)

class Mesec(univ.Integer):
    subtypeSpec = constraint.ValueRangeConstraint(1, 12)

class Dan(univ.Integer):
    subtypeSpec = constraint.ValueRangeConstraint(1, 31)

class Datum2(univ.Sequence):
    componentType = namedtype.NamedTypes(
        namedtype.NamedType("leto",   Leto()),
        namedtype.NamedType("mesec",  Mesec()),
        namedtype.NamedType("dan",    Dan()),
    )


# ─── Test ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from pyasn1.codec.der import encoder, decoder

    print("=== (a) DanVTednu ===")
    for dan in ["ponedeljek", "četrtek", "nedelja"]:
        d = DanVTednu(dan)
        enc = encoder.encode(d)
        print(f"  {dan:12s} → HEX: {enc.hex()}")

    print("\n  Napačna vrednost ('monday'):")
    try:
        bad = DanVTednu("monday")
        encoder.encode(bad)
    except Exception as e:
        print(f"  ✗ Napaka (pričakovano): {e}")

    print("\n=== (b) Datum ===")
    d = Datum()
    d["leto"]  = 2025
    d["mesec"] = 5
    d["dan"]   = 25
    enc = encoder.encode(d)
    print(f"  2025-05-25 → HEX: {enc.hex()}")
    dec, _ = decoder.decode(enc, asn1Spec=Datum())
    print(f"  Dekodirano: leto={dec['leto']}, mesec={dec['mesec']}, dan={dec['dan']}")

    print("\n=== (c) Datum2 ===")
    d2 = Datum2()
    d2["leto"]  = 2024
    d2["mesec"] = 12
    d2["dan"]   = 31
    enc2 = encoder.encode(d2)
    print(f"  2024-12-31 → HEX: {enc2.hex()}")
    dec2, _ = decoder.decode(enc2, asn1Spec=Datum2())
    print(f"  Dekodirano: leto={dec2['leto']}, mesec={dec2['mesec']}, dan={dec2['dan']}")

    print("\n  Napačen mesec (13):")
    try:
        bad2 = Datum2()
        bad2["leto"]  = 2024
        bad2["mesec"] = 13
        bad2["dan"]   = 1
        encoder.encode(bad2)
    except Exception as e:
        print(f"  ✗ Napaka (pričakovano): {e}")
