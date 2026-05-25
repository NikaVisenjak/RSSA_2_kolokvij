"""
Vaja 4: Chatroom Server z enkriptiranimi sporočili
- Vsak klient dobi lasten AES session key (hibridna enkripcija)
- Server prejema sporočila z select() in jih posreduje vsem ostalim klientom
- Vsako sporočilo se re-enkriptira za vsakega prejemnika posebej
"""

import socket
import select
import threading
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Random import get_random_bytes
import struct
import json


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


def encrypt_for_client(message: str, session_key: bytes) -> bytes:
    """
    AES-EAX enkriptira sporočilo z danim session ključem.
    Vrne: nonce (16B) + tag (16B) + ciphertext
    """
    cipher = AES.new(session_key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(message.encode())
    return cipher.nonce + tag + ciphertext


class ChatServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        # socket -> {'session_key': bytes, 'username': str}
        self.clients = {}
        self.lock = threading.Lock()

    def generate_session_key(self) -> bytes:
        return get_random_bytes(16)  # 128-bit AES ključ

    def handshake(self, conn, addr) -> tuple[str, bytes]:
        """
        Hibridni handshake:
        1. Klient pošlje RSA javni ključ
        2. Server generira AES session key
        3. Server enkriptira session key z RSA javnim ključem
        4. Server pošlje enkriptirani session key
        5. Klient pošlje uporabniško ime (enkriptirano z AES)
        """
        print(f"[HANDSHAKE] Začetek z {addr}")

        # 1. Prejmi RSA javni ključ od klienta
        pub_key_data = recv_framed(conn)
        rsa_pub_key = RSA.import_key(pub_key_data)
        print(f"[HANDSHAKE] Prejet RSA javni ključ od {addr}")

        # 2. Generiraj AES session key
        session_key = self.generate_session_key()

        # 3. Enkriptiraj session key z RSA javnim ključem
        cipher_rsa = PKCS1_OAEP.new(rsa_pub_key)
        encrypted_session_key = cipher_rsa.encrypt(session_key)

        # 4. Pošlji enkriptirani session key
        send_framed(conn, encrypted_session_key)
        print(f"[HANDSHAKE] Poslan enkriptirani session key na {addr}")

        # 5. Prejmi enkriptirano uporabniško ime
        enc_username = recv_framed(conn)
        nonce = enc_username[:16]
        tag = enc_username[16:32]
        ciphertext = enc_username[32:]
        cipher_aes = AES.new(session_key, AES.MODE_EAX, nonce=nonce)
        username = cipher_aes.decrypt_and_verify(ciphertext, tag).decode()
        print(f"[HANDSHAKE] Klient {addr} je: {username}")

        return username, session_key

    def broadcast(self, message: str, sender_conn):
        """Pošlje sporočilo vsem klientom razen pošiljatelju."""
        with self.lock:
            recipients = {
                conn: info
                for conn, info in self.clients.items()
                if conn != sender_conn
            }

        for conn, info in recipients.items():
            try:
                encrypted = encrypt_for_client(message, info["session_key"])
                send_framed(conn, encrypted)
            except Exception as e:
                print(f"[BROADCAST] Napaka pri pošiljanju: {e}")

    def handle_client(self, conn, addr):
        """Obravnava posameznega klienta v ločeni niti."""
        try:
            username, session_key = self.handshake(conn, addr)
            with self.lock:
                self.clients[conn] = {
                    "session_key": session_key,
                    "username": username,
                    "addr": addr,
                }
            print(f"[SERVER] {username} se je pridružil. Skupaj klientov: {len(self.clients)}")
            join_msg = f"*** {username} se je pridružil chatroomu ***"
            self.broadcast(join_msg, conn)

            # Sprejemaj sporočila od tega klienta
            while True:
                try:
                    enc_data = recv_framed(conn)
                except ConnectionError:
                    break

                # Dekriptiraj sporočilo
                nonce = enc_data[:16]
                tag = enc_data[16:32]
                ciphertext = enc_data[32:]
                cipher_aes = AES.new(session_key, AES.MODE_EAX, nonce=nonce)
                try:
                    message = cipher_aes.decrypt_and_verify(ciphertext, tag).decode()
                except Exception as e:
                    print(f"[SERVER] Napaka pri dekriptiranju od {username}: {e}")
                    break

                print(f"[{username}] {message}")
                full_msg = f"[{username}] {message}"
                self.broadcast(full_msg, conn)

        except Exception as e:
            print(f"[SERVER] Napaka s klientom {addr}: {e}")
        finally:
            with self.lock:
                info = self.clients.pop(conn, None)
            if info:
                leave_msg = f"*** {info['username']} je zapustil chatroom ***"
                print(f"[SERVER] {info['username']} se je odjavil.")
                self.broadcast(leave_msg, conn)
            conn.close()

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
            server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_sock.bind((self.host, self.port))
            server_sock.listen(10)
            print(f"[SERVER] Chatroom strežnik teče na {self.host}:{self.port}")
            print("[SERVER] Čakam na povezave...")

            while True:
                conn, addr = server_sock.accept()
                print(f"[SERVER] Nova povezava od {addr}")
                thread = threading.Thread(
                    target=self.handle_client, args=(conn, addr), daemon=True
                )
                thread.start()


if __name__ == "__main__":
    server = ChatServer(HOST, PORT)
    server.run()