import socket

# create UDP connection. DGRAM = datagram, individual message sent across network
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

HOST = "127.0.0.1"
PORT = 5051

udp_socket.bind((HOST, PORT))

udp_socket.settimeout(2)

print("UDP receiver is waiting...")

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
            break

