import socket
import threading
import time

# first, define the heartbeat function
def send_heartbeats():
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    while True:
        udp_socket.sendto(b"ALIVE", ("127.0.0.1", 5051))

        print("Primary: Heartbeat sent")

        time.sleep(1)

# second, create and start the heartbeat thread
heartbeat_thread = threading.Thread(
    target=send_heartbeats,
    daemon=True
)

heartbeat_thread.start()


# create me a network communciation object -> using IPv4 -> using TCP
# created TCP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


# which computer/network interface should server live on
# lives on this computer/my laptop
HOST = "127.0.0.1"    # localhost/loopback address

# program that recieves requests on the local network
PORT = 5050

# attach this socket to 127.0.0.1, port 5050
server_socket.bind((HOST, PORT))

print(f"Server bound to {HOST}:{PORT}")

# socket now allowed to recieve incoming TCP connection requests/now ready for incoming TCP connections
server_socket.listen()

print(f"Primary TCP Server is listening on {HOST}:{PORT}")

while True:

    # tell python to wait until someone connects
    connection, address = server_socket.accept()

    print("A client connected!")
    print(f"Client address: {address}")


    # wait till client sends some data
    data = connection.recv(1024)    # receive up to 1024 bytes of data in the call
    message = data.decode()
    print(f"Client says: {message}")


    # send client response back
    response = "Hello Client!"
    connection.sendall(response.encode())

    connection.close()

    print("Client disconnected.")




