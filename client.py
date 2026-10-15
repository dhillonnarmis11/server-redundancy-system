import socket
import time

# tell client where server is
# tell client which computer has server
HOST = "127.0.0.1"
# which program/service on that computer
PRIMARY_PORT = 5050
BACKUP_PORT = 5052

# FIRST, attempt to connect to the PRIMARY
# create a socket that uses IPv4 + TCP
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


# connect client to server
# attempt to connect to primary server
try:
    client_socket.connect((HOST, PRIMARY_PORT))
    print("Connected to primary server!")

# handle a refused connection
except ConnectionRefusedError:
    print("Primary server is unavailable!")

    # close the failed primary socket 
    client_socket.close()

    # try connecting to backup server
    for attempt in range(1, 6):
    # attempt to connect to the BACKUP server
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            client_socket.connect((HOST, BACKUP_PORT))
            print("Connected to BACKUP server!")

            # send message to backup
            client_socket.sendall(b"Hello Backup!")

            # receive response from backup
            response = client_socket.recv(1024)

            print(f"Backup says: {response.decode()}")

            # stop retrying after successful connection
            break


        except ConnectionRefusedError:
            print(f"Backup server not ready. Attempt {attempt}/5")

            # wait before trying again
            if attempt < 5:
                time.sleep(2)

        finally:
            client_socket.close()


# communicate with PRIMARY 
else:
    message = "Hello Primary!"

    client_socket.sendall(message.encode())

    response = client_socket.recv(1024)
    
    print(f"Primary says: {response.decode()}")

finally:
    client_socket.close()


