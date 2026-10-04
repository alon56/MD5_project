import socket
import threading
import logging
import hashlib

from protocol import Protocol, GET, WORK, FOUND, DONE
from brute_force import ALPHABET


# constants
HOST_IP = "127.0.0.1"
PORT = 6741
QUEUE_LINE = 5
CHUNK_SIZE = 1000000
ACCEPT_TIMEOUT = 1.0  # how often the accept loop wakes up to re-check if we are done


class WorkManager:
    """Shared between all client threads. Hands out ranges that never
    overlap and never skip, and remembers the password once it is found.

    The length and the maximum come from the password the user enters,
    so the server scales to any length without changing the code."""

    def __init__(self, target_hash: str, length: int, chunk_size: int, base: int):
        self.target_hash = target_hash
        self.length = length
        self.chunk_size = chunk_size
        self.maximum = base ** length  # how many options a password of this length has
        self.next_start = 0
        self.password = None
        self.lock = threading.Lock()

    def get_next_range(self):
        """Return (start, end) with end exclusive, or None when the
        password is already found or there is no work left."""
        with self.lock:
            if self.password is not None or self.next_start >= self.maximum:
                return None
            start = self.next_start
            end = min(start + self.chunk_size, self.maximum)
            self.next_start = end
            return start, end

    def report_found(self, password: str):
        with self.lock:
            self.password = password

    def is_done(self) -> bool:
        with self.lock:
            return self.password is not None


class ClientHandler(threading.Thread):
    """One thread per connected client. Answers its requests until the
    client is told to stop (DONE) or it disconnects."""

    def __init__(self, protocol: Protocol, address: tuple, manager: WorkManager):
        super().__init__()
        self.protocol = protocol
        self.address = address
        self.manager = manager

    def run(self):
        logging.info(f"client connected: {self.address}")
        try:
            while True:
                request = self.protocol.recv_list()
                command = request[0]

                if command == GET:
                    work = self.manager.get_next_range()
                    if work is None:
                        # password found by someone, or no ranges left -> tell this client to finish
                        self.protocol.send_list([DONE])
                        break
                    start, end = work
                    self.protocol.send_list([WORK, str(start), str(end),
                                             self.manager.target_hash,
                                             str(self.manager.length)])

                elif command == FOUND:
                    password = request[1]
                    self.manager.report_found(password)
                    logging.info(f"password found: {password} (by {self.address})")
                    self.protocol.send_list([DONE])
                    break

        except (ConnectionError, socket.error) as err:
            logging.warning(f"client {self.address} ended: {err}")
        except Exception as err:
            # never let a handler thread crash with a traceback
            logging.warning(f"client {self.address} unexpected error: {err}")
        finally:
            try:
                self.protocol.prot_socket.close()
            except socket.error:
                pass
            logging.info(f"client closed: {self.address}")


class Server:
    def __init__(self, host: str, port: int, manager: WorkManager):
        self.host = host
        self.port = port
        self.manager = manager
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self):
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(QUEUE_LINE)
            self.server_socket.settimeout(ACCEPT_TIMEOUT)
            logging.info(f"server listening on {self.host}:{self.port}")

            while not self.manager.is_done():
                try:
                    client_socket, address = self.server_socket.accept()
                except socket.timeout:
                    continue  # no client this second -> loop back and re-check is_done()

                client_socket.settimeout(None)  # the handler should block normally on this client
                handler = ClientHandler(Protocol(client_socket), address, self.manager)
                handler.start()

            logging.info(f"server finished, password is: {self.manager.password}")

        except socket.error as msg:
            logging.warning(f"Connection failed, received socket error {msg}")
        except Exception as err:
            logging.warning(f"server unexpected error: {err}")
        finally:
            try:
                self.server_socket.close()
            except socket.error:
                pass


def build_manager_from_input() -> WorkManager:
    """Ask for a password and build the work from it: the length and the
    target hash are both derived from what you type. Keeps asking until the
    input is digits only, so a typo can never crash the server."""
    while True:
        password = input("which password do you want to crack? ").strip()
        if password.isascii() and password.isdigit():
            break
        print("digits only (0-9), please try again")

    length = len(password)
    target_hash = hashlib.md5(password.encode('utf-8')).hexdigest().upper()
    logging.info(f"cracking length={length}, hash={target_hash}")
    return WorkManager(target_hash, length, CHUNK_SIZE, len(ALPHABET))


def main():
    try:
        manager = build_manager_from_input()
        server = Server(HOST_IP, PORT, manager)
        server.start()
    except (EOFError, KeyboardInterrupt):
        logging.info("server stopped by user")
    except Exception as err:
        logging.warning(f"server could not run: {err}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format=('%(asctime)s - %(levelname)s - %(message)s'),
        handlers=[
            logging.FileHandler("server_log_MD5.file"),
            logging.StreamHandler()
        ]
    )
    main()
