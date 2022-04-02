from datetime import datetime
import os
import re
import socket
import json
import logging

import concurrent.futures
import ssl
from threading import current_thread
import random

SERVER_ADDRESS = ('172.16.16.102', 12000)

def make_socket(destination_address = 'localhost', port = 12000):
    try:
        thread_name = re.findall("(?<=ThreadPoolExecutor-).*", current_thread().getName())[0]

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (destination_address, port)

        logging.warning(f"[THREAD {thread_name}] Connecting to {server_address}")
        sock.connect(server_address)

        return sock
    except Exception as ee:
        logging.warning(f"Error {str(ee)}")

def make_secure_socket(destination_address = 'localhost',port = 12000):
    try:
        thread_name = re.findall("(?<=ThreadPoolExecutor-).*", current_thread().getName())[0]

        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.verify_mode=ssl.CERT_OPTIONAL
        context.load_verify_locations(os.getcwd() + '/domain.crt')

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (destination_address, port)
        logging.warning(f"[THREAD {thread_name}] Connecting to {server_address}")
        
        sock.connect(server_address)
        secure_socket = context.wrap_socket(sock,server_hostname = destination_address)
        logging.warning(f"[THREAD {thread_name}] {secure_socket.getpeercert()}")
        return secure_socket
    except Exception as ee:
        logging.warning(f"error {str(ee)}")

# ======== Deserialisasi data JSON menjadi dictionary ========
def deserialize_from_json(data_to_deserialize):
    thread_name = re.findall("(?<=ThreadPoolExecutor-).*", current_thread().getName())[0]

    logging.warning(f"[THREAD {thread_name}] Deserialisasi {data_to_deserialize.strip()}")
    return json.loads(data_to_deserialize)
    
# ======== Send Command to server ========
def send_command(command_str, is_secure = False):
    address_server = SERVER_ADDRESS[0]
    port_server = SERVER_ADDRESS[1]

    # ======== Inisialisasi socket untuk connect ke server ========
    if is_secure == True:
        sock = make_secure_socket(address_server, port_server)
    else:
        sock = make_socket(address_server, port_server)

    try:
        thread_name = re.findall("(?<=ThreadPoolExecutor-).*", current_thread().getName())[0]
        
        logging.warning(f"[THREAD {thread_name}] Sending message ")
        sock.sendall(command_str.encode())
        # Look for the response, waiting until socket is done (no more data)
        data_received = "" # Empty string
        while True:
            # Socket does not receive all data at once, data comes in part, need to be concatenated at the end of process
            data = sock.recv(16)
            if data:
                # Data is not empty, concat with previous content
                data_received += data.decode()
                if "\r\n\r\n" in data_received:
                    break
            else:
                # No more data, stop the process by break
                break
        # At this point, data_received (string) will contain all data coming from the socket
        # To be able to use the data_received as a dict, need to load it using json.loads()
        logging.warning(f"[THREAD {thread_name}] Data received from server")
        hasil = deserialize_from_json(data_received)
        return hasil
    except Exception as ee:
        logging.warning(f"Error during data receiving {str(ee)}")
        return False


def getdatapemain(nomor = 0, is_secure = False):
    cmd = f"getdatapemain {nomor}\r\n\r\n"
    hasil = send_command(cmd, is_secure)
    return hasil

def lihatversi(is_secure = False):
    cmd = f"versi \r\n\r\n"
    hasil = send_command(cmd, is_secure)
    return hasil

if __name__=='__main__':
    thread_count = dict()
    thread_count[1] = 1
    thread_count[2] = 5
    thread_count[3] = 10
    thread_count[4] = 20

    thread_result = dict()
    for key in thread_count:
        logging.warning(f"============ {thread_count[key]} Thread ============")
        texec = dict()
        status_task = dict()
        task = concurrent.futures.ThreadPoolExecutor(max_workers = thread_count[key])

        # ======== Melakukan 30 requests ========
        start_time = datetime.now()
        for i in range(0, 30):
            nomor_pemain = random.randint(1, 20)
            texec[i+1] = task.submit(getdatapemain, nomor_pemain, True)
        end_time = datetime.now()

        # ======== Cek status 30 responses ========
        for i in range(0, 30):
            if(texec[i+1].result() != None):
                status_task[i+1] = texec[i+1].result()

        thread_result[key] = [end_time - start_time, len(status_task)]

    logging.warning("\r\n")
    for key in thread_result:
        logging.warning(f"30 Request client menggunakan {thread_count[key]} thread:")
        logging.warning(f"   > Response diterima: {thread_result[key][1]}")
        logging.warning(f"   > Waktu untuk menyelesaikan: {thread_result[key][0]}\r\n")



