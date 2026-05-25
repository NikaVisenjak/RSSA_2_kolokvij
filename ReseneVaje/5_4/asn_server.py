import socket
from pyasn1.codec.der.decoder import decode
from asn1_model import TimeSeries

HOST = "0.0.0.0"
PORT = 22222

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(1)

    print(f"Server listening on {PORT}...")

    conn, addr = server.accept()
    print("Client connected:", addr)

    data = conn.recv(65536)

    try:
        obj, _ = decode(data, asn1Spec=TimeSeries())

        print("\n✔ DECODE SUCCESS")
        print(obj.prettyPrint())

        conn.sendall(b"ASN.1 OK")

    except Exception as e:
        msg = f"ASN.1 ERROR: {e}"
        print("\n✖", msg)
        conn.sendall(msg.encode())

    conn.close()
    server.close()

if __name__ == "__main__":
    start_server()