import socket
import threading
import time
import logging


# which computer/network interface should server live on
# lives on this computer/my laptop
HOST = "127.0.0.1"    # localhost/loopback address

# program that recieves requests on the local network
PORT = 5050

# this is the UDP port where the backup server is waiting for heartbeats
HEARTBEAT_PORT = 5051


# set up logging so we can see the time and type of every message
# INFO = normal activity, WARNING = something unexpected, ERROR = something failed
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# first, define the heartbeat function
def send_heartbeats():

    # create a UDP socket -> using IPv4 -> using UDP
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        while True:

            # send ALIVE message to the backup server on UDP port 5051
            udp_socket.sendto(b"ALIVE", (HOST, HEARTBEAT_PORT))

            logging.info("Primary: Heartbeat sent")

            # wait 1 second before sending the next heartbeat
            time.sleep(1)

    # if something goes wrong while sending heartbeats, log the error
    except OSError as error:
        logging.error(f"Heartbeat error: {error}")

    # always close the UDP socket when this function finishes
    finally:
        udp_socket.close()


# this function handles communication with one connected TCP client
# every client will have its own thread running this function
def handle_client(connection, address):

    try:
        logging.info("A client connected!")
        logging.info(f"Client address: {address}")

        # wait till client sends some data
        data = connection.recv(1024)    # receive up to 1024 bytes of data in the call

        # if client disconnects without sending anything, stop this function
        if not data:
            return

        message = data.decode()
        logging.info(f"Client says: {message}")

        # send client response back
        response = "Hello from PRIMARY!"
        connection.sendall(response.encode())

    # if something goes wrong during client communication, log the error
    except OSError as error:
        logging.error(f"Client communication error: {error}")

    # close this client's connection even if an error happens
    finally:
        connection.close()

        logging.info("Client disconnected.")


# this function starts the primary TCP server
def start_server():

    # create me a network communciation object -> using IPv4 -> using TCP
    # created TCP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # allow the server to reuse its address when restarting
    # helps avoid certain address already in use errors after restarting
    server_socket.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1
    )

    try:
        # attach this socket to 127.0.0.1, port 5050
        server_socket.bind((HOST, PORT))

        logging.info(f"Server bound to {HOST}:{PORT}")

        # socket now allowed to recieve incoming TCP connection requests/now ready for incoming TCP connections
        server_socket.listen()

        logging.info(f"Primary TCP Server is listening on {HOST}:{PORT}")

        # second, create and start the heartbeat thread
        heartbeat_thread = threading.Thread(
            target=send_heartbeats,
            daemon=True
        )

        heartbeat_thread.start()

        # keep the primary server running and accepting clients
        while True:

            # tell python to wait until someone connects
            connection, address = server_socket.accept()

            # create a separate thread for this client
            # this allows multiple clients to communicate without waiting for each other
            client_thread = threading.Thread(
                target=handle_client,
                args=(connection, address),
                daemon=True
            )

            # start running the handle_client function in the new thread
            client_thread.start()

    # if the TCP server has a socket error, log it instead of showing a traceback
    except OSError as error:
        logging.error(f"Server error: {error}")

    # always close the main TCP socket when the server stops
    finally:
        server_socket.close()


# only start the server when we run server.py directly
# if another Python file imports server.py, the server will not automatically start
if __name__ == "__main__":
    start_server()

    