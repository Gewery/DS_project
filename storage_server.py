import os
import socket
import subprocess
import sys
from subprocess import Popen, PIPE


def recieve_file(con, file_location_server): # run when client wants to upload file
    if os.path.exists(file_location_server):
        print('File already exists, saving it as: ', end='')
        file_location_server, ext = file_location_server[:file_location_server.rfind('.')], file_location_server[file_location_server.rfind('.') + 1:]

        number = 1
        while os.path.exists(file_location_server + '_copy' + str(number)):
            number += 1

        file_location_server += '_copy' + str(number) + '.' + ext

        print(file_location_server)

    f = open(file_location_server, 'wb+')
    number_of_kb = int(recieve_string(con))

    for i in range(number_of_kb):
        f.write(con.recv(1024))

    f.close()

    print('file ' + file_location_server + ' recieved')

def send_file(connection, file_location_server): # run when client want to download file
    f = open(file_location_server, 'rb') # TODO check if file exists
    to_send = []
    chunk = f.read(1024)
    while chunk:
        to_send.append(chunk)
        chunk = f.read(1024)

    send_string_to_s(connection, str(len(to_send)))

    for kb in to_send:
        connection.send(kb)

    f.close()

    print('file ' + file_location_server + ' sent')

def recieve_string(con):
    try:
        st = bytearray(con.recv(1024))
    except:
        con.close()
        print('connection closed')
        return ""


    while len(st) != 0 and st[0] == 0:
        st.remove(0)

    return st.decode('utf-8')

def send_string_to_s(con, st):
    encoded_command = bytes(st, 'utf-8')
    kb = bytearray()
    for i in range(1024 - len(encoded_command)):
        kb.append(0)
    kb += encoded_command
    con.send(kb)  # send command with 0-bytes in the beginning

def wait_for_connection():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', 8802))
    sock.listen()
    connection, addr = sock.accept()
    return connection


# def return_syntax_error(st):
#     send_string_to_s("Syntax error in recieved command:" + st)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('', 8801))
s.listen()

root_dir = 'mount'
working_dir = root_dir

while True:
    con, addr = s.accept()
    print(str(addr) + 'connected')

    while True:
        command = recieve_string(con) # TODO handle syntax errors
        print('recieved string:', command)
        if len(command) == 0:
            break

        if command[:13] == 'recieve file:':
            file_location_server = command[13:]
            connection = wait_for_connection()
            recieve_file(connection, file_location_server)
            send_string_to_s(con, 'recieved')
            connection.close()
        elif command[:10] == 'send file:':
            file_location_server = command[10:]
            connection = wait_for_connection()
            send_file(connection, file_location_server)
            send_string_to_s(con, 'sent')
            connection.close()
        else:
            p = Popen([command], stdout = PIPE, stderr = PIPE, shell=True)
            output, error = p.communicate()
            if p.returncode == 0:
                send_string_to_s(con, output.decode('utf-8'))
            else:
                send_string_to_s(con, error.decode('utf-8'))
