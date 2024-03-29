import os
import socket
import time
import sys


def upload_file(sock, client_location):
    f = open(client_location, 'rb')  # TODO check if file exists
    to_send = []
    chunk = f.read(1024)
    while chunk:
        to_send.append(chunk)
        chunk = f.read(1024)

    send_string_as_kb(str(len(to_send)), sock)

    for kb in to_send:
        sock.send(kb)

    f.close()

    print('file ' + client_location + ' sent')


def download_file(sock, client_location):
    if os.path.exists(client_location):
        print('File already exists, saving it as: ', end='')
        client_location, ext = client_location[:client_location.rfind('.')], client_location[
                                                                             client_location.rfind('.') + 1:]

        number = 1
        while os.path.exists(client_location + '_copy' + str(number) + '.' + ext):
            number += 1

        client_location += '_copy' + str(number) + '.' + ext

        print(client_location)

    f = open(client_location, 'wb+')
    number_of_kb = int(recieve_string(sock))

    for i in range(number_of_kb):
        f.write(sock.recv(1024))

    f.close()

    print('file ' + client_location + ' recieved')


def recieve_string(s):
    st = bytearray(s.recv(1024))
    while len(st) != 0 and st[0] == 0:
        st.remove(0)

    return st.decode('utf-8')


def send_string_as_kb(st, s):
    encoded_command = bytes(st, 'utf-8')
    kb = bytearray()
    for i in range(1024 - len(encoded_command)):
        kb.append(0)
    kb += encoded_command
    s.send(kb)  # send command with 0-bytes in the beginning


def connect_to(ss_addr, ss_port):
    sock = socket.socket()
    sock.connect((ss_addr, ss_port))
    return sock


print(
    'commands:\nupload file: uf [location on localhost] [location on server (with name of file)]\n'
    'download file: df [location of file on server] [location on localhost (with name of file)]\n'
    'initialization: init\n'
    'file creation: touch [directory and name]\n'
    'directory creation: mkdir [directory]\n'
    'directory deletion: rmdir [directory]\n')

nameserver_address, nameserver_port = "18.191.53.235", 8800
s = socket.socket()
s.connect((nameserver_address, nameserver_port))
working_dir = recieve_string(s)

# storage_addr_bytes = s.recv(4)
# storage_addr = ""
# for x in storage_addr_bytes:
#     storage_addr += str(x) + '.'
# storage_addr = storage_addr[:-1]
# print('Storage server address:', storage_addr)

while True:
    command = input('~' + working_dir + '> ')

    if command[:2] == 'uf':  # TODO white list of commands?
        lst = list(map(str, command.split()))
        if len(lst) != 3:
            print('Wrong format of command ' + command)
            continue

        cmd, client_location, server_location = map(str, command.split())
        if not os.path.exists(client_location):
            print('File ' + client_location + ' does not exists')
            continue
        send_string_as_kb(command, s)
        recieve_st = recieve_string(s)
        if recieve_st[:13] != 'send file to:':
            print('Error occured. Recieved command from nameserver:', recieve_st)
        else:
            ss_addr = recieve_st[13:-4]
            ss_port = int(recieve_st[-4:])
            sock = connect_to(ss_addr, ss_port)
            upload_file(sock, client_location)
        continue
    elif command[:2] == 'df':
        lst = list(map(str, command.split()))
        if len(lst) != 3:
            print('Wrong format of command ' + command)
            continue
        send_string_as_kb(command, s)
        command, server_location, client_location = map(str, command.split())
        recieve_st = recieve_string(s)
        if recieve_st[:18] != 'recieve file from:':
            print('Error occured. Recieved command from nameserver:', recieve_st)
        else:
            ss_addr = recieve_st[18:-4]
            ss_port = int(recieve_st[-4:])
            sock = connect_to(ss_addr, ss_port)
            download_file(sock, client_location)
        continue

    send_string_as_kb(command, s)
    if command == 'init':
        working_dir = ''
        recieve_st = recieve_string(s)
        if len(recieve_st) != 0:
            print(recieve_st)
    else:
        recieve_st = recieve_string(s)
        if command == "ls":
            recieve_st = recieve_st.replace('\n', ' ')

        lst = list(map(str, command.split()))
        if lst[0] == 'cd' and recieve_st[:13] == 'cd_command_ok':
            working_dir = recieve_st[13:]
            continue
        if len(recieve_st) != 0:
            print(recieve_st)
