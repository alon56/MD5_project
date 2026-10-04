import socket
import logging

from protocol import Protocol, GET, WORK, FOUND, DONE
from brute_force import BruteForce


# constants
HOST_IP = "127.0.0.1"
PORT = 6741


class Client:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.protocol = Protocol(self.socket)

    def run(self):
        try:
            self.socket.connect((self.host, self.port))
            logging.info(f"connected to server {self.host}:{self.port}")

            while True:
                # ask the server for a range
                self.protocol.send_list([GET])
                response = self.protocol.recv_list()
                command = response[0]

                if command == DONE:
                    logging.info("server said DONE, stopping")
                    break

                if command == WORK:
                    start = int(response[1])
                    end = int(response[2])
                    target_hash = response[3]
                    length = int(response[4])

                    brute_force = BruteForce(length, target_hash)
                    password = brute_force.search_range(start, end)

                    if password:
                        self.protocol.send_list([FOUND, password])
                        logging.info(f"found the password: {password}")
                        self.protocol.recv_list()  # wait for the server's DONE
                        break
                    # not found in this range -> loop and ask for the next one

        except (ConnectionError, socket.error) as err:
            logging.warning(f"connection error: {err}")
        except Exception as err:
            # never let the client crash with a traceback
            logging.warning(f"unexpected error: {err}")
        finally:
            try:
                self.socket.close()
            except socket.error:
                pass


def main():
    try:
        client = Client(HOST_IP, PORT)
        client.run()
    except (EOFError, KeyboardInterrupt):
        logging.info("client stopped by user")
    except Exception as err:
        logging.warning(f"client could not run: {err}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format=('%(asctime)s - %(levelname)s - %(message)s'),
        handlers=[
            logging.FileHandler("client_log_MD5.file"),
            logging.StreamHandler()
        ]
    )
    main()
