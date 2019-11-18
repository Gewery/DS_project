import socket
import time
from subprocess import Popen, PIPE
from threading import Thread

class ServerConnection(Thread):
    def __init__(self, address: str, port: int, address_for_client: str):
        super().__init__(daemon=True)
        self.socket = socket.socket()
        try:
            self.socket.connect((address, port))
            server_connections_online.append(self)
        except:
            pass
        self.address = address
        self.address_for_client = address_for_client
        # Queues contains commands to send with different priority
        self.commands_to_send_p1 = [] #[(command, correct_response), (), ..., ()]
        self.commands_to_send_p2 = []
        self.last_checked = time.time()
        self.response = ''

    def reconnect(self):
        print('reconnecting to server' + self.address)
        try:
            self.socket = socket.socket()
            self.socket.connect((self.address, storage_port))
            server_connections_online.append(self)
            print('reconnected')
        except:
            self.last_checked = time.time()
            print('reconnection failed')
            pass

    def ping(self):
        # print('pinging...')
        self._send_string('ping')
        if self._recieve_string() == 'ping':
            # print('success')
            return True
        else:
            # print('fail')
            return False

    def run(self):
        print('Thread started, address: ' + self.address)
        while True:
            if time.time() - self.last_checked > ping_timeout:
                if self not in server_connections_online:
                    self.reconnect()
                elif not self.ping():
                    server_connections_online.remove(self)
                self.last_checked = time.time()

            if len(self.commands_to_send_p1) > 0:
                command, correct_response = self.commands_to_send_p1.pop(0)
                print('executing: ' + command + ' and waiting for >' + correct_response + '<')
                self._send_string(add_to_command(command, root))
                response = self._recieve_string()
                print('got response >' + response + '<')
                if correct_response == '!ANY!':
                    self.response = response
                elif response != correct_response:
                    print('Command ' + add_to_command(command, root) + ' not executed on server ' + self.address + '. Trying again')
                    self.commands_to_send_p1.insert(0, (command, correct_response))
                else:
                    if command[:6] == 'touch ':
                        for file in list(map(str, command.split()))[1:]:
                            if file not in servers_with_file:
                                servers_with_file[file] = []
                            if self not in servers_with_file[file]:
                                servers_with_file[file].append(self)
                    elif command[:3] == 'cp ':
                        file = list(map(str, command.split()))[2]
                        if file not in servers_with_file: # imp
                            servers_with_file[file] = []
                        if self not in servers_with_file[file]: # imp
                            servers_with_file[file].append(self)
                    elif command[:3] == 'rm ':
                        rf = 0
                        if command[1] == '-rf':
                            rf = 1
                        for file in list(map(str, command.split()))[1 + rf:]:
                            for key in servers_with_file.keys(): # rm -rf support
                                if key.find(file) == 0:
                                    if file in servers_with_file and self in servers_with_file[file]:
                                        servers_with_file[key].remove(self)
                                        if len(servers_with_file[file]) == 0:
                                            servers_with_file.pop(file)
                    continue

                    
            if len(self.commands_to_send_p2) > 0: # replication commands only
                command, correct_response = self.commands_to_send_p2.pop(0)
                print('p2 executing: ' + command + ' and waiting for >' + correct_response + '<')
                self._send_string(add_to_command(command, root))
                response = self._recieve_string()
                print('p2 got response >' + response + '<')
                if response != correct_response:
                    print(
                        'Command ' + command + ' was not executed on server ' + self.address + '. Will try again later')
                    self.commands_to_send_p2.append((command, correct_response))
                elif command[:13] == 'recieve file:':
                    file_name = command[13:-4]
                    print('I know that ' + file_name + ' was recieved by ' + self.address);
                    if file_name not in servers_with_file: servers_with_file[file_name] = []
                    if self not in servers_with_file[file_name]:
                        servers_with_file[file_name].append(self)
                    distrubute_file(file_name)


    def _send_string(self, st):
        if st != 'ping':
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

ping_timeout = 2

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


server_connections = []
server_connections_online = []
servers = [('3.134.84.124', '3.134.84.124')]
storage_port = 8801
servers_with_file = {} # stores connections
port_p2 = 8803
port_p1 = 8802

def connect_to_servers():
    for storage_addr, storage_addr_for_client in servers:
        s_sender = ServerConnection(storage_addr, storage_port, storage_addr_for_client)
        server_connections.append(s_sender)
        s_sender.start()

def send_command_to_servers(command, correct_response):
    for s_sender in server_connections:
        s_sender.commands_to_send_p1.append((command, correct_response))
        print(command + ' added to queue p1. Correct response = ' + correct_response)

def distrubute_file(file):
    for server_from in servers_with_file[file]:
        for server_to in server_connections:
            if server_to in servers_with_file[file]:
                continue
            server_from.commands_to_send_p2.append(('send file:' + concat_path(root, file) + 'addr:' + server_to.address + str(port_p2), 'sent'))
            server_to.commands_to_send_p2.append(('recieve file:' + concat_path(root, file) + str(port_p2), 'recieved'))

def concat_path(path_1, path_2, path_3 = ''):
    result = path_1
    if len(path_2) != 0:
        if path_2[0] == '/': path_2 = path_2[1:]
        if len(path_2) != 0 and path_2[-1] == '/': path_2 = path_2[:-1]
        if len(result) != 0:
            result += '/'
        result += path_2
    if len(path_3) != 0:
        if path_3[0] == '/':
            path_3 = path_3[1:]
        result += '/' + path_3

    result = result.rstrip()

    return result

