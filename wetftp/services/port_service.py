import select

from wetftp.config import cfg


def port_service(hacker_data_sock, docker_data_server, output, store):
    docker_data_server.listen(5)
    docker_data_sock, _ = docker_data_server.accept()

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
    docker_data_sock.close()
    docker_data_server.close()
