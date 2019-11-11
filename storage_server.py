import os
import socket
import subprocess
import sys


def recieve_file(server_location): # run when client wants to upload file
    print('DEBUG: recieve_file function')
    if os.path.exists(server_location):
        print('File already exists, saving it as: ', end='')
        server_location, ext = server_location[:server_location.rfind('.')], server_location[server_location.rfind('.') + 1:]

        number = 1
        while os.path.exists(server_location + '_copy' + str(number)):
            number += 1

        server_location += '_copy' + str(number) + '.' + ext

        print(server_location)

    f = open(server_location, 'wb+')
    number_of_kb = int(recieve_string())

    for i in range(number_of_kb):
        f.write(con.recv(1024))

    f.close()

    print('file ' + server_location + ' recieved')

def send_file(server_location): # run when client want to download file
    print('DEBUG: send_file function')

    f = open(server_location, 'rb')
    to_send = []
    chunk = f.read(1024)
    while chunk:
        to_send.append(chunk)
        chunk = f.read(1024)

    send_string_as_kb(str(len(to_send)))  # TODO probably will need to add some 0-s in the last kb

    for kb in to_send:
        con.send(kb)

    f.close()

    print('file ' + server_location + ' sent')

def recieve_string():
    try:
        st = bytearray(con.recv(1024))
    except:
        con.close()
        print('connection closed')
        return ""


    while len(st) != 0 and st[0] == 0:
        st.remove(0)

    return st.decode('utf-8')

def send_string_as_kb(st):
    encoded_command = bytes(st, 'utf-8')
    kb = bytearray()
    for i in range(1024 - len(encoded_command)):
        kb.append(0)
    kb += encoded_command
    con.send(kb)  # send command with 0-bytes in the beginning


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('', 8800))
s.listen()

while True:
    con, addr = s.accept()
    print(str(addr) + 'connected')

    while True:
        command = recieve_string() # TODO handle syntax errors

        if len(command) == 0:
            break

        if command[:2] == 'uf':
            command, client_location, server_location = map(str, command.split())
            recieve_file(server_location)
        elif command[:2] == 'df':
            command, server_location, client_location = map(str, command.split())
            send_file(server_location)
        else:
            try:
                result = subprocess.check_output(command).decode('utf-8')
                send_string_as_kb(result)
            except:
                send_string_as_kb(str(sys.exc_info()[1]))
