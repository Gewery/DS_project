import os
import socket
from subprocess import Popen, PIPE
import multiprocessing

timeout = 5 # 5 seconds to connect to another ss

def recieve_file(con, file_location_server): # run when client wants to upload file
    if os.path.exists(file_location_server):
        number_of_kb = int(recieve_string(con))
        for i in range(number_of_kb):
            con.recv(1024)
        print('file ' + file_location_server + ' already exists (skipped)')
        return 'recieved'

    f = open(file_location_server, 'wb+')
    number_of_kb = int(recieve_string(con))

    for i in range(number_of_kb):
        f.write(con.recv(1024))

    f.close()

    print('file ' + file_location_server + ' recieved')
    return 'recieved'

def send_file(connection, file_location_server): # run when client want to download file
    if not os.path.exists(file_location_server): # in case this file already deleted by rm command
        send_string_to_s(connection, str(0))
        return 'sent'

    f = open(file_location_server, 'rb')
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
    return 'sent'

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

def connect(socket, addr, port):
    socket.connect((addr, port))

accept_connection_return_value = ()
def accept_connection(sock, return_dict):
    return_dict['rv'] = sock.accept()

def wait_for_connection(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', port))
    sock.listen()

    # added timeouts to not wait fallen server to communicate
    manager = multiprocessing.Manager()
    return_dict = manager.dict()

    p = multiprocessing.Process(target=accept_connection, args=(sock, return_dict))
    p.start()
    p.join(timeout)

    if p.is_alive():
        print('Timeout exceeded')
        p.terminate()
        p.join()
        return -1
    else:
        connection, addr = return_dict['rv']
        return connection

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('', 8801))
s.listen()

root_dir = 'mount'
working_dir = root_dir
port_p2 = 8803

while True:
    con, addr = s.accept()
    print(str(addr) + 'connected')

    while True:
        command = recieve_string(con) # TODO handle syntax errors
        print('recieved string:', command)
        if len(command) == 0:
            break

        if command[:13] == 'recieve file:':
            file_location_server = command[13:-4]
            port = int(command[-4:])
            connection = wait_for_connection(port)
            if connection == -1:
                send_string_to_s(con, 'Timeout exceeded')
            else:
                response = recieve_file(connection, file_location_server)
                send_string_to_s(con, response)
                connection.close()
        elif command[:10] == 'send file:':
            file_location_server = command[10:-4]
            port = int(command[-4:])
            if port == port_p2:
                sock = socket.socket()
                addr = command[command.rfind('addr:') + 5:-4]
                # added timeouts to not wait fallen server to communicate
                p = multiprocessing.Process(target=connect, args=(sock, addr, port))
                p.start()
                p.join(timeout)

                if p.is_alive():
                    print('Timeout exceeded')
                    p.terminate()
                    p.join()
                    send_string_to_s(con, 'Timeout exceeded')
                else:
                    file_location_server = command[10:command.rfind('addr:')]
                    response = send_file(sock, file_location_server)
                    send_string_to_s(con, response)
            else:
                connection = wait_for_connection(port)
                response = send_file(connection, file_location_server)
                send_string_to_s(con, response)
                connection.close()
        else:
            p = Popen([command], stdout = PIPE, stderr = PIPE, shell=True)
            output, error = p.communicate()
            if p.returncode == 0:
                send_string_to_s(con, output.decode('utf-8'))
            else:
                send_string_to_s(con, error.decode('utf-8'))
