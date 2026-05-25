import socket
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP, AES
from Crypto.Random import get_random_bytes

client = socket.socket()
client.connect(("localhost", 9999))

# receive server public key
pubkey = RSA.import_key(client.recv(2048))
rsa_cipher = PKCS1_OAEP.new(pubkey)

# generate session key
session_key = get_random_bytes(16)

# send encrypted session key
client.send(rsa_cipher.encrypt(session_key))

while True:
    msg = input("Message: ").encode()

    cipher = AES.new(session_key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(msg)

    client.send(cipher.nonce + tag + ciphertext)