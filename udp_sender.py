import socket
import time


# which computer/network interface should receive the heartbeats
# both programs are running on this computer/my laptop
HOST = "127.0.0.1"

# UDP port where the backup server is waiting for heartbeats
HEARTBEAT_PORT = 5051


# this function sends fake primary heartbeat messages
# useful for testing the backup without running the actual primary server
def send_heartbeats():

    # create a network communication object -> using IPv4 -> using UDP
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        # keep sending heartbeat messages until we stop the program
        while True:

            # send ALIVE as bytes to the backup server
            udp_socket.sendto(
                b"ALIVE",
                (HOST, HEARTBEAT_PORT)
            )

            print("Test sender: Heartbeat sent")

            # wait 1 second before sending the next heartbeat
            time.sleep(1)

    # always close the UDP socket when the program stops
    finally:
        udp_socket.close()


# only start sending heartbeats when this file is run directly
if __name__ == "__main__":
    send_heartbeats()