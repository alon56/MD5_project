import hashlib
import string


# the characters a password can be made of. the assignment target is a number,
# so the alphabet is the digits 0-9. a password of length N means every option
# from "0...0" to "9...9" (10**N options).
ALPHABET = string.digits


class BruteForce:
    def __init__(self, length: int, target_hash: str, alphabet: str = ALPHABET):
        self.length = length
        self.target_hash = target_hash
        self.alphabet = alphabet
        self.base = len(alphabet)

    def index_to_text(self, index: int) -> str:
        """Turn a number into a fixed-length string over the alphabet,
        like counting in base len(alphabet). index 0 -> all first chars."""
        chars = []
        for _ in range(self.length):
            index, remainder = divmod(index, self.base)
            chars.append(self.alphabet[remainder])
        return ''.join(reversed(chars))

    def search_range(self, start: int, finish: int):
        """Check every option from start up to (but not including) finish.
        finish is exclusive, like Python's range, so server ranges never
        overlap and never skip an option."""
        for index in range(start, finish):
            text = self.index_to_text(index)
            digest = hashlib.md5(text.encode('utf-8')).hexdigest().upper()
            if self.target_hash == digest:
                return text
        return ""


if __name__ == '__main__':
    target = hashlib.md5('042'.encode('utf-8')).hexdigest().upper()
    bf = BruteForce(3, target)
    print(bf.search_range(0, bf.base ** bf.length))