def add_to_command(command, to_add):
    if command[:10] == 'send file:' or command[:13] == 'recieve file:':
        return command
    lst = list(map(str, command.split()))
    command = lst[0]
    added_count = 0
    for i in range(1, len(lst)):
        if lst[i][0].isalpha() or lst[i][0].isdigit() or lst[i][0] == '_' or lst[i][0] == '.':
            command += ' ' + concat_path(to_add, lst[i])
            added_count += 1
        else:
            command += ' ' + lst[i]

    if added_count == 0:
        command += ' ' + to_add

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

        if command == 'init':
            servers_with_file.clear()
            working_dir = ''

            for scon in server_connections:
                scon.commands_to_send_p1.clear()
                scon.commands_to_send_p2.clear()

            p = Popen(['rm -rf mount'], stdout=PIPE, stderr=PIPE, shell=True)
            output, error = p.communicate()
            send_command_to_servers('rm -rf ', output.decode('utf-8'))

            p = Popen(['mkdir mount'], stdout=PIPE, stderr=PIPE, shell=True)
            output, error = p.communicate()
            send_command_to_servers('mkdir ', output.decode('utf-8'))

            available_size = ''

            for scon in server_connections_online:
                scon.commands_to_send_p1.append(('get_available_size', '!ANY!'))
                for i in range(2):
                    if scon.response == '':
                        time.sleep(0.2)
                if scon.response == '':
                    continue
                available_size = scon.response
                scon.response = ''
                break

            if available_size == '':
                send_string_to_client('No servers online, try later')
            else:
                send_string_to_client(available_size)

        elif command[:2] == 'uf':
            lst = list(map(str, command.split()))
            if len(lst) > 3:
                send_string_to_client("Wrong format of command: " + command)
                continue
                
            command, file_location_client, file_location_server = map(str, command.split())
            file_location_server = concat_path(working_dir, file_location_server)

            if file_location_server in servers_with_file:
                send_string_to_client('File ' + file_location_server + ' already exists. Choose another name')
            else:
                while len(server_connections_online) == 0:
                    print('Waiting for any storage server to turn on')
                    time.sleep(5)
                server_connection = server_connections_online[0]
                server_connection.commands_to_send_p1.append(('recieve file:' + concat_path(root, file_location_server) + str(port_p1), 'recieved'))
                send_string_to_client('send file to:' + server_connection.address_for_client + str(port_p1))

                servers_with_file[file_location_server] = []
                servers_with_file[file_location_server].append(server_connection)
                p = Popen(['touch ' + concat_path(root, file_location_server)], stdout=PIPE, stderr=PIPE, shell=True)
                output, error = p.communicate()
                if p.returncode != 0:
                    print(error.decode('utf-8'))
                else:
                    distrubute_file(file_location_server)

        elif command[:2] == 'df': 
            lst = list(map(str, command.split()))
            if len(lst) > 3:
                send_string_to_client("Wrong format of command: " + command)
                continue
                
            command, file_location_server, file_location_client = map(str, command.split())
            file_location_server = concat_path(working_dir, file_location_server)

            if file_location_server not in servers_with_file:
                send_string_to_client('File ' + file_location_server + ' does not exists')
            else:
                if len(servers_with_file[file_location_server]) == 0: # There is nothing we can do
                    print('Wow, File not found on any servers')
                    continue
                flag = 0
                server_connection = ''
                while not flag:
                    for scon in servers_with_file[file_location_server]:
                        if scon in server_connections_online:
                            server_connection = scon
                            flag = 1
                            break
                    print('Waiting for any storage server with this file to turn on')
                    time.sleep(5)

                send_string_to_client('recieve file from:' + server_connection.address_for_client + str(port_p1))
                server_connection.commands_to_send_p1.append(('send file:' + concat_path(root, file_location_server) + str(port_p1), 'sent'))
        elif command[:5] == 'stat ':
            lst = list(map(str, command.split()))
            file_location_server = lst[1]
            file_location_server = concat_path(working_dir, file_location_server)
            for scon in servers_with_file[file_location_server]:
                if scon in server_connections_online:
                    scon.commands_to_send_p1.append((add_to_command(command, working_dir), '!ANY!'))
                    for i in range(2):
                        if scon.response == '':
                            time.sleep(0.2)
                    if scon.response == '':
                        continue
                    file_stat = scon.response
                    scon.response = ''
            if file_stat == '':
                send_string_to_client('No servers online, try later')
            else:
                send_string_to_client(file_stat)
        else:
            lst = list(map(str, command.split()))
            p = Popen([add_to_command(add_to_command(command, working_dir), root)], stdout=PIPE, stderr=PIPE, shell=True)
            output, error = p.communicate()
            nameserver_result = ''
            if p.returncode == 0:
                if command[:2] == 'ls':
                    send_string_to_client(output.decode('utf-8'))
                    continue
                if command[:3] == 'cd ':
                    if lst[1] == '..':
                        if len(working_dir) != 0:
                            if working_dir.rfind('/') == -1:
                                working_dir = ''
                            else:
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
            send_command_to_servers(add_to_command(command, working_dir), nameserver_result)
            send_string_to_client(nameserver_result)