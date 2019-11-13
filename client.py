import os
import socket
import time
import sys


def upload_file(client_location):
    f = open(client_location, 'rb')
    to_send = []
    chunk = f.read(1024)
    while chunk:
        to_send.append(chunk)
        chunk = f.read(1024)

    send_string_as_kb(str(len(to_send)))  # TODO probably will need to add some 0-s in the last kb

    for kb in to_send:
        s.send(kb)

    f.close()

    print('file ' + client_location + ' sent')


def download_file(client_location):
    if os.path.exists(client_location):
        print('File already exists, saving it as: ', end='')
        client_location, ext = client_location[:client_location.rfind('.')], client_location[client_location.rfind('.') + 1:]

        number = 1
        while os.path.exists(client_location + '_copy' + str(number) + '.' + ext):
            number += 1

        client_location += '_copy' + str(number) + '.' + ext

        print(client_location)

    f = open(client_location, 'wb+')
    number_of_kb = int(recieve_string())

    for i in range(number_of_kb):
        f.write(s.recv(1024))

    f.close()

    print('file ' + client_location + ' recieved')


def recieve_string():
    st = bytearray(s.recv(1024))
    while len(st) != 0 and st[0] == 0:
        st.remove(0)

    return st.decode('utf-8')


def send_string_as_kb(st):
    encoded_command = bytes(st, 'utf-8')
    kb = bytearray()
    for i in range(1024 - len(encoded_command)):
        kb.append(0)
    kb += encoded_command
    s.send(kb)  # send command with 0-bytes in the beginning

print(
    'commands:\nupload file: uf [location on localhost] [location on server (with name of file)]\n'
    'download file: df [location of file on server] [location on localhost (with name of file)]\n')

nameserver_address, nameserver_port = "18.218.164.132", 8800
storage_port = 8800
s = socket.socket()
s.connect((nameserver_address, nameserver_port))

# storage_addr_bytes = s.recv(4)
# storage_addr = ""
# for x in storage_addr_bytes:
#     storage_addr += str(x) + '.'
# storage_addr = storage_addr[:-1]
# print('Storage server address:', storage_addr)

working_dir = '~'

while True:
    command = input(working_dir + '> ')

    send_string_as_kb(command)

    if command[:2] == 'uf': # TODO while list of commands?
        command, client_location, server_location = map(str, command.split())
        upload_file(client_location)
        print('DEBUG: ' + command + ' from ' + client_location + ' to ' + server_location)
    elif command[:2] == 'df':
        command, server_location, client_location = map(str, command.split())
        download_file(client_location)
        print('DEBUG: ' + command + ' from ' + client_location + ' to ' + server_location)
    else:
        recieve_st = recieve_string()
        if command == "ls":
            recieve_st = recieve_st.replace('\n', ' ')

        lst = list(map(str, command.split()))
        if lst[0] == 'cd' and recieve_st == 'ok':
            if lst[1][0] == '/': lst[1] = lst[1][1:]
            if lst[1][-1] == '/': lst[1] = lst[1][:-1]

            if lst[1] == '..':
                if working_dir.rfind('/') != -1:
                    working_dir = working_dir[:working_dir.rfind('/')]
            else:
                working_dir += '/' + lst[1]
        if len(recieve_st) != 0:
            print(recieve_st)

