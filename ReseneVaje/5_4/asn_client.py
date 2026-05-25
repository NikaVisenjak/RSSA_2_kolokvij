import socket
from pyasn1.codec.der.encoder import encode
from asn1_model import TimeSeries

SERVER_IP = "127.0.0.1"   # če testiraš lokalno daj "127.0.0.1"
PORT = 22222

def build_sample():
    ts = TimeSeries()

    ts["SensorID"] = 1
    ts["Type"] = "Temperature"

    values = ts["Values"]
    values.extend([1.1, 2.2, 3.3, 4.4, 5.5,
                   6.6, 7.7, 8.8, 9.9, 10.0])

    return ts

def send():
    ts = build_sample()
    data = encode(ts)

    print("Sending DER:", data.hex())

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((SERVER_IP, PORT))

    s.sendall(data)

    response = s.recv(4096)
    print("Server response:", response.decode())

    s.close()

if __name__ == "__main__":
    send()