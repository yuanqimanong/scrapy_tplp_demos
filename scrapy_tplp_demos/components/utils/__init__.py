import base64
import os
import re


class CommonUtil:
    retry_times = 0

    @staticmethod
    def convert_headers(data):
        new_data = {}
        for k, v in data.items():
            new_data.update({k.decode(encoding="utf-8"): v[0].decode(encoding="utf-8")})
        return new_data

    @staticmethod
    def convert_cookies(data):
        return dict({i.split('=', 1)[0].strip(): i.split('=', 1)[1].strip() for i in
                     data.decode(encoding="utf-8").split(";")})

    @staticmethod
    def get_screenshot(response):
        return response.meta.get('SeleniumCrawl').get('screenshot_result')

    @staticmethod
    def save_screenshot(response, dir, filename):
        pic = response.meta.get('SeleniumCrawl').get('screenshot_result')
        if pic:
            CommonUtil.mk_dir(dir)
            img = base64.b64decode(pic)
            file = open(F'{dir}/{filename}', "wb")
            file.write(img)
            file.close()

    @staticmethod
    def mk_dir(path):
        dirname = os.path.dirname(path)
        if dirname and not os.path.exists(dirname):
            os.makedirs(dirname)

    @staticmethod
    def turn_page(start_urls):
        urls = []
        for url in start_urls:
            if '【' and '】' in url:
                result = re.match(r'^(.*)【([^】]+?)】(.*)$', url)
                bgn = result.group(1)
                turn_page_expression = result.group(2)
                end = result.group(3)
                if '::' in turn_page_expression:
                    _result = re.match(r'^(\d+)-(\d+)::(\d+)', turn_page_expression)
                    _a = int(_result.group(1))
                    _b = int(_result.group(2)) - 1
                    _i = int(_result.group(3))

                    for i in range(_b):
                        if 0 == _a or 1 == _a:
                            urls.append(F'{bgn}{str(_a)}{end}')
                            _a = 2
                        else:
                            _x = _a * _i
                            _a = _x
                            urls.append(F'{bgn}{str(_x)}{end}')
                elif ':' in turn_page_expression:
                    _result = re.match(r'^(\d+)-(\d+):(\d+)', turn_page_expression)
                    _a = int(_result.group(1))
                    _b = int(_result.group(2)) - 1
                    _i = int(_result.group(3))
                    urls.append(F'{bgn}{str(_a)}{end}')
                    for i in range(_b):
                        _x = _a + _i
                        _a = _x
                        urls.append(F'{bgn}{str(_x)}{end}')
                else:
                    _result = re.match(r'^(\d+)-(\d+)', turn_page_expression)
                    _a = int(_result.group(1))
                    _b = int(_result.group(2)) - 1
                    urls.append(F'{bgn}{str(_a)}{end}')
                    for i in range(_b):
                        _x = _a + 1
                        _a = _x
                        urls.append(F'{bgn}{str(_x)}{end}')

            else:
                urls.append(url)

        return urls

    @staticmethod
    def retry_method(times):
        if CommonUtil.retry_times < times:
            CommonUtil.retry_times += 1
            return True
        return False

    @staticmethod
    def retry_success():
        CommonUtil.retry_times = 0
