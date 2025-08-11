import socket
import random

HOST = 'localhost'
PORT = 12345

number = random.randint(1, 100)
print('Generated number:', number)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall(str(number).encode())
