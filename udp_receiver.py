import socket
import threading
import logging

# BACKUP SERVER

# which computer/network interface should backup server live on
# lives on this computer/my laptop
HOST = "127.0.0.1"

# UDP port where the backup server receives heartbeats
HEARTBEAT_PORT = 5051

# TCP port where the backup will accept clients after promotion
BACKUP_TCP_PORT = 5052

# wait up to 2 seconds for each heartbeat before counting a miss
HEARTBEAT_TIMEOUT = 2

# number of missed heartbeat timeouts allowed before promotion
MAX_MISSED = 3


# set up logging to show the time and type of every message
# INFO = normal activity, WARNING = unexpected activity, ERROR = failure
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# this function handles communication with one TCP client
# every connected client will have its own thread running this function
def handle_client(connection, address):

    try:
        logging.info(f"Client connected: {address}")

        # wait till client sends some data
        data = connection.recv(1024)

        # if client disconnects without sending data, stop this function
        if not data:
            logging.info("Client disconnected without sending data")
            return

        # convert the received bytes into a readable string
        message = data.decode()

        logging.info(f"Client says: {message}")

        # send a response back to the connected client
        response = "Hello from NEW PRIMARY!"
        connection.sendall(response.encode())

    # if something goes wrong during communication, log the error
    except OSError as error:
        logging.error(f"Client communication error: {error}")

    # always close the client connection when finished
    finally:
        connection.close()

        logging.info(f"Client disconnected: {address}")


# this function starts the backup TCP server after promotion
def start_tcp_server():

    # create me a network communication object -> using IPv4 -> using TCP
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # allow the TCP address to be reused after certain restarts
    tcp_socket.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1
    )

    try:
        # attach this TCP socket to 127.0.0.1, port 5052
        tcp_socket.bind((HOST, BACKUP_TCP_PORT))

        # socket now ready to receive incoming TCP connection requests
        tcp_socket.listen()

        logging.info(
            f"NEW PRIMARY listening on {HOST}:{BACKUP_TCP_PORT}"
        )

        # keep accepting TCP clients while the new primary is running
        while True:

            # tell Python to wait until someone connects
            connection, address = tcp_socket.accept()

            # create a separate thread for each connected client
            # this allows multiple clients to communicate independently
            client_thread = threading.Thread(
                target=handle_client,
                args=(connection, address),
                daemon=True
            )

            # start the thread to handle this client's communication
            client_thread.start()

    # if something goes wrong with the TCP socket, log the error
    except OSError as error:
        logging.error(f"Backup TCP server error: {error}")

    # always close the TCP socket when the server stops
    finally:
        tcp_socket.close()


# this function monitors heartbeat messages from the primary server
def monitor_heartbeats():

    # create a UDP socket -> using IPv4 -> using UDP
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # attach this socket to the UDP heartbeat port
    udp_socket.bind((HOST, HEARTBEAT_PORT))

    # do not wait forever for a heartbeat
    # raise socket.timeout if no message arrives within 2 seconds
    udp_socket.settimeout(HEARTBEAT_TIMEOUT)

    # start with zero missed heartbeats
    missed_heartbeats = 0

    # backup begins in BACKUP state
    server_state = "BACKUP"

    logging.info("Backup server started")
    logging.info("Waiting for primary heartbeats...")

    try:
        # keep monitoring while this server is still the backup
        while server_state == "BACKUP":

            try:
                # wait for a UDP message from the primary
                data, address = udp_socket.recvfrom(1024)

                # check if the received message is a valid heartbeat
                if data == b"ALIVE":

                    # reset counter because primary is still sending heartbeats
                    missed_heartbeats = 0

                    logging.info("Heartbeat received. Counter reset.")

            # this happens when no UDP message arrives within 2 seconds
            except socket.timeout:

                # increase the missed heartbeat counter by one
                missed_heartbeats += 1

                logging.warning(
                    f"Missed heartbeat: "
                    f"{missed_heartbeats}/{MAX_MISSED}"
                )

                # check if the primary has missed too many heartbeats
                if missed_heartbeats >= MAX_MISSED:

                    logging.error("PRIMARY FAILURE DETECTED")

                    # change this server's role from BACKUP to PRIMARY
                    server_state = "PRIMARY"

                    logging.info("Backup promoted to NEW PRIMARY")

    # close the UDP socket when monitoring finishes
    finally:
        udp_socket.close()

    # if the backup was promoted, start accepting TCP clients
    if server_state == "PRIMARY":
        start_tcp_server()


# only start monitoring when udp_receiver.py is run directly
# importing this file for testing will not automatically start the backup
if __name__ == "__main__":
    monitor_heartbeats()