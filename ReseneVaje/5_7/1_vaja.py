from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP, AES
from Crypto.Random import get_random_bytes

# ---------------- RSA ----------------
key = RSA.generate(2048)
private_key = key
public_key = key.publickey()

rsa_cipher = PKCS1_OAEP.new(public_key)

session_key = get_random_bytes(16)  # AES key

encrypted_session_key = rsa_cipher.encrypt(session_key)

# decrypt session key
rsa_dec = PKCS1_OAEP.new(private_key)
decrypted_session_key = rsa_dec.decrypt(encrypted_session_key)

print("Session key OK:", session_key == decrypted_session_key)

# ---------------- AES ----------------
data = b"Hello world secret message"

cipher = AES.new(session_key, AES.MODE_EAX)
ciphertext, tag = cipher.encrypt_and_digest(data)

decipher = AES.new(decrypted_session_key, AES.MODE_EAX, nonce=cipher.nonce)
plaintext = decipher.decrypt_and_verify(ciphertext, tag)

print("AES OK:", plaintext)