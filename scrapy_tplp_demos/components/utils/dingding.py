import base64
import hashlib
import hmac
import time
import urllib.parse

import requests


class DingDingRobot:

    def __init__(self, web_hook, secret):
        self.web_hook = web_hook
        self.secret = secret

    @classmethod
    def _init_robot(cls, web_hook, secret):
        return cls(web_hook, secret)

    def send_msg(self, msg, at_mobiles, is_at_all=False):
        headers = {
            'Content-Type': 'application/json'
        }
        s, t = self._get_sign()
        params = {
            'sign': s,
            'timestamp': t
        }
        requests.post(url=self.web_hook, params=params, json=self._build_msg(msg, at_mobiles, is_at_all),
                      headers=headers)

    def _get_sign(self):
        timestamp = str(round(time.time() * 1000))
        secret_enc = self.secret.encode('utf-8')
        string_to_sign = '{}\n{}'.format(timestamp, self.secret)
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        return sign, timestamp

    @staticmethod
    def _build_msg(text, at_mobiles, is_at_all):
        msg = {
            "at": {
                "atMobiles": at_mobiles,
                "isAtAll": is_at_all
            },
            "text": {
                "content": text
            },
            "msgtype": "text"
        }
        return msg
