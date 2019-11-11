import os
import socket
import time
import sys

def upload_file(local_location, dest_location):
    f = open(local_location)
    to_send = []
    chunk = f.read(1024)
    while chunk:
        to_send.append(chunk)
        chunk = f.read(1024)

    send_string_as_kb(len(to_send)) # TODO probably will need to add some 0-s in the last kb

    for kb in to_send:
        s.send(kb)

    f.close()

    print('file ' + local_location + ' sent')


def download_file(dest_location, local_location):
    if os.path.exists(dest_location):
        print('File already exists, saving it as: ', end='')
        local_location, ext = local_location[:local_location.rfind('.')], local_location[local_location.rfind('.') + 1:]
        number = 0
        if local_location[-1] == ')':
            try:
                number = int(local_location[local_location.rfind('(') + 1:-1])
            except:
                pass
        number += 1

        if number != 1:
            local_location = local_location[:local_location.rfind('(')]

            local_location += '(' + str(number) + ').' + ext

        print(local_location)

    f = open(local_location, 'wb+')

    number_of_kb = int(recieve_string())

    for i in range(number_of_kb):
        f.write(s.recv(1024))

    f.close()

    print('file ' + dest_location + ' recieved')


def recieve_string():
    st = bytearray(s.recv(1024))
    while len(st) != 0 and st[0] == 0:
        st.remove(0)

    return st.decode('utf-8')


def send_string_as_kb(st):
    #global s
    encoded_command = bytes(st, 'utf-8')
    kb = bytearray()
    for i in range(1024 - len(encoded_command)):
        kb.append(0)
    kb += encoded_command
    s.send(kb)  # send command with 0-bytes in the beginning

print(
    'commands:\nupload file: uf [location on localhost] [location on server (with name of file)]\ndownload file: df [location of file on server ] [location on localhost (with name of file)]\n')

nameserver_address, nameserver_port = "3.15.180.89", 8800
storage_port = 8800
s = socket.socket()
s.connect((nameserver_address, nameserver_port))

storage_addr_bytes = s.recv(4)
storage_addr = ""
for x in storage_addr_bytes:
    storage_addr += str(x) + '.'
storage_addr = storage_addr[:-1]
print('Storage server address:', storage_addr)

s.close()

s = socket.socket()
s.connect((storage_addr, storage_port))

while True:
    print(end='> ')
    command = input()

    send_string_as_kb(command)

    if command[:2] == 'uf':
        command, local_location, dest_location = map(str, command.split())
        upload_file(local_location, dest_location)
        print('DEBUG: ' + command + ' from ' + local_location + ' to ' + dest_location)
    elif command[:2] == 'df':
        command, dest_location, local_location = map(str, command.split())
        download_file(dest_location, local_location)
        print('DEBUG: ' + command + ' from ' + local_location + ' to ' + dest_location)
    else:
        recieve_st = recieve_string()
        if command == "ls":
            recieve_st = recieve_st.replace('\n', ' ')
        print(recieve_st)
