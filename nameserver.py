import socket
from threading import Thread

class ServerConnection(Thread):
    def __init__(self, socket: socket.socket):
        super().__init__(daemon=True)
        self.socket = socket

    def run(self): # TODO add online_servers support
        while True:
            if len(commands_to_send[self.socket]) > len(responses[self.socket]):
                self._send_string(commands_to_send[self.socket][len(responses[self.socket])])
                responses[self.socket].append(self._recieve_string())

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
    print('sending string to client:', st)
    encoded_command = bytes(st, 'utf-8')
    kb = bytearray()
    for i in range(1024 - len(encoded_command)):
        kb.append(0)
    kb += encoded_command
    con.send(kb)  # send command with 0-bytes in the beginning


commands_to_send = {}
responses = {}
sockets = []
servers = ['3.15.137.86']
servers_online = ['3.15.137.86']
storage_port = 8800

def connect_to_servers():
    for storage_addr in servers:
        server_sock = socket.socket()
        server_sock.connect((storage_addr, storage_port))
        sockets.append(server_sock)
        commands_to_send[server_sock] = []
        responses[server_sock] = []
        ServerConnection(server_sock).start()

def send_command_to_servers(command):
    command_number = {}
    for socket in sockets:
        command_number[socket] = len(commands_to_send)
        commands_to_send[socket].append(command)

    while True:
        number_of_responses = 0
        for socket in sockets:
            if command_number[socket] < len(responses[socket]):
                number_of_responses += 1

        if number_of_responses == len(servers_online):
            break

    return responses[sockets[0]][command_number[sockets[0]]] # TODO replace it to work with servers_online list


def concat_path(path_1, path_2 = '', path_3 = ''):
    result = path_1
    if len(path_2) != 0:
        result += '/' + path_2
    if len(path_3) != 0:
        result += '/' + path_3

    return result

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('', 8800))
s.listen()

connect_to_servers()

root = 'mount'
working_dir = ''

file_system = {root: []}

while True:
    con, addr = s.accept()
    print(str(addr) + 'connected')

    while True:
        command = recieve_string()  # TODO handle syntax errors
        print('recieved string:', command)

        if len(command) == 0:
            break

        if command[:2] == 'uf': # TODO
            command, client_location, server_location = map(str, command.split())
            server_location = working_dir + server_location
            # recieve_file(server_location)
        elif command[:2] == 'df': # TODO
            command, server_location, client_location = map(str, command.split())
            server_location = working_dir + server_location
            # send_file(server_location)
        elif command[:2] == 'ls':
            lst = list(map(str, command.split()))
            path = ''
            if len(lst) > 1:
                path = lst[1]
                if path[0] == '/': path = path[1:]
                if len(path) > 0 and path[-1] == '/': path = path[:-1]
            if concat_path(root, working_dir, path) in file_system:
                send_string_as_kb(str(*file_system[concat_path(root, working_dir, path)]))
            else:
                send_string_as_kb("Directory " + concat_path(working_dir, path) + ' does not exists')
        elif command[:6] == 'mkdir ' or command[:6] == 'rmdir ':
            lst = list(map(str, command.split()))
            path = ''
            if len(lst) == 1:
                send_string_as_kb("Wrong format: " + command)
                continue

            if lst[1][-1] == '/': lst[1] = lst[1][:-1]

            if lst[1].rfind('/') != -1:
                path = lst[1][:lst[1].rfind('/')]
            dir_name = lst[1][lst[1].rfind('/') + 1:]

            if command[:6] == 'mkdir ' and concat_path(root, working_dir) in file_system:
                result = send_command_to_servers(command[:6] + concat_path(root, working_dir, path) + '/' + dir_name)
                if result == "":
                    file_system[concat_path(root, working_dir, path)].append(dir_name)
                    file_system[concat_path(root, working_dir, path) + '/' + dir_name] = []
                    send_string_as_kb("")
                else:
                    send_string_as_kb(result)
            elif command[:6] == 'rmdir ' and concat_path(root, working_dir) in file_system: # TODO add recursive deletion support?
                result = send_command_to_servers(command[:6] + concat_path(root, working_dir, path) + '/' + dir_name)
                if result == "":
                    path = lst[1]
                    file_system[concat_path(root, working_dir, path)].pop(dir_name)
                else:
                    send_string_as_kb(result)
            else:
                send_string_as_kb("Directory " + concat_path(working_dir, path) + ' does not exists')
        elif command[:6] == 'touch ' or command[:3] == 'rm ':
            lst = list(map(str, command.split()))
            command = lst[0]
            for i in range(1, len(lst)):
                if lst[i][0].isalpha() or lst[i][0] == '_':
                    command += ' ' + concat_path(root, working_dir) + '/' + lst[i]

            result = send_command_to_servers(command)
            send_string_as_kb(result)
        elif command[:3] == 'cd ':
            lst = list(map(str, command.split()))

            if lst[1][0] == '/': lst[1] = lst[1][1:]
            if lst[1][-1] == '/': lst[1] = lst[1][:-1]

            if len(lst) > 2:
                send_string_as_kb("Syntax error in command: " + command)
            elif lst[1] == '..':
                if working_dir.rfind('/') != -1:
                    working_dir = working_dir[:working_dir.rfind('/')]
                send_string_as_kb("ok")
            elif concat_path(root, working_dir) + '/' + lst[1] not in file_system:
                send_string_as_kb("Directory " + working_dir + '/' + lst[1] + " does not exists")
            else:
                working_dir += '/' + lst[1]
                send_string_as_kb("ok")
        elif command[:3] == 'mv ' or command[:3] == 'cp ':
            lst = list(map(str, command.split()))
            command = lst[0]
            for i in range(1, len(lst)):
                if lst[i][0].isalpha() or lst[i][0] == '_':
                    command += ' ' + concat_path(root, working_dir) + '/' + lst[i]
            result = send_command_to_servers(command)
            if result == "":
                path_1, path_2 = '', ''
                file_name_1 = lst[1]
                file_name_2 = lst[2]
                if lst[1].rfind('/') != -1:
                    path_1, file_name_1 = lst[1][:lst[1].rfind('/')], lst[1][lst[1].rfind('/') + 1:]

                if lst[2].rfind('/') != -1:
                    path_2, file_name_2 = lst[2][:lst[2].rfind('/')], lst[2][lst[2].rfind('/') + 1:]

                if command == 'mv':
                    file_system[path_1].remove(file_name_1)

                file_system[path_2].append(file_name_2)
                send_string_as_kb("")
            else:
                send_string_as_kb(result)
        else:
            lst = list(map(str, command.split()))
            command = lst[0]
            for i in range(1, len(lst)):
                if lst[i][0].isalpha() or lst[i][0] == '_':
                    command += ' ' + concat_path(root, working_dir) + '/' + lst[i]
            result = send_command_to_servers(command)
            send_string_as_kb(result)