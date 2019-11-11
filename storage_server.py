import os
import socket


def recieve_file(dest_location): # run when client wants to upload file
    print('DEBUG: recieve_file function')

    if os.path.exists(dest_location):
        print('File already exists, saving it as: ', end='') # TODO: Send this message to client
        dest_location, ext = dest_location[:dest_location.rfind('.')], dest_location[dest_location.rfind('.') + 1:]
        number = 0
        if dest_location[-1] == ')':
            try:
                number = int(dest_location[dest_location.rfind('(') + 1:-1])
            except:
                pass
        number += 1

        if number != 1:
            dest_location = dest_location[:dest_location.rfind('(')]

        dest_location += '(' + str(number) + ').' + ext

        print(dest_location)

    f = open(dest_location, 'wb+')
    number_of_kb = int(recieve_string())

    for i in range(number_of_kb):
        f.write(s.recv(1024))

    f.close()

    print('file ' + dest_location + ' recieved')

def send_file(local_location): # run when client want to download file
    print('DEBUG: send_file function')

    f = open(local_location)
    to_send = []
    chunk = f.read(1024)
    while chunk:
        to_send.append(chunk)
        chunk = f.read(1024)

    send_string_as_kb(len(to_send))  # TODO probably will need to add some 0-s in the last kb

    for kb in to_send:
        s.send(kb)

    f.close()

    print('file ' + local_location + ' sent')

def recieve_string():
    st = bytearray(s.recv(1024))
    while st[0] == 0:
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


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('', 8800))
s.listen()

con, addr = s.accept()

while True:
    command = recieve_string() # TODO handle syntax errors

    if command[:2] == 'uf':
        command, local_location, dest_location = map(str, command.split())
        recieve_file(dest_location)
    elif command[:2] == 'df':
        command, dest_location, local_location = map(str, command.split())
        send_file()
    else:
        os.system(command) # TODO pass output of this to client
