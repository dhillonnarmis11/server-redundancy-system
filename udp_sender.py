import socket
import time

udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

HOST = "127.0.0.1"
PORT = 5051

while True:
    message = "ALIVE"

    udp_socket.sendto(message.encode(), (HOST, PORT))

    print("Heartbeat sent!")

    time.sleep(1)

