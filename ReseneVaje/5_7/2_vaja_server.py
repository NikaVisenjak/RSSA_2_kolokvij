import socket
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP, AES

server = socket.socket()
server.bind(("localhost", 9999))
server.listen(1)

conn, addr = server.accept()
print("Connected:", addr)

# RSA key pair
key = RSA.generate(2048)
private_key = key
public_key = key.publickey()

# send public key
conn.send(public_key.export_key())

# receive encrypted session key
enc_session_key = conn.recv(256)

rsa_cipher = PKCS1_OAEP.new(private_key)
session_key = rsa_cipher.decrypt(enc_session_key)

print("Session key received")

while True:
    data = conn.recv(4096)
    if not data:
        break

    nonce = data[:16]
    tag = data[16:32]
    ciphertext = data[32:]

    cipher = AES.new(session_key, AES.MODE_EAX, nonce=nonce)
    msg = cipher.decrypt_and_verify(ciphertext, tag)

    print("Client:", msg.decode())