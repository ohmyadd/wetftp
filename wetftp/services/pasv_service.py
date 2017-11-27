import select

from wetftp.config import cfg


def pasv_service(hacker_data_server, docker_data_sock, output, store):
    hacker_data_sock, _ = hacker_data_server.accept()

    while 1:
        r, w, x = select.select([hacker_data_sock, docker_data_sock], [], [])
        if hacker_data_sock in r:
            text = hacker_data_sock.recv(1024)
            if not text:
                break
            if store[0]:
                output.o('wetftp', 'file', text)
            docker_data_sock.sendall(text)

        if docker_data_sock in r:
            text = docker_data_sock.recv(1024)
            if not text:
                break
            hacker_data_sock.sendall(text)

    hacker_data_sock.close()
    hacker_data_server.close()
    docker_data_sock.close()
