import grpc
import threading

import chat_pb2
import chat_pb2_grpc

PORT = 50051


def listen(stub):
    """Posluša stream iz serverja"""
    for note in stub.ChatStream(chat_pb2.Empty()):
        print(f"\n[{note.name}] {note.message}")


def run():
    name = input("Username: ")

    with grpc.insecure_channel(f"localhost:{PORT}") as channel:
        stub = chat_pb2_grpc.ChatServerStub(channel)

        # thread za poslušanje
        t = threading.Thread(target=listen, args=(stub,), daemon=True)
        t.start()

        print("Vpiši sporočila (quit za izhod):")

        while True:
            msg = input("> ").strip()

            if msg.lower() in ("quit", "exit", "izhod"):
                break

            stub.SendNote(chat_pb2.Note(name=name, message=msg))


if __name__ == "__main__":
    run()