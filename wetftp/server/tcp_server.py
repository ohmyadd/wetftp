import socket

from wetftp.config import cfg
from wetftp.server import SocketServer, ftp_server


class tcp_server(SocketServer.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, sock, handler):
        super(tcp_server, self).__init__(sock, handler)
        self.cfg = cfg


class tcp_handler(SocketServer.BaseRequestHandler):
    def handle(self):
        hacker_sock = self.request
        docker_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        docker_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        sock = (cfg.get('wetftp', 'docker_addr'), cfg.getint('wetftp', 'docker_port'))
        docker_sock.connect(sock)

        ftp = ftp_server.ftp_server(hacker_sock, docker_sock)
        try:
            ftp.run()
        except Exception, e:
            print 'tcp server ftp run exception: ', e
        finally:
            ftp.stop()
