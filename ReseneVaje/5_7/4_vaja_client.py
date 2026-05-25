"""
Vaja 4: Chatroom Klient z enkriptiranimi sporočili
- Generira RSA par ključev in pošlje javni ključ strežniku
- Prejme enkriptirani AES session key od strežnika
- V ločeni niti sprejema enkriptirana sporočila od strežnika
- V glavni niti pošilja enkriptirana sporočila strežniku
"""

import socket
import threading
import sys
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Random import get_random_bytes
import struct


HOST = "127.0.0.1"
PORT = 65432


def recv_exact(sock, n):
    """Prejme natanko n bajtov."""
    data = b""
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            raise ConnectionError("Povezava prekinjena.")
        data += chunk
    return data


def send_framed(sock, data: bytes):
    """Pošlje podatke z 4-bajtno dolžino na začetku."""
    sock.sendall(struct.pack(">I", len(data)) + data)


def recv_framed(sock) -> bytes:
    """Prejme okvirjeno sporočilo (4-bajtna dolžina + podatki)."""
    raw_len = recv_exact(sock, 4)
    length = struct.unpack(">I", raw_len)[0]
    return recv_exact(sock, length)


def encrypt_message(message: str, session_key: bytes) -> bytes:
    """
    AES-EAX enkriptira sporočilo.
    Vrne: nonce (16B) + tag (16B) + ciphertext
    """
    cipher = AES.new(session_key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(message.encode())
    return cipher.nonce + tag + ciphertext


def decrypt_message(data: bytes, session_key: bytes) -> str:
    """
    AES-EAX dekriptira sporočilo.
    Pričakuje: nonce (16B) + tag (16B) + ciphertext
    """
    nonce = data[:16]
    tag = data[16:32]
    ciphertext = data[32:]
    cipher = AES.new(session_key, AES.MODE_EAX, nonce=nonce)
    return cipher.decrypt_and_verify(ciphertext, tag).decode()


def receive_messages(sock, session_key, stop_event):
    """
    Nit, ki neprestano sprejema in dekriptira sporočila od strežnika.
    """
    while not stop_event.is_set():
        try:
            enc_data = recv_framed(sock)
            message = decrypt_message(enc_data, session_key)
            # Izpiši sporočilo čisto (brez prekinitve vnosa)
            print(f"\r{message}\n> ", end="", flush=True)
        except ConnectionError:
            if not stop_event.is_set():
                print("\n[KLIENT] Povezava s strežnikom prekinjena.")
            stop_event.set()
            break
        except Exception as e:
            if not stop_event.is_set():
                print(f"\n[KLIENT] Napaka pri sprejemanju: {e}")
            stop_event.set()
            break


def handshake(sock, username: str) -> bytes:
    """
    Hibridni handshake s strežnikom:
    1. Generiraj RSA par ključev (2048-bit)
    2. Pošlji RSA javni ključ strežniku
    3. Prejmi enkriptirani AES session key
    4. Dekriptiraj session key z RSA zasebnim ključem
    5. Pošlji enkriptirano uporabniško ime
    """
    print("[KLIENT] Generiram RSA ključe (2048-bit)...")
    rsa_key = RSA.generate(2048)
    rsa_pub_key = rsa_key.publickey()

    # 2. Pošlji RSA javni ključ
    pub_key_data = rsa_pub_key.export_key()
    send_framed(sock, pub_key_data)
    print("[KLIENT] RSA javni ključ poslan strežniku.")

    # 3. Prejmi enkriptirani session key
    encrypted_session_key = recv_framed(sock)

    # 4. Dekriptiraj session key
    cipher_rsa = PKCS1_OAEP.new(rsa_key)
    session_key = cipher_rsa.decrypt(encrypted_session_key)
    print(f"[KLIENT] Session key prejet in dekriptiran: {session_key.hex()}")

    # 5. Pošlji enkriptirano uporabniško ime
    enc_username = encrypt_message(username, session_key)
    send_framed(sock, enc_username)
    print(f"[KLIENT] Prijavljen kot: {username}")

    return session_key


def main():
    if len(sys.argv) < 2:
        username = input("Vpiši svoje ime: ").strip()
    else:
        username = sys.argv[1]

    if not username:
        print("Ime ne sme biti prazno!")
        sys.exit(1)

    print(f"[KLIENT] Povezujem se na {HOST}:{PORT}...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((HOST, PORT))
    except ConnectionRefusedError:
        print(f"[KLIENT] Ne morem se povezati na {HOST}:{PORT}. Ali strežnik teče?")
        sys.exit(1)

    try:
        # Hibridni handshake
        session_key = handshake(sock, username)
        print("[KLIENT] Uspešno povezan! Piši sporočila (za izhod: 'quit'):\n")

        # Zaženi nit za sprejemanje sporočil
        stop_event = threading.Event()
        recv_thread = threading.Thread(
            target=receive_messages,
            args=(sock, session_key, stop_event),
            daemon=True,
        )
        recv_thread.start()

        # Glavna zanka za pošiljanje sporočil
        while not stop_event.is_set():
            try:
                print("> ", end="", flush=True)
                message = input()
                if message.lower() in ("quit", "exit", "izhod"):
                    print("[KLIENT] Zapuščam chatroom...")
                    stop_event.set()
                    break
                if not message.strip():
                    continue
                # Enkriptiraj in pošlji sporočilo
                enc_msg = encrypt_message(message, session_key)
                send_framed(sock, enc_msg)
            except (KeyboardInterrupt, EOFError):
                print("\n[KLIENT] Izhod...")
                stop_event.set()
                break

    finally:
        sock.close()
        print("[KLIENT] Povezava zaprta.")


if __name__ == "__main__":
    main()