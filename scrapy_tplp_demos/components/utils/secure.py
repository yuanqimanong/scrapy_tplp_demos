from base64 import b64encode, b64decode

from Crypto.Cipher import AES
from Crypto.Hash import MD5, SHA1
from Crypto.Util.Padding import pad, unpad


class SecureUtil:

    @staticmethod
    def md5(text, encoding='UTF-8', length=32):
        h = MD5.new()
        h.update(bytes(text, encoding=encoding))

        if 16 == length:
            return h.hexdigest()[8:-8]
        else:
            return h.hexdigest()

    @staticmethod
    def sha1(text, encoding='UTF-8'):
        h = SHA1.new()
        h.update(bytes(text, encoding=encoding))
        return h.hexdigest()

    @staticmethod
    def aes_cbc_encrypt(text, key, iv):
        cipher = AES.new(key.encode('UTF-8'), AES.MODE_CBC, iv.encode('UTF-8'))
        ct_bytes = cipher.encrypt(pad(text.encode('UTF-8'), AES.block_size))
        return b64encode(ct_bytes).decode('UTF-8')

    @staticmethod
    def aes_cbc_decrypt(text, key, iv):
        cipher = AES.new(key.encode('UTF-8'), AES.MODE_CBC, iv.encode('UTF-8'))
        decrypt_text = unpad(cipher.decrypt(b64decode(text)), AES.block_size)
        return decrypt_text.decode('UTF-8')


class Base64:
    @staticmethod
    def encode(text, encoding='UTF-8'):
        return b64encode(str(text).encode(encoding)).decode()

    @staticmethod
    def decode(text, encoding='UTF-8'):
        try:
            return b64decode(str(text)).decode(encoding)
        except UnicodeDecodeError:
            return b64decode(text)
