import socket
import threading

# import the function that handles TCP clients in our primary server
# we only want to test this function, not start the entire server
from server import handle_client as primary_handle_client

# import the function that handles TCP clients in our backup server
# give it a different name so Python can tell the two functions apart
from udp_receiver import handle_client as backup_handle_client


# first, test if the primary server responds correctly to a client
# pytest automatically finds functions whose names start with test_
def test_primary_response():

    # create two sockets that are already connected to each other
    # one socket acts as the server side and the other acts as the client side
    # this lets us test TCP-style communication without using actual TCP ports
    server_side, client_side = socket.socketpair()

    # create a separate thread to run the primary server's handle_client function
    # pass the server-side socket and a fake client address to the function
    worker = threading.Thread(
        target=primary_handle_client,
        args=(server_side, ("local", 0))
    )

    # start the thread so the server can wait for a client message
    worker.start()

    try:
        # only wait up to 2 seconds for a response
        # prevents the test from waiting forever if something goes wrong
        client_side.settimeout(2)

        # send a test message from the client side to the server side
        client_side.sendall(b"Test primary")

        # wait for the primary server to send a response
        response = client_side.recv(1024)

        # check if the response is exactly what we expected
        # if the condition is True, the test continues
        # if the condition is False, pytest marks the test as failed
        assert response == b"Hello from PRIMARY!"

    finally:
        # always close the client socket after the test
        client_side.close()

        # wait up to 2 seconds for the server thread to finish
        worker.join(timeout=2)


# second, test if the backup server responds correctly to a client
def test_backup_response():

    # create two connected sockets for our backup server test
    server_side, client_side = socket.socketpair()

    # create a thread to run the backup server's handle_client function
    worker = threading.Thread(
        target=backup_handle_client,
        args=(server_side, ("local", 0))
    )

    # start the backup server's client-handling function
    worker.start()

    try:
        # set a 2 second timeout so the test does not wait forever
        client_side.settimeout(2)

        # send a message to the backup server
        client_side.sendall(b"Test backup")

        # receive the backup server's response
        response = client_side.recv(1024)

        # verify that the backup returns the expected message
        # pytest reports a failure if the response is different
        assert response == b"Hello from NEW PRIMARY!"

    finally:
        # close the client socket even if the test fails
        client_side.close()

        # wait for the backup server's thread to finish
        worker.join(timeout=2)