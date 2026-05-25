import socket
import select
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP, AES

server = socket.socket()
server.bind(("localhost", 9999))
server.listen()

sockets = [server]
sessions = {}  # socket -> session_key
rsa_keys = {}   # socket -> private_key

print("Server running...")

while True:
    readable, _, _ = select.select(sockets, [], [])

    for s in readable:
        if s == server:
            conn, addr = server.accept()
            print("New client:", addr)

            key = RSA.generate(2048)
            rsa_keys[conn] = key

            conn.send(key.publickey().export_key())
            sockets.append(conn)

        else:
            data = s.recv(4096)
            if not data:
                sockets.remove(s)
                continue

            if s not in sessions:
                rsa_cipher = PKCS1_OAEP.new(rsa_keys[s])
                sessions[s] = rsa_cipher.decrypt(data)
                print("Session created")
                continue

            session_key = sessions[s]

            nonce = data[:16]
            tag = data[16:32]
            ciphertext = data[32:]

            cipher = AES.new(session_key, AES.MODE_EAX, nonce=nonce)
            msg = cipher.decrypt_and_verify(ciphertext, tag)

            print("Client says:", msg.decode())