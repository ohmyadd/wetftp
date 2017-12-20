import time
import select
from OpenSSL import SSL as ssl

from wetftp.config import cfg


def pasv_service(hacker_data_server, docker_data_sock, output, store, secure):
    hacker_data_sock, _ = hacker_data_server.accept()
    print ('accept')
    if None not in secure[:2]:
        server_context, client_context, server_session, client_session = secure
        docker_data_sock = ssl.Connection(client_context, docker_data_sock)
        if client_session:
            docker_data_sock.set_session(client_session)
        docker_data_sock.set_connect_state()
        docker_data_sock.do_handshake()

        hacker_data_sock = ssl.Connection(server_context, hacker_data_sock)
        hacker_data_sock.set_accept_state()
        hacker_data_sock.do_handshake()

    while 1:
        r, w, x = select.select([hacker_data_sock, docker_data_sock], [], [])
        if hacker_data_sock in r:
            try:
                text = hacker_data_sock.recv(1024)
            except:
                hacker_data_sock.shutdown()
                docker_data_sock.shutdown()
                break
            print('hacker', text)

            if not text:
                break
            if store[0]:
                output.o('wetftp', 'file', text)
            docker_data_sock.sendall(text)

        if docker_data_sock in r:
            try:
                text = docker_data_sock.recv(1024)
            except:
                docker_data_sock.shutdown()
                hacker_data_sock.shutdown()
                break
            print('docker', text)
            if not text:
                break
            hacker_data_sock.sendall(text)

    if None not in secure[:2]:
        while hacker_data_sock.shutdown() and docker_data_sock.shutdown():
            time.sleep(0.1)

    hacker_data_sock.close()
    hacker_data_server.close()
    docker_data_sock.close()
