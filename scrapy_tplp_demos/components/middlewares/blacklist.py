import re
import time


class WaitListChecker(object):
    wait_list = [
        r'<h2 class="h2" id="[^><]*?challenge-running">\s*Checking if the site connection is secure\s*</h2>',
        r'<h1><span data-translate="checking_browser">Checking your browser before accessing</span>',
        r'<p data-translate="please_wait" id="cf-spinner-please-wait">Please stand by, while we are checking your browser...</p>'
    ]

    @staticmethod
    def judgement(source):
        for wait in WaitListChecker.wait_list:
            if re.search(wait, source, re.I) is not None:
                time.sleep(6)
                return


class RetryBanListChecker(object):
    ban_list = [
        r'<title>禁止访问 \| 磐云</title>',
    ]

    @staticmethod
    def judgement(source):
        for ban in RetryBanListChecker.ban_list:
            if re.search(ban, source, re.I) is not None:
                return True
        return False
