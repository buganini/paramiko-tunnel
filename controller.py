import sys
import socket
import paramiko
import threading
import queue
import json
import time
import env
import select
import os

PSK_USERNAME = "secret_username"
PSK_PASSWORD = "secret_password"

broker_address = "0.0.0.0" # any interface
broker_port = 0 # any port
broker_host_key = paramiko.RSAKey.generate(1024)
broker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
broker_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

dataq = queue.Queue()

def forwarder(transport, forwarder_socket):
    sock, addr = forwarder_socket.accept()
    channel = transport.open_forwarded_tcpip_channel(addr, forwarder_socket.getsockname())

    print("Accept from", addr, channel)
    while True:
        r, w, x = select.select([sock, channel], [], [])
        if sock in r:
            data = sock.recv(512)
            if len(data) == 0:
                break
            channel.send(data)
        if channel in r:
            data = channel.recv(512)
            if len(data) == 0:
                break
            sock.send(data)
    channel.close()
    sock.close()
    print("Forwarder closed")


#ssh server parameters defined in the class
class Server(paramiko.ServerInterface):
    def __init__(self, transport):
        self.transport = transport

    def check_auth_password(self, username, password):
        if username == PSK_USERNAME and password == PSK_PASSWORD:
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def check_port_forward_request(self, address, port):
        if address:
            return False

        forwarder_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        forwarder_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        forwarder_socket.bind(('127.0.0.1', 0))
        forwarder_socket.listen(100)

        thr = threading.Thread(
            target=forwarder, args=(self.transport, forwarder_socket)
        )
        thr.start()
        port = forwarder_socket.getsockname()[1]
        print(f"Start forwarder on port {port}")

        dataq.put(port)

        return port

#ssh client handler
def client_handler(client_socket):
    #bind client socket to ssh server session and add rsa key
    ssh_session = paramiko.Transport(client_socket)
    ssh_session.add_server_key(broker_host_key)
    server = Server(ssh_session)

    #start the ssh server and negotiate ssh params
    try:
        ssh_session.start_server(server=server)
    except paramiko.SSHException as err:
        print("[!] SSH Parameters Negotiation Failed")

    port = dataq.get()
    print(f"[*] SSH Tunnel Port {port}")

    cmd = f"ssh -o StrictHostKeyChecking=no localhost -p {port}"
    print(cmd)
    os.system(cmd)

    try:
        ssh_session.close()
    except:
        print("[!] Error closing SSH session")
    print("[*] SSH session closed")

#ssh server bind and listen
try:
    broker_socket.bind((broker_address, broker_port))
except:
    print(f"[!] Bind Error for SSH Server using {broker_address}:{broker_port}")
    sys.exit(1)

print(f"[*] Bind Success for SSH Server using {broker_address}:{broker_socket.getsockname()[1]}")
broker_socket.listen()
print("[*] Listening")

#Keep ssh server active and accept incoming tcp connections
client_socket, addr = broker_socket.accept()
print(f"[*] Incoming Connection from {addr[0]}:{addr[1]}")
client_handler(client_socket)
