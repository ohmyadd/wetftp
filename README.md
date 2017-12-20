# Wetftp
Wetftp is a high interaction FTP honeypot,designed to log brute force attacks and every action of attacker after login.

## Features
* Use docker to provide a real linux document system.
* Wetftp locate at the middle between ftpd container and attacker.
* Log all of attacker's action.
* Save a copy of files that attacker upload.
* Support ftps(ftp over ssl).
* Support ssl's session reuse.
* Kinds of ways to report to you when wetland is touching by hacker

## Requirements
* A linux system (tested on ubuntu)
* ftpd images in docker (e.g. bogem/ftp)
* python2.7
* pyOpenSSL
* requests

## Setup and Configuration
1. Copy wetftp.cfg.default to wetftp.cfg

2. Generate private key and sign the certificate
  * `mkdir data && cd data`
  * `openssl genrsa -out server.key 2048` 
  * `openssl req -new -key server.key -out server.csr`
  * `openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.crt`

3. Install python requirements
  * `pip install pyOpenSSl requests`

4. Install docker
  * install docker with docs in [www.docker.com](www.docker.com)
  * `docker search ftpd` or `docker search ftp`
  * `docker run -d --name ftpd ftpd_image_name`
  * `docker inspect ftpd`,then replace **docker_addr** in wetftp.cfg with ftpd's ip.
  * some ftpd container maybe need to do something else, please read docs of the image in [hub.docker.com](hub.docker.com)

5. Configure the output plugins in wetftp.cfg
  * enable or disable in [output] section
  * Edit the url of incoming robots when using bearychat
  * Edit user、pwd... when using email
6. Configure ftps in wetftp.cfg if necessary
  * first make sure your ftpd images support ftps, has been configured to work.
  * enable it in [ftps] section.
  * ssl session can be reused between control channel and data channel,so if your ftpd support it, enable reuse in [ftps] seciton.
  * e.g. a configure file of vsftpd, it should enable ftps and reuse

```bash
rsa_cert_file=/var/server.crt
rsa_private_key_file=/var/server.key
ssl_enable=YES
# This determines ssl session reuse or not
require_ssl_reuse=YES
```

## Running
1. Run
  * `nohup python main &`
2. Stop
  * `netstat -autpn | grep 21`
  * `kill pid_number`
3. View logs
  * `cd logs && ls`
