import os
import socket
import subprocess
import sys
from subprocess import Popen, PIPE


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

    send_string_as_kb(str(len(to_send)))

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

# def return_syntax_error(st):
#     send_string_as_kb("Syntax error in recieved command:" + st)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('', 8800))
s.listen()

root_dir = 'mount'
working_dir = root_dir

while True:
    con, addr = s.accept()
    print(str(addr) + 'connected')

    while True:
        command = recieve_string() # TODO handle syntax errors
        print('recieved string:', command)
        if len(command) == 0:
            break

        if command[:2] == 'uf': # TODO
            command, client_location, server_location = map(str, command.split())
            server_location = working_dir + server_location
            recieve_file(server_location)
        elif command[:2] == 'df': # TODO
            command, server_location, client_location = map(str, command.split())
            server_location = working_dir + server_location
            send_file(server_location)
        else:
            p = Popen([command], stdout = PIPE, stderr = PIPE, shell=True)
            output, error = p.communicate()
            if p.returncode == 0:
                send_string_as_kb(output.decode('utf-8'))
            else:
                send_string_as_kb(error.decode('utf-8'))
