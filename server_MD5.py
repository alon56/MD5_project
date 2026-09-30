import socket
import threading
import logging


class client:
    def __init__(self,start: int, finish: int , client_socket: socket, client_address: tuple):
        self.start = start
        self.finish = finish
        self.socket =client_socket
        self.addr = client_address
        

#constant
HOST_IP = "127.0.0.1"
PORT = 6741
QUEUE_LINE = 5


def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind((HOST_IP, PORT))
        server_socket.listen(QUEUE_LINE)
        I=0

        while True:
            client_socket, client_address = server_socket.accept()
            client_thread =threading.Thread(target=handle_client(),args=(client(I, I + 1000, client_socket, client_address)))
            client_thread.start()

    except socket.error as msg:
        logging.warning(f"Connection failed, received socket error {msg}")

    finally:
        server_socket.close()


def handle_client(client: client):
    pass 


def main():
    start_server()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format=('%(asctime)s - %(levelname)s - %(message)s'),
        handlers=[
            logging.FileHandler("server_log_MD5.file")
        ]
    ) 
    main()
