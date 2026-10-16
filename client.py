import socket
import time

# tell client where server is
# tell client which computer has server
HOST = "127.0.0.1"

# TCP port where the original primary server accepts clients
PRIMARY_PORT = 5050

# TCP port where the backup accepts clients after promotion
BACKUP_PORT = 5052

# maximum number of attempts to connect to the backup
MAX_RETRIES = 5

# wait 2 seconds between failed backup connection attempts
RETRY_DELAY = 2

# maximum time to wait for a TCP socket operation
CONNECTION_TIMEOUT = 3


# this function sends a message and receives a response
# used for both the primary and backup server
def communicate_with_server(client_socket, server_name):

    # create the message that we want to send to the server
    message = f"Hello {server_name}!"

    # convert the string into bytes and send it through TCP
    client_socket.sendall(message.encode())

    # wait for the server to send a response
    response = client_socket.recv(1024)

    # convert received bytes back into a readable string
    print(f"{server_name} says: {response.decode()}")


# this function tries to connect to the primary server first
# if primary is unavailable, it tries the backup server
def start_client():

    # create me a network communication object -> using IPv4 -> using TCP
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # do not wait forever if the connection or communication stalls
    client_socket.settimeout(CONNECTION_TIMEOUT)

    try:
        # first, try connecting to the primary server on port 5050
        client_socket.connect((HOST, PRIMARY_PORT))

        print("Connected to PRIMARY server!")

        # send message and receive response from the primary
        communicate_with_server(client_socket, "PRIMARY")

        # primary communication succeeded, so no backup is needed
        return

    # this happens if the primary refuses the TCP connection
    except ConnectionRefusedError:
        print("Primary server unavailable!")

    # this happens if the primary connection or communication times out
    # or another socket-related error occurs
    except OSError as error:
        print(f"Primary connection error: {error}")

    # always close the primary socket before trying the backup
    finally:
        client_socket.close()

    # primary was unavailable, so try connecting to the backup
    for attempt in range(1, MAX_RETRIES + 1):

        # create a new TCP socket for every backup attempt
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # set a timeout so each attempt cannot wait forever
        client_socket.settimeout(CONNECTION_TIMEOUT)

        try:
            print(f"Trying BACKUP server. Attempt {attempt}/{MAX_RETRIES}")

            # attempt to connect to the backup on TCP port 5052
            client_socket.connect((HOST, BACKUP_PORT))

            print("Connected to BACKUP server!")

            # send message and receive response from the backup
            communicate_with_server(client_socket, "BACKUP")

            # connection and communication succeeded, stop this function
            return

        # handle a refused connection, timeout, or other socket error
        except OSError as error:
            print(f"Backup not ready: {error}")

            # only wait if we still have another attempt remaining
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)

        # close this attempt's socket whether it succeeded or failed
        finally:
            client_socket.close()

    # this runs only if all backup attempts failed
    print("ERROR: Both primary and backup servers are unavailable!")


# only start the client when client.py is run directly
if __name__ == "__main__":
    start_client()