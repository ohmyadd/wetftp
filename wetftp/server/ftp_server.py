import select
import socket
import threading

from wetftp.config import cfg
from wetftp import services
from wetftp.output import output

from OpenSSL import SSL as ssl


class ftp_server(object):
    def __init__(self, hacker_sock, docker_sock):
        self.hacker_sock = hacker_sock
        self.docker_sock = docker_sock

        self.local_ip_with_hacker = hacker_sock.getsockname()[0]
        self.local_ip_with_docker = docker_sock.getsockname()[0]

        self.running = False
        self.output = output(hacker_sock.getpeername()[0])

        self.store = [False]

        self.server_version = ssl.TLSv1_METHOD
        self.client_version = ssl.SSLv23_METHOD
        self.secure = False
        self.server_context = False
        self.client_context = False

    def run(self):
        self.running = True

        while self.running:
            r, w, x = select.select([self.hacker_sock, self.docker_sock], [], [])
            if self.hacker_sock in r:
                try:
                    text = self.hacker_sock.recv(1024)
                except:
                    break
                print('hacker said:', text)
                if not text:
                    break

                self.output.o('wetftp', 'cmd', text.strip())
                if text[:4].upper() in ('STOR', 'STOU', 'APPE'):
                    self.store[0] = [True]

                text = self.check(text)
                if text:
                    self.docker_sock.sendall(text)

            if self.docker_sock in r:
                try:
                    text = self.docker_sock.recv(1024)
                except:
                    break
                print('docker said:', text)
                if not text:
                    break
                if text[:3] == '226':
                    self.store = [False]

                text = self.check(text)
                if text:
                    self.hacker_sock.sendall(text)

    def stop(self):
        self.running = False
        self.hacker_sock.close()
        self.docker_sock.close()

    def check(self, text):
        if text[:4].upper() == b'PORT':
            return self.check_port_request(text)

        elif text[:3] == b'227':
            return self.check_pasv_request(text)

        elif text[:4] == b'AUTH':
            """
            if 'SSL' in text:
                self.server_version = ssl.PROTOCOL_SSLv23
            else:
                self.server_version = ssl.PROTOCOL_TLSv1
            """
            print("check auth")
            return self.check_auth_request(text)

        elif text[:3] == b'234':
            print("check 234")
            return self.check_sslnego_request(text)

        else:
            return text

    def check_auth_request(self, text):
        self.secure = True
        self.server_context = ssl.Context(self.server_version)
        self.server_context.use_certificate_file(cfg.get('ftps', 'cert'))
        self.server_context.use_privatekey_file(cfg.get('ftps', 'key'))
        self.client_context = ssl.Context(self.client_version)
        if cfg.getboolean('ftps', 'reuse'):
            print 'wo set le mode'
            self.server_context.set_session_cache_mode(ssl.SESS_CACHE_SERVER)
            self.client_context.set_session_cache_mode(ssl.SESS_CACHE_CLIENT)
        else:
            self.server_context.set_session_cache_mode(ssl.SESS_CACHE_OFF)
            self.client_context.set_session_cache_mode(ssl.SESS_CACHE_OFF)
        return text

    def check_sslnego_request(self, text):
        self.docker_sock = ssl.Connection(self.client_context,
                                          socket=self.docker_sock)
        self.docker_sock.set_connect_state()
        self.docker_sock.do_handshake()
        print 'docker nego done'

        self.hacker_sock.sendall(text)
        self.hacker_sock = ssl.Connection(self.server_context,
                                          socket=self.hacker_sock)
        self.hacker_sock.set_accept_state()
        self.hacker_sock.do_handshake()
        print('hacker nego done')

        return

    def check_port_request(self, cmd):
        bts = cmd.split()[1].split(',')
        ip = '.'.join(bts[:4])
        if ip != self.hacker_sock.getpeername()[0]:
            return cmd
        port1 = bts[4:]
        port2 = (int(port1[0]) << 8) + int(port1[1])

        new_cmd = 'PORT ' + ','.join(self.local_ip_with_docker.split('.') + port1) + '\r\n'

        hacker_sock = (ip, port2)
        docker_sock = (self.local_ip_with_docker, port2)

        hacker_data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        hacker_data_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        hacker_data_sock.bind((docker_sock[0], cfg.getint('wetftp', 'wetftp_port') - 1))

        docker_data_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        docker_data_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        docker_data_server.bind(docker_sock)
        docker_data_server.listen(5)

        try:
            hacker_data_sock.connect(hacker_sock)
        except Exception as e:
            print(e)
            hacker_data_sock.close()
            return new_cmd

        if self.secure:
            server_context = self.server_context
            client_context = self.client_context
            if cfg.getboolean('ftps', 'reuse'):
                server_session = None
                client_session = self.docker_sock.get_session()
            else:
                server_session = None
                client_session = None
        else:
            server_context = None
            client_context = None
            server_session = None
            client_session = None

        data_threading = threading.Thread(target=services.port_service,
                                          args=(hacker_data_sock,
                                                docker_data_server,
                                                self.output,
                                                self.store,
                                                [server_context,
                                                 client_context,
                                                 server_session,
                                                 client_session]))
        data_threading.setDaemon(True)
        data_threading.start()

        return new_cmd

    def check_pasv_request(self, cmd):
        print("checkin")
        bts = cmd.split()[-1].strip('().').split(',')
        ip = '.'.join(bts[:4])
        port1 = bts[4:]
        port2 = (int(port1[0]) << 8) + int(port1[1])

        new_bts = self.local_ip_with_hacker.split('.') + port1
        new_cmd = '  '.join(cmd.split()[:-1]) + ' (%s)\r\n' % ','.join(new_bts)

        hacker_sock = (self.local_ip_with_hacker, port2)
        docker_sock = (ip, port2)

        docker_data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        docker_data_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            docker_data_sock.connect(docker_sock)
        except Exception as e:
            print('ftp server86', e)
            docker_data_sock.close()
            return new_cmd
        else:
            hacker_data_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # TODO: excepiton
            hacker_data_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            hacker_data_server.bind(hacker_sock)
            hacker_data_server.listen(5)

        if self.secure:
            server_context = self.server_context
            client_context = self.client_context
            if cfg.getboolean('ftps', 'reuse'):
                server_session = None
                client_session = self.docker_sock.get_session()
            else:
                server_session = None
                client_session = None
        else:
            server_context = None
            client_context = None
            server_session = None
            client_session = None

        data_threading = threading.Thread(target=services.pasv_service,
                                          args=(hacker_data_server,
                                                docker_data_sock,
                                                self.output,
                                                self.store,
                                                [server_context,
                                                 client_context,
                                                 server_session,
                                                 client_session]))
        data_threading.setDaemon(True)
        data_threading.start()

        return new_cmd
