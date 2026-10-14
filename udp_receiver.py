import socket

def start_tcp_server():

    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    tcp_socket.bind(("127.0.0.1", 5052))

    tcp_socket.listen()

    print("BACKUP TCP SERVER IS NOW ACTIVE ON PORT 5052")

    connection, address = tcp_socket.accept()

    print(f"Client connected to new primary: {address}")

    data = connection.recv(1024)

    print(f"Client says: {data.decode()}")

    connection.sendall("Hello from NEW PRIMARY!".encode())

    connection.close()
    tcp_socket.close()




# create UDP connection. DGRAM = datagram, individual message sent across network
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

HOST = "127.0.0.1"
PORT = 5051

udp_socket.bind((HOST, PORT))

udp_socket.settimeout(2)

print("UDP receiver is waiting...")

server_state = "BACKUP"

print(f"Current server state: {server_state}")

missed_heartbeats = 0
MAX_MISSED = 3

while True:
    try:
        data, address = udp_socket.recvfrom(1024)

        message = data.decode()

        if message == "ALIVE":
            missed_heartbeats = 0
            print(f"Heartbeat received. Counter reset.")

    except socket.timeout:
        missed_heartbeats += 1

        print(f"Missed heartbeat: {missed_heartbeats}/{MAX_MISSED}")

        if missed_heartbeats >= MAX_MISSED:
            print("ALERT: PRIMARY SERVER FAILURE DETECTED!")

            server_state = "PRIMARY"

            print(f"New server state: {server_state}")

            break

if server_state == "PRIMARY":
    start_tcp_server()

