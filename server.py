import socket
import select

HEADER_LENGTH = 10

IP = "127.0.0.1"
PORT = 1234

ids = {}
users = {}
# modelo de usuario
# users[aaaaaa] = {
#     'name': 'joao da silva',
#     'nick': 'jhon',
#     'sala': [],
#     'socket': aaaaa
# }

channels = {
    'Conversa':{
        'name': 'Conversa',
        'users': []
    },
    'Trabalho': {
        'name': 'Trabalho',
        'users': []
    }
}

def join(sala, user):
    conected_users = channels[sala]['users']
    current_user = users[user]

    if current_user in conected_users:
        print('User already connected!')
        return 0

    conected_users.append(current_user)

    # current_user['sala'].append(sala)

def quit(user):
    current_user = users[user]
    current_channel = channels[current_user['sala']]

    current_channel['users'].remove(current_user)
    current_user['sala'].remove(current_channel)




# Create a socket
# socket.AF_INET - address family, IPv4, some otehr possible are AF_INET6, AF_BLUETOOTH, AF_UNIX
# socket.SOCK_STREAM - TCP, conection-based, socket.SOCK_DGRAM - UDP, connectionless, datagrams, socket.SOCK_RAW - raw IP packets
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# SO_ - socket option
# SOL_ - socket option level
# Sets REUSEADDR (as a socket option) to 1 on socket
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Bind, so server informs operating system that it's going to use given IP and port
# For a server using 0.0.0.0 means to listen on all available interfaces, useful to connect locally to 127.0.0.1 and remotely to LAN interface IP
server_socket.bind((IP, PORT))

# This makes server listen to new connections
server_socket.listen()

# List of sockets for select.select()
sockets_list = [server_socket]

# List of connected clients - socket as a key, user header and name as data
clients = {}

print(f'Listening for connections on {IP}:{PORT}...')

# Handles message receiving
def receive_message(client_socket):

    try:

        message_header = client_socket.recv(HEADER_LENGTH)

        if not len(message_header):
            return False

        message_length = int(message_header.decode('utf-8').strip())

        return {'header': message_header, 'data': client_socket.recv(message_length)}

    except:
        return False

while True:

    read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)

    for notified_socket in read_sockets:

        if notified_socket == server_socket:

            client_socket, client_address = server_socket.accept()

            user = receive_message(client_socket)

            if user is False:
                continue

            sockets_list.append(client_socket)

            clients[client_socket] = user

            print('Accepted new connection from {}:{}, username: {}'.format(*client_address, user['data'].decode('utf-8')))
            users[user['data'].decode('utf-8')] = user['data'].decode('utf-8')
            ids[user['data'].decode('utf-8')] = client_socket


        else:

            # Receive message
            message = receive_message(notified_socket)

            # If False, client disconnected, cleanup
            if message is False:
                print('Closed connection from: {}'.format(clients[notified_socket]['data'].decode('utf-8')))

                # Remove from list for socket.socket()
                sockets_list.remove(notified_socket)

                # Remove from our list of users
                del clients[notified_socket]

                continue

            # Get user by notified socket, so we will know who sent the message
            user = clients[notified_socket]
            if  'NICK' in message["data"].decode("utf-8"):
                if users.get(message["data"].decode("utf-8")[5:]) is None :
                    users[user["data"].decode("utf-8")] = message["data"].decode("utf-8")[5:]
                    print(users)
                else :
                    print('Error canot user that username')

            if  'PRIVMSG' in message["data"].decode("utf-8"):
                msg = message["data"].decode("utf-8")[8:]
                msg = msg.split()
                alvo = msg[0]
                mensagem = msg[1]
                idDoAlvo = list(users.keys())[list(users.values()).index(alvo)]
                print(f'Received private message from {users[user["data"].decode("utf-8")]}: {mensagem} para o usuario {idDoAlvo}')
                mensagem = mensagem.encode("utf-8")
                # Iterate over connected clients and broadcast message
                for client_socket in clients:

                    # But don't sent it to sender
                    if client_socket == ids[idDoAlvo]:
                        print(f"{len(mensagem):<{HEADER_LENGTH}}".encode('utf-8'))
                        client_socket.send(user['header'] + users[user["data"].decode("utf-8")].encode("utf-8") + f"{len(mensagem):<{HEADER_LENGTH}}".encode('utf-8') + mensagem)

            else :
                # print(ids)
                print(f'Received message from {users[user["data"].decode("utf-8")]}: {message["data"].decode("utf-8")}')

                # Iterate over connected clients and broadcast message
                for client_socket in clients:

                    # But don't sent it to sender
                    if client_socket != notified_socket:

                        client_socket.send(user['header'] + users[user["data"].decode("utf-8")].encode("utf-8") + message['header'] + message['data'])

    # It's not really necessary to have this, but will handle some socket exceptions just in case
    for notified_socket in exception_sockets:

        # Remove from list for socket.socket()
        sockets_list.remove(notified_socket)

        # Remove from our list of users
        del clients[notified_socket]