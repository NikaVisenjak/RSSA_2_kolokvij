import grpc
from concurrent import futures
import time
import threading

import chat_pb2
import chat_pb2_grpc


class ChatServer(chat_pb2_grpc.ChatServerServicer):

    def __init__(self):
        # seznam vseh sporočil
        self.messages = []
        self.condition = threading.Condition()

    # client pošlje sporočilo
    def SendNote(self, request, context):
        print(f"[SERVER] {request.name}: {request.message}")

        with self.condition:
            self.messages.append(request)
            self.condition.notify_all()

        return chat_pb2.Empty()

    # streaming vsem clientom
    def ChatStream(self, request, context):
        last_index = 0

        while True:
            with self.condition:
                while len(self.messages) == last_index:
                    self.condition.wait()

                # pošlji nova sporočila
                while last_index < len(self.messages):
                    note = self.messages[last_index]
                    last_index += 1
                    yield note


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chat_pb2_grpc.add_ChatServerServicer_to_server(ChatServer(), server)

    server.add_insecure_port("[::]:50051")
    server.start()

    print("[SERVER] Chat server running...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[SERVER] Stopping...")
        server.stop(0)


if __name__ == "__main__":
    serve()