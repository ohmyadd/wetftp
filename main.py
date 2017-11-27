from wetftp import config
from wetftp.server import tcp_server


# TODO: ssl support
# TODO: output subsystem

address = config.cfg.get("wetftp", "wetftp_addr")
port = config.cfg.getint("wetftp", "wetftp_port")


if __name__ == '__main__':
    tServer = tcp_server.tcp_server((address, port), tcp_server.tcp_handler)
    tServer.serve_forever()
