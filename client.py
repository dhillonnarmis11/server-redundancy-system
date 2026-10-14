import socket

# create a socket that uses IPv4 + TCP
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# tell client where server is
# tell client which computer has server
HOST = "127.0.0.1"
# which program/service on that computer
PORT = 5050

# connect client to server
client_socket.connect((HOST, PORT))
print("Connected to server!")

message = "Hello Server!"

# python string message converted/encoded to bytes as it transmist bytes/binary data
client_socket.send(message.encode())


data = client_socket.recv(1024)

response = data.decode()

print(f"Server says: {response}")

