import socket
import logging
import json
import os
import ssl

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

# Format Request
# NAMACOMMAND <spasi> PARAMETER
def proses_request(request_string):
    # Pisahkan antar command dan parameter
    cmd_string = request_string.split(" ")
    # Set default result = None
    result = None
    try:
        command = cmd_string[0].strip()
        if (command == 'getdatapemain'):
            # getdatapemain <spasi> parameter1
            # parameter1 harus berupa nomor pemain
            logging.warning("Getdata")
            nomorpemain = cmd_string[1].strip()
            try:
                logging.warning(f"Data {nomorpemain} ketemu")
                result = alldata[nomorpemain]
            except:
                result = None
        elif (command == 'versi'):
            result = versi()
    except:
        result = None
    return result


def run_server(server_address, is_secure = False):
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

        # ======== Receive the data in small chunks and retransmit it ========
        try:
            selesai = False
            data_received = "" # String
            while True:
                data = connection.recv(32)
                logging.warning(f"Received {data}")
                if data:
                    data_received += data.decode()
                    if "\r\n\r\n" in data_received:
                        selesai = True

                    if (selesai == True):
                        hasil = proses_request(data_received)
                        logging.warning(f"Hasil proses: {hasil}")

                        hasil = serialize_to_json(hasil)
                        hasil += "\r\n\r\n"
                        connection.sendall(hasil.encode())
                        selesai = False
                        data_received = ""  # String
                        break
                else:
                   logging.warning(f"No more data from {client_address}")
                   break
        # Clean up the connection
        except ssl.SSLError as error_ssl:
            logging.warning(f"SSL error: {str(error_ssl)}")


if __name__=='__main__':
    try:
        run_server(('0.0.0.0', 12000), is_secure = False)
    except KeyboardInterrupt:
        logging.warning("Control-C: Program berhenti")
        exit(0)
    finally:
        logging.warning("Selesai")
