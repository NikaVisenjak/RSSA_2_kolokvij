# RSSA 2. Kolokvij - Rešitve z razlagami

## Pregled nalog

---

## NALOGA 1: Flask Login (varnostna ranljivost)

**Ranljivost:** Timing attack pri primerjavi gesel z `==`

**Rešitev:**
```bash
cd naloga1_flask
pip install flask
python app.py
# Obišči http://localhost:5000/login
```

**Ključni koncepti:**
- `hmac.compare_digest()` = constant-time primerjava (prepreči timing attack)
- Gesla hranimo kot SHA-256 **hash**, ne plaintext
- `hashlib.sha256("geslo".encode()).hexdigest()` = hash gesla

---

## NALOGA 2: ASN.1 (EVL Inc.)

**Zakaj ASN.1?** Omejena internetna zveza (Antarktika) + fax (Japonska)  
**Zakaj ENUMERATED in ne INTEGER?** Prihranimo bajte - prenaša se samo indeks (0/1/2)

```bash
cd naloga2_asn1
pip install pyasn1
python evl_order.py
```

**DER format bajt po bajt:**
```
0x30 0x0A        -- SEQUENCE, dolžina 10
0x0A 0x01 0x01   -- ENUMERATED rockets = indeks 1 (4001)
0x0A 0x01 0x00   -- ENUMERATED bombs = indeks 0 (1019)
0x0A 0x01 0x01   -- ENUMERATED chocolates = indeks 1 (1499)
0x01 0x01 0xFF   -- BOOLEAN TRUE (akcija takoj)
```

---

## NALOGA 3: ASN.1 DER preverjanje

**House objekt:**
| Polje   | Tag  | Obseg |
|---------|------|-------|
| rooms   | 0x02 | 1..4  |
| windows | 0x02 | 5..8  |
| doors   | 0x02 | 7..11 |
| sockets | 0x02 | 9..13 |

**DER struktura:**
```
0x30 [len]           -- SEQUENCE
0x02 0x01 [rooms]    -- INTEGER
0x02 0x01 [windows]  -- INTEGER
0x02 0x01 [doors]    -- INTEGER
0x02 0x01 [sockets]  -- INTEGER
```

```bash
cd naloga3_asn1_der
pip install pyasn1
python check_house.py
```

---

## NALOGA 4: gRPC igra ugibanja

**Koraki za zagon:**
```bash
cd naloga4_grpc
pip install grpcio grpcio-tools

# Generiraj Python kodo iz .proto
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. guessing_game.proto

# Terminal 1: server
python server.py

# Terminal 2: client
python client.py
```

**gRPC pojmi:**
- `stub` = client-side proxy (kličemo kot lokalno funkcijo, gre čez mrežo)
- `ServicerClass` = server-side implementacija
- `insecure_channel` = brez TLS (samo za razvoj!)

---

## NALOGA 5: gRPC Bayes igra

**Strategija:** Iterativna bisekcija - vsako ugibanje razpolovi preostali prostor  
**Kompleksnost:** O(log n) poskusov glede na velikost prostora

```bash
cd naloga5_grpc_bayes
pip install grpcio grpcio-tools

python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. bayes_game.proto

# Terminal 1:
python server.py

# Terminal 2:
python client.py
```

**Primer bisekcije:**
```
Prostor: x=[0,1000], y=[0,1000]
Ugibam (500, 500) -> SEVERO-VZHOD
Prostor: x=[500,1000], y=[500,1000]
Ugibam (750, 750) -> JUG
Prostor: x=[500,1000], y=[500,750]
... (logaritmično konvergira)
```

---

## NALOGA 6: gRPC mTLS

**mTLS = mutual TLS** - oba (client IN server) se identificirata z certifikatom

```bash
cd naloga6_grpc_secure
pip install grpcio grpcio-tools

# 1. Generiraj certifikate
# Windows (PowerShell):
powershell -ExecutionPolicy Bypass -File generate_certs.ps1
# Linux/macOS/Git Bash:
bash generate_certs.sh

# 2. Generiraj gRPC kodo
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. secure_service.proto

# 3. Terminal 1:
python server.py

# 4. Terminal 2:
python client.py
```

**Zakaj je identiteta skrita?**
- TLS najprej vzpostavi šifriran tunel
- Šele ZNOTRAJ tega tunela se izmenjata certifikata
- Pasivni opazovalec vidi samo šifrirane bajte!

**Razlika navaden TLS vs mTLS:**
```
Navaden TLS:  Server -> Client: "Jaz sem strežnik X" (certifikat)
mTLS:         Server -> Client: "Jaz sem strežnik X" (certifikat)
              Server -> Client: "Pokaži mi TVOJ certifikat!"
              Client -> Server: "Jaz sem klient Y" (certifikat, ŠIFRIRAN!)
```

---

## Povzetek ključnih pojmov

| Pojem | Razlaga |
|-------|---------|
| DER | Binary encoding za ASN.1 - deterministično, kompaktno |
| ENUMERATED | ASN.1 tip - shranjuje indeks ne vrednost (prihrani bajte) |
| Timing attack | Napad ki meri čas odgovora za ugotavljanje tajnih podatkov |
| hmac.compare_digest | Constant-time primerjava - prepreči timing attack |
| gRPC stub | Client-side proxy objekt za klicanje RPC metod |
| mTLS | Obojestransko TLS - oba imata certifikat |
| CSR | Certificate Signing Request - zahteva za podpis certifikata |
| CA | Certificate Authority - zaupanja vredna podpisnica certifikatov |
