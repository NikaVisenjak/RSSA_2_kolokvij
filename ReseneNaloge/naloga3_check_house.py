"""
ASN.1 DER dekoder, validator in popravljalnik za objekt House.

House ::= SEQUENCE {
    rooms   INTEGER (1..4),
    windows INTEGER (5..8),
    doors   INTEGER (7..11),
    sockets INTEGER (9..13)
}
"""

# --- Omejitve polj ---
FIELDS = [
    ("rooms",   1,  4),
    ("windows", 5,  8),
    ("doors",   7, 11),
    ("sockets", 9, 13),
]

# Privzete veljavne vrednosti za popravek (sredina obsega)
DEFAULT_FIX = {
    "rooms":   2,
    "windows": 6,
    "doors":   9,
    "sockets": 11,
}

# ─── DER pomožne funkcije ────────────────────────────────────────────────────

def parse_der(data: bytes) -> dict:
    """Razčleni DER zaporedje in vrne slovar {ime_polja: vrednost}."""
    if len(data) < 2:
        raise ValueError("Podatki so prekratki za DER.")

    # SEQUENCE tag mora biti 0x30
    if data[0] != 0x30:
        raise ValueError(f"Pričakovan tag SEQUENCE (0x30), dobljen: 0x{data[0]:02x}")

    seq_len = data[1]
    payload = data[2:]

    if len(payload) != seq_len:
        raise ValueError(
            f"Dolžina SEQUENCE ({seq_len}) se ne ujema z dejansko dolžino ({len(payload)})."
        )

    result = {}
    offset = 0
    field_index = 0

    while offset < len(payload):
        if field_index >= len(FIELDS):
            raise ValueError("Preveč polj v zaporedju.")

        tag = payload[offset]
        if tag != 0x02:
            raise ValueError(
                f"Pričakovan tag INTEGER (0x02) pri odmiku {offset}, dobljen: 0x{tag:02x}"
            )

        length = payload[offset + 1]
        value_bytes = payload[offset + 2 : offset + 2 + length]

        if len(value_bytes) != length:
            raise ValueError("Nepopolni podatki za INTEGER.")

        value = int.from_bytes(value_bytes, byteorder="big", signed=True)
        field_name = FIELDS[field_index][0]
        result[field_name] = value

        offset += 2 + length
        field_index += 1

    if field_index != len(FIELDS):
        raise ValueError(f"Pričakoval {len(FIELDS)} polj, našel {field_index}.")

    return result


def encode_integer(value: int) -> bytes:
    """Zakodira celo število kot DER INTEGER TLV."""
    # Minimalno število bajtov za vrednost (signed)
    length = max(1, (value.bit_length() + 8) // 8)
    val_bytes = value.to_bytes(length, byteorder="big", signed=True)
    return bytes([0x02, len(val_bytes)]) + val_bytes


def encode_sequence(fields: dict) -> bytes:
    """Zakodira House kot DER SEQUENCE."""
    payload = b"".join(encode_integer(fields[name]) for name, _, _ in FIELDS)
    return bytes([0x30, len(payload)]) + payload


# ─── Validacija ──────────────────────────────────────────────────────────────

def validate(fields: dict) -> list[str]:
    """Preveri omejitve; vrne seznam napak (prazen = OK)."""
    errors = []
    for name, lo, hi in FIELDS:
        val = fields.get(name)
        if val is None:
            errors.append(f"  ✗ '{name}': manjka")
        elif not (lo <= val <= hi):
            errors.append(f"  ✗ '{name}' = {val}  (dovoljeno: {lo}..{hi})")
    return errors


def fix(fields: dict) -> dict:
    """Popravi vrednosti, ki so izven obsega, z vnaprej določenimi veljavnimi vrednostmi."""
    fixed = dict(fields)
    for name, lo, hi in FIELDS:
        val = fixed.get(name)
        if val is None or not (lo <= val <= hi):
            fixed[name] = DEFAULT_FIX[name]
    return fixed


# ─── Tiskanje ────────────────────────────────────────────────────────────────

def print_fields(fields: dict, label: str = ""):
    if label:
        print(f"  [{label}]")
    for name, lo, hi in FIELDS:
        val = fields.get(name, "?")
        ok = "✓" if isinstance(val, int) and lo <= val <= hi else "✗"
        print(f"    {ok} {name:8s} = {val}  (obseg: {lo}..{hi})")


def process_file(path: str):
    print(f"\n{'='*55}")
    print(f" Datoteka: {path}")
    print(f"{'='*55}")

    # Preberi hex vsebino
    with open(path, "r") as f:
        hex_str = f.read().strip()

    print(f"  HEX vhod : {hex_str}")
    data = bytes.fromhex(hex_str)
    print(f"  Bajti    : {' '.join(f'{b:02x}' for b in data)}")

    # Razčleni
    try:
        fields = parse_der(data)
    except ValueError as e:
        print(f"\n  [!] Napaka pri razčlenjevanju: {e}")
        return

    # Prikaži vrednosti
    print("\n  Dekodirane vrednosti:")
    print_fields(fields)

    # Validiraj
    errors = validate(fields)
    if not errors:
        print("\n  ✅ Vse vrednosti so veljavne. Ni potrebnih popravkov.")
        return

    print(f"\n  ❌ Najdene napake ({len(errors)}):")
    for err in errors:
        print(err)

    # Popravi
    fixed_fields = fix(fields)
    fixed_bytes = encode_sequence(fixed_fields)
    fixed_hex = fixed_bytes.hex()

    print("\n  Popravljene vrednosti:")
    print_fields(fixed_fields, "popravljeno")

    print(f"\n  HEX izhod: {fixed_hex}")
    print(f"  Bajti    : {' '.join(f'{b:02x}' for b in fixed_bytes)}")

    # Shrani popravljeno datoteko
    out_path = path.replace(".txt", "_fixed.txt")
    with open(out_path, "w") as f:
        f.write(fixed_hex)
    print(f"\n  💾 Shranjeno: {out_path}")


# ─── Glavna logika ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    files = sys.argv[1:] if len(sys.argv) > 1 else ["house1.txt", "house2.txt"]

    print("╔═══════════════════════════════════════════════════════╗")
    print("║      ASN.1 House DER Validator & Popravljalnik        ║")
    print("╚═══════════════════════════════════════════════════════╝")

    for path in files:
        try:
            process_file(path)
        except FileNotFoundError:
            print(f"\n  [!] Datoteka ne obstaja: {path}")
        except Exception as e:
            print(f"\n  [!] Neznana napaka: {e}")

    print(f"\n{'='*55}\n Končano.\n{'='*55}\n")