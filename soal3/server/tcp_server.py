import re
import socket
import logging
import json
import os
import ssl
import threading
from time import sleep

# ======== Serialisasi JSON menjadi data ========
def serialize_from_json(filepath):
    file = open(filepath, 'r')
    result = json.load(file)
    return result

# ======== Serialisasi data menjadi JSON ========
def serialize_to_json(data_to_serialize):
    serialized = json.dumps(data_to_serialize)
    logging.warning("Serialized Data")
    logging.warning(serialized)
    return serialized

# ======== Versi Program ========
def versi():
    return "versi 0.0.1"

# ======== Set alldata dari JSON ========
alldata = dict()
alldata = serialize_from_json('./player.json')

# ======== Server Thread Lists ========
thread_list = []

# Format Request
# NAMACOMMAND <spasi> PARAMETER
def proses_request(request_string):
    # ======== Assign current thread name to thread_name ========
    thread_name = threading.current_thread().getName()
    # Pisahkan antar command dan parameter
    cmd_string = request_string.split(" ")
    # Set default result = None
    result = None
    try:
        command = cmd_string[0].strip()
        if (command == 'getdatapemain'):
            # getdatapemain <spasi> parameter1
            # parameter1 harus berupa nomor pemain
            logging.warning(f"[{thread_name}] Getdata")
            nomorpemain = cmd_string[1].strip()
            try:
                logging.warning(f"[{thread_name}] Data {nomorpemain} ketemu")
                result = alldata[nomorpemain]
            except:
                result = None
        elif (command == 'versi'):
            result = versi()
    except:
        result = None
    return result

def server_instance(connection, client_address, is_secure = False, socket_context = None):
    # ======== Assign current thread name to thread_name ========
    thread_name = threading.current_thread().getName()
    # ======== Receive the data in small chunks and retransmit it ========
    try:
        if is_secure == True:
            connection = socket_context.wrap_socket(connection, server_side=True)
        else:
            connection = connection

        selesai = False
        data_received = "" # String
        while True:
            data = connection.recv(32)
            # sleep(1)
            logging.warning(f"[{thread_name}] Received {data}")
            if data:
                data_received += data.decode()
                if "\r\n\r\n" in data_received:
                    selesai = True

                if (selesai == True):
                    hasil = proses_request(data_received)
                    # logging.warning(f"Hasil proses: {hasil}")

                    hasil = serialize_to_json(hasil)
                    hasil += "\r\n\r\n"
                    connection.sendall(hasil.encode())
                    selesai = False
                    data_received = ""  # String
                    break
            else:
                logging.warning(f"[{thread_name}] No more data from {client_address}")
                connection.close()
                break

        logging.warning(f"[{thread_name}] No more data from {client_address}")
        connection.close()
    # Clean up the connection
    except ssl.SSLError as error_ssl:
        logging.warning(f"SSL error: {str(error_ssl)}")

def run_server(server_address, is_secure = False):
    socket_context = None
    if is_secure == True:
        cert_location = os.getcwd() + '/certs/'
        socket_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        socket_context.load_cert_chain(
            certfile = cert_location + 'domain.crt',
            keyfile = cert_location + 'domain.key'
        )

    # ======== Initialisation Socket ========
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # ======== Bind the socket to the port ========
    logging.warning(f"Starting up on {server_address}")
    sock.bind(server_address)

    # ======== Listen for incoming connections ========
    sock.listen(1000) 

    while True:
        # ======== Wait for a connection ========
        logging.warning("Waiting for a connection")
        connection, client_address = sock.accept()
        logging.warning(f"Incoming connection from {client_address}")

        t = threading.Thread(target = server_instance, args = (connection, client_address, is_secure, socket_context))
        t.start()
        thread_list.append(t)

if __name__=='__main__':
    try:
        run_server(('0.0.0.0', 12000), is_secure = True)
    except KeyboardInterrupt:
        logging.warning("Control-C: Program berhenti")
        exit(0)
    finally:
        for t in thread_list:
            t.join()
        logging.warning("Selesai")
