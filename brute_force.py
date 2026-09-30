import hashlib


class brute_force:
    def __init__(self, length: int, target_hash: str):
        self.length = length
        self.target_hash = target_hash


    def doit(self, start: int, finish: int):
        for attempt in range(start, finish+1):
            attempt=str(attempt)
            attempt=attempt.zfill(self.length)
            password_try=hashlib.md5(attempt.encode('utf-8')).hexdigest().upper()
            if self.target_hash == password_try:
                return attempt
        return ""

if __name__ == '__main__':
    bf = brute_force(5, hashlib.md5('00010'.encode('utf-8')).hexdigest().upper())
    print(bf.doit(0, 100))