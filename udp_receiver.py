import socket

# create UDP connection. DGRAM = datagram, individual message sent across network
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

HOST = "127.0.0.1"
PORT = 5051

udp_socket.bind((HOST, PORT))

print("UDP receiver is waiting...")


data, address = udp_socket.recvfrom(1024)

print(f"Received: {data.decode()}")
print(f"Sender address: {address}")

