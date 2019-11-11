import socket
import time

def get_available_storage_address():
    return [127, 0, 0, 1]

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('', 8800))
s.listen()

con, addr = s.accept()
print(str(addr) + ' connected')

storage_addr = get_available_storage_address()
con.send(bytes(storage_addr))
print(str(storage_addr) + ' sent to client')

con.close()

print('connection closed')