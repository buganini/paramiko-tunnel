#!/usr/bin/env python

import socket
import select
import sys
import threading
import paramiko

PSK_USERNAME = "secret_username"
PSK_PASSWORD = "secret_password"

def reverse_forward_tunnel(broker_host, broker_port, target_host, target_port):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    print("Connecting to ssh host %s:%d ..." % (broker_host, broker_port))
    try:
        client.connect(
            broker_host,
            broker_port,
            username=PSK_USERNAME,
            password=PSK_PASSWORD,
        )
    except Exception as e:
        print("*** Failed to connect to %s:%d: %r" % (broker_host, broker_port, e))
        sys.exit(1)

    print(
        "Now forwarding remote port to %s:%d ..."
        % (target_host, target_port)
    )

    transport = client.get_transport()
    transport.request_port_forward("", 0)
    chan = transport.accept(30)

    if chan:
        sock = socket.socket()
        try:
            sock.connect((target_host, target_port))
        except Exception as e:
            print("Forwarding request to %s:%d failed: %r" % (target_host, target_port, e))
            return

        print(
            "Connected!  Tunnel open %r -> %r -> %r"
            % (chan.origin_addr, chan.getpeername(), (target_host, target_port))
        )
        while True:
            r, w, x = select.select([sock, chan], [], [])
            if sock in r:
                data = sock.recv(512)
                if len(data) == 0:
                    break
                chan.send(data)
            if chan in r:
                data = chan.recv(512)
                if len(data) == 0:
                    break
                sock.send(data)
        chan.close()
    sock.close()
    print("Tunnel closed from %r" % (chan.origin_addr,))
    client.close()


def rforward(broker_host, broker_port, target_host, target_port, daemon=False):
    thr = threading.Thread(
        target=reverse_forward_tunnel, args=(broker_host, broker_port, target_host, target_port,),
        daemon=daemon
    )
    thr.start()

if __name__=="__main__":
    broker_host = sys.argv[1]
    broker_port = int(sys.argv[2])
    target_host = sys.argv[3]
    target_port = int(sys.argv[4])
    rforward(broker_host, broker_port, target_host, target_port)