"""
Author: Alon Fried

Program name: Protocol

Description: Wraps a socket so every message is prefixed with its length
(zero-padded to a fixed number of digits). This solves the TCP stream
problem where one recv can return half a message, or one message plus
part of the next one.

Date: 04/10/26
"""

import socket


# command names - kept here so the client and the server can't spell them differently
GET = "GET"
WORK = "WORK"
FOUND = "FOUND"
DONE = "DONE"


class Protocol:
    def __init__(self, prot_socket: socket.socket, zfill: int = 4, list_delimiter: str = ','):
        self.prot_socket = prot_socket
        self.zfill = zfill
        self.list_delimiter = list_delimiter

    def send(self, data: bytes):
        length = str(len(data))
        if len(length) > self.zfill:
            raise ValueError(f"cannot handle data of size '{length}', max zfill is {self.zfill} digits")

        self.prot_socket.sendall(length.zfill(self.zfill).encode())
        self.prot_socket.sendall(data)

    def _recv_exact(self, amount: int) -> bytes:
        """Keep reading until exactly `amount` bytes arrive, or the peer closes."""
        buffer = b''
        while len(buffer) < amount:
            chunk = self.prot_socket.recv(amount - len(buffer))
            if chunk == b'':
                raise ConnectionError("socket closed by the other side")
            buffer += chunk
        return buffer

    def recv(self) -> bytes:
        length = int(self._recv_exact(self.zfill).decode())
        return self._recv_exact(length)

    def send_str(self, msg: str):
        self.send(msg.encode())

    def recv_str(self) -> str:
        return self.recv().decode()

    def send_list(self, arr: list[str]):
        self.send_str(self.list_delimiter.join(arr))

    def recv_list(self) -> list[str]:
        return self.recv_str().split(self.list_delimiter)
