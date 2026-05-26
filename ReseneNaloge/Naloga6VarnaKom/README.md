# Naloga 3 — gRPC mTLS (Mutual TLS) Varnostna Komunikacija

## Arhitektura rešitve

```
┌─────────────────────────────────────────────────────────────┐
│                    PKI INFRASTRUKTURA                        │
│  ┌─────────┐   podpiše   ┌──────────┐   podpiše             │
│  │   CA    │ ──────────> │ server   │                        │
│  │(ca.crt) │             │ .crt/.key│                        │
│  │         │ ──────────> │ client   │                        │
│  └─────────┘             │ .crt/.key│                        │
└─────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                    mTLS ROKOVANJE (HANDSHAKE)                 │
│                                                               │
│  KLIENT                              STREŽNIK                 │
│    │                                    │                     │
│    │──── TCP vzpostavitev ──────────────►│                    │
│    │                                    │                     │
│    │──── ClientHello ──────────────────►│  (TLS handshake)   │
│    │◄─── ServerHello + server.crt ──────│                     │
│    │     Klient preveri server.crt!     │                     │
│    │                                    │                     │
│    │════ TLS TUNEL VZPOSTAVLJEN ════════│ (šifriranje aktivno)│
│    │                                    │                     │
│    │──── client.crt (ZNOTRAJ TUNELA) ──►│ ← KLJUČNO!        │
│    │     Strežnik preveri client.crt!   │                     │
│    │                                    │                     │
│    │════ VARNA DVOSMERNA SEJA ══════════│                     │
└──────────────────────────────────────────────────────────────┘
```

## Zakaj je identiteta klienta zaščitena?

**Ključno varnostno jamstvo:** Klientov certifikat (`client.crt`) se pošlje
strežniku **ZNOTRAJ šifriranega TLS tunela**, ki je vzpostavljen PREDEN
se certifikat prenese.

To pomeni:
- ❌ Tretje osebe vidijo samo šifrirane TCP pakete
- ❌ Tretje osebe ne morejo dešifrirati vsebine (nimajo zasebnega ključa)
- ✅ Samo strežnik (z `server.key`) lahko odpre tunel in vidi klientov certifikat
- ✅ Identiteta klienta (`naloga3-client-secret`) je vidna **samo strežniku**

## Struktura projekta

```
grpc_mtls/
├── proto/
│   └── secure_service.proto      ← Definicija gRPC storitve
├── certs/
│   ├── ca.crt / ca.key           ← Korenski CA (Certificate Authority)
│   ├── server.crt / server.key   ← Strežniški certifikat
│   └── client.crt / client.key   ← Klientov certifikat (identiteta)
├── server/
│   └── server.py                 ← gRPC strežnik z mTLS
├── client/
│   └── client.py                 ← gRPC klient z mTLS
├── generate_certs.py             ← Generiranje PKI infrastrukture
├── secure_service_pb2.py         ← Generirano iz proto (sporočila)
└── secure_service_pb2_grpc.py    ← Generirano iz proto (storitve)
```

## Namestitev

```bash
pip install grpcio grpcio-tools cryptography
```

## Zagon

### 1. Generiranje certifikatov (enkrat)
```bash
python generate_certs.py
```

### 2. Zagon strežnika
```bash
python server/server.py
```

### 3. Zagon klienta (v ločenem terminalu)
```bash
python client/client.py
```

## Varnostne lastnosti

| Lastnost | Implementacija |
|---|---|
| Identifikacija strežnika | `server.crt` podpisan s CA |
| Identifikacija klienta | `client.crt` podpisan s CA |
| Šifriranje prenosa | TLS (AES-256-GCM / ChaCha20) |
| Zaščita identitete klienta | Certifikat prenesen ZNOTRAJ TLS tunela |
| Zaščita pred MitM | Verifikacija server.crt + certificate pinning |
| Zaščita pred replay napadi | UUID nonce pri Ping klic |
| Brez insecure porta | Samo `add_secure_port()` |

## gRPC storitve (proto)

```protobuf
service SecureService {
  rpc SendMessage   (MessageRequest)    returns (MessageResponse);
  rpc GetServerInfo (ServerInfoRequest) returns (ServerInfoResponse);
  rpc Ping          (PingRequest)       returns (PingResponse);
}
```

## Generiranje proto kode

```bash
python -m grpc_tools.protoc \
  -I./proto \
  --python_out=. \
  --grpc_python_out=. \
  ./proto/secure_service.proto
```
