import socket
import os
import time
from subprocess import Popen, PIPE
from threading import Thread

class ServerSender(Thread):
    def __init__(self, socket: socket.socket, address: str):
        super().__init__(daemon=True)
        self.socket = socket
        self.address = address
        # Queues contains commands to send with different priority
        self.commands_to_send_p1 = [] #[(command, correct_response), (), ..., ()]
        self.commands_to_send_p2 = []

    def run(self): # TODO add online_servers support
        print('I started, address: ' + self.address)
        while True:
            if len(self.commands_to_send_p1) > 0:
                command, correct_response = self.commands_to_send_p1.pop(0)
                self._send_string(command)
                response = self._recieve_string()
                if response != correct_response:
                    print('Command ' + command + ' not executed on server ' + self.address + '. Trying again')
                    self.commands_to_send_p1.insert(0, (command, correct_response))
                    
            if len(self.commands_to_send_p2) > 0:
                command, correct_response = self.commands_to_send_p2.pop(0)
                self._send_string(command)
                response = self._recieve_string()
                if response != correct_response:
                    print(
                        'Wow, Command ' + command + ' not executed on server ' + self.address + '. Trying again')
                    self.commands_to_send_p1.insert(0, (command, correct_response))

    def _send_string(self, st):
        print('sending string to server:', st)
        encoded_command = bytes(st, 'utf-8')
        kb = bytearray()
        for i in range(1024 - len(encoded_command)):
            kb.append(0)
        kb += encoded_command
        self.socket.send(kb)

    def _recieve_string(self):
        st = bytearray(self.socket.recv(1024))
        while len(st) != 0 and st[0] == 0:
            st.remove(0)

        return st.decode('utf-8')


def get_available_storage_address():
    return [127, 0, 0, 1]


def recieve_string_from_client():
    try:
        st = bytearray(con.recv(1024))
    except:
        con.close()
        print('connection closed')
        return ""


    while len(st) != 0 and st[0] == 0:
        st.remove(0)

    return st.decode('utf-8')

def send_string_to_client(st):
    print('sending string to client:', st)
    encoded_command = bytes(st, 'utf-8')
    kb = bytearray()
    for i in range(1024 - len(encoded_command)):
        kb.append(0)
    kb += encoded_command
    con.send(kb)  # send command with 0-bytes in the beginning


server_senders = []
servers = ['3.15.137.86']
servers_online = ['3.15.137.86']
storage_port = 8800

def connect_to_servers():
    for storage_addr in servers:
        server_sock = socket.socket()
        server_sock.connect((storage_addr, storage_port))
        s_sender = ServerSender(server_sock, storage_addr)
        server_senders.append(s_sender)
        s_sender.start()

def send_command_to_servers(command, correct_response):
    for s_sender in server_senders:
        s_sender.commands_to_send_p1.append((command, correct_response))
        print(command + ' added to queue p1. correct_response = ' + correct_response)


def concat_path(path_1, path_2 = '', path_3 = ''):
    result = path_1
    if len(path_2) != 0:
        if path_2[0] == '/': path_2 = path_2[1:]
        if len(path_2) != 0 and path_2[-1] == '/': path_2 = path_2[:-1]
        result += '/' + path_2
    if len(path_3) != 0:
        if path_3[0] == '/':
            path_3 = path_3[1:]
        result += '/' + path_3

    return result

def add_root_and_wd_to_command(command):
    lst = list(map(str, command.split()))
    command = lst[0]
    for i in range(1, len(lst)):
        if lst[i][0].isalpha() or lst[i][0].isdigit() or lst[i][0] == '_' or lst[i][0] == '.':
            command += ' ' + concat_path(root, working_dir, lst[i])

    if len(lst) == 1:
        command += ' ' + concat_path(root, working_dir)

    return command


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('', 8800))
s.listen()

connect_to_servers()

root = 'mount'
working_dir = ''

while True:
    con, addr = s.accept()
    print(str(addr) + 'connected')
    send_string_to_client(working_dir)

    while True:
        command = recieve_string_from_client()
        print('recieved string:', command)

        if len(command) == 0:
            break

        if command[:2] == 'uf': # TODO
            command, client_location, server_location = map(str, command.split())
            server_location = working_dir + server_location
            # recieve_file(server_location)
            continue
        elif command[:2] == 'df': # TODO
            command, server_location, client_location = map(str, command.split())
            server_location = working_dir + server_location
            # send_file(server_location)
            continue
        else:
            lst = list(map(str, command.split()))
            command = add_root_and_wd_to_command(command)
            p = Popen([command], stdout=PIPE, stderr=PIPE, shell=True)
            output, error = p.communicate()
            nameserver_result = ''
            if p.returncode == 0:
                if command[:3] == 'ls ':
                    send_string_to_client(output.decode('utf-8'))
                    continue
                if command[:3] == 'cd ':
                    print(lst, working_dir)
                    if lst[1] == '..':
                        if len(working_dir) != 0:
                            working_dir = working_dir[:working_dir.rfind('/')]
                    else:
                        working_dir = concat_path(working_dir, lst[1])
                    send_string_to_client("cd_command_ok" + working_dir)
                    continue
                nameserver_result = output.decode('utf-8')
            else:
                send_string_to_client(error.decode('utf-8'))
                continue
                
            # send to servers everything except ls, cd, uf, df
            send_command_to_servers(command, nameserver_result)
            send_string_to_client(nameserver_result)