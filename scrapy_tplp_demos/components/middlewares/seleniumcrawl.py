import copy
import logging
import os
import random
import shutil
import tempfile
import time

import undetected_chromedriver as webdriver
from scrapy import Request, signals
from scrapy.http import HtmlResponse
from scrapy.utils.request import request_httprepr
from selenium.common import WebDriverException, ElementNotInteractableException, TimeoutException
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.remote_connection import LOGGER as webdriver_logger
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from scrapy_tplp_demos.components.middlewares.blacklist import WaitListChecker

logging.getLogger('urllib3').setLevel(logging.WARNING)
webdriver_logger.setLevel(logging.WARNING)
selenium_logger = logging.getLogger(__name__)


class SeleniumRequest(Request):
    def __init__(self, url, delay=1, until=None, script=None, screenshot=None, size=(1366, 768),
                 load_time=28.0, random_ua=False,
                 meta=None,
                 *args,
                 **kwargs):
        self.delay = delay
        self.until = until
        self.script = script
        self.screenshot = screenshot
        self.size = size
        self.load_time = load_time
        self.random_ua = random_ua

        _meta = copy.deepcopy(meta) or {}
        selenium_meta = _meta.get('SeleniumCrawl')
        if selenium_meta is not None:
            self.delay = selenium_meta.get('delay') or delay
            self.until = selenium_meta.get('until') or until
            self.script = selenium_meta.get('script') or script
            self.screenshot = selenium_meta.get('screenshot') or screenshot
            self.size = selenium_meta.get('size') or size
            self.load_time = selenium_meta.get('load_time') or load_time
            self.random_ua = selenium_meta.get('random_ua') or random_ua

        _selenium_meta = _meta.setdefault('SeleniumCrawl', {})
        _selenium_meta['enabled'] = True
        _selenium_meta['delay'] = self.delay
        _selenium_meta['until'] = self.until
        _selenium_meta['script'] = self.script
        _selenium_meta['screenshot'] = self.screenshot
        _selenium_meta['size'] = self.size
        _selenium_meta['load_time'] = self.load_time
        _selenium_meta['random_ua'] = self.random_ua

        super().__init__(url, meta=_meta, *args, **kwargs)


class SeleniumCrawlMiddleware:
    _save_log_list = []

    def _save_log(message):
        SeleniumCrawlMiddleware._save_log_list.append(message)

    def get_headers(self, current_url, log_list):
        request_headers = {}
        response_headers = {}
        for log in log_list:
            if 'Network.requestWillBeSent' == log['method']:
                if current_url == log['params']['request']['url']:
                    request_headers = log['params']['request']['headers']
                    continue

            if 'Network.responseReceived' == log['method']:
                if current_url == log['params']['response']['url']:
                    response_headers = log['params']['response']['headers']

        return request_headers, response_headers

    def __init__(self, settings, stats):
        self.stats = stats
        extension_list = F'{os.path.abspath(r"..")}/components/middlewares/browser_plugins/webrtc-control_0.3.0_0,{os.path.abspath(r"..")}/components/middlewares/browser_plugins/audioContext_fingerprint_defender_0.1.6_0,{os.path.abspath(r"..")}/components/middlewares/browser_plugins/canvas_fingerprint_defender_0.1.9_0,{os.path.abspath(r"..")}/components/middlewares/browser_plugins/font_fingerprint_defender_0.1.3_0,{os.path.abspath(r"..")}/components/middlewares/browser_plugins/webgl_fingerprint_defender_0.1.5_0'

        self.download_delay = settings.getfloat('DOWNLOAD_DELAY')
        ip_proxy_service = settings.getbool('IP_PROXY_SERVICE')
        if ip_proxy_service:
            ip_proxy_list = list(str(x) for x in settings.getlist('IP_PROXY_LIST'))

            # ????????????
            if ip_proxy_service:
                if len(ip_proxy_list) > 0:
                    random_proxy = random.choice(ip_proxy_list)
                    user_password = ['', '']
                    if '@' in random_proxy:
                        tunnel_proxy = random_proxy.split('@')
                        user_password = tunnel_proxy[0].split(':')
                        ipaddress_port = tunnel_proxy[1].split(':')
                    else:
                        ipaddress_port = random_proxy.split(':')
                    # ????????????
                    proxy = (ipaddress_port[0], int(ipaddress_port[1]), user_password[0], user_password[1])
                    self.proxy_extension = ProxyExtension(*proxy)
                    extension_list = F'{self.proxy_extension.directory},{extension_list}'

        # ????????????
        self.selenium_options_geolocation = {
            "latitude": 23.1674,
            "longitude": 120.795,
            "accuracy": 1
        }
        self.selenium_options_timezone = {
            "timezoneId": 'Asia/Taipei'
        }

        # selenium ??????
        selenium_settings = {
            # cache_valid_range 100???
            'selenium_driver_path': ChromeDriverManager(
                path=F'{os.path.abspath(r"..")}/components/selenium_cache/driver',
                cache_valid_range=100).install(),
            'browser_user_data_dir': F'{os.path.abspath(r"..")}/components/selenium_cache/user_data_dir',
            'load_extension': extension_list
        }

        options = ChromeOptions()
        # ???????????????????????????????????????????????????bug
        options.add_argument('--disable-gpu')
        # ??????
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--force-device-scale-factor=1')
        # ?????????????????????
        options.add_argument('--no-first-run --no-service-autorun --password-store=basic')
        # ???????????? ??????WebRTC??????,????????????
        options.add_argument(F"--load-extension={selenium_settings.get('load_extension')}")
        # ??????????????????
        options.set_capability('pageLoadStrategy', 'normal')

        self.driver = webdriver.Chrome(options=options,
                                       user_data_dir=selenium_settings.get(
                                           'browser_user_data_dir'),
                                       driver_executable_path=selenium_settings.get(
                                           'selenium_driver_path'),
                                       enable_cdp_events=True,
                                       suppress_welcome=False)
        self.driver.get('chrome://version/')
        handles = self.driver.window_handles
        if len(handles) > 1:
            self.driver.switch_to.window(handles[1])

        # ???????????????????????????
        self.driver.execute_cdp_cmd("Emulation.setGeolocationOverride", self.selenium_options_geolocation)
        self.driver.execute_cdp_cmd("Emulation.setTimezoneOverride", self.selenium_options_timezone)

        self.driver.add_cdp_listener('Network.requestWillBeSent', SeleniumCrawlMiddleware._save_log)
        self.driver.add_cdp_listener('Network.responseReceived', SeleniumCrawlMiddleware._save_log)

    @classmethod
    def from_crawler(cls, crawler):
        o = cls(crawler.settings, crawler.stats)
        crawler.signals.connect(o.spider_closed, signals.spider_closed)
        return o

    def process_request(self, request, spider):
        selenium_meta = request.meta.get('SeleniumCrawl') or {}
        if selenium_meta.get('enabled') is True:

            # ????????????????????????
            _window_size = selenium_meta.get('size')
            self.driver.set_window_size(_window_size[0], _window_size[1])
            # ???????????????JS????????????
            self.driver.set_page_load_timeout(selenium_meta.get('load_time'))
            self.driver.set_script_timeout(selenium_meta.get('load_time'))

            try:
                # ????????????UA???????????????
                if selenium_meta.get('random_ua'):
                    self.driver.execute_cdp_cmd("Emulation.setUserAgentOverride", {
                        "userAgent": request.headers.getlist('User-Agent')[0].decode()
                    })

                # ??????????????????
                self.driver.get(request.url)
                time.sleep(1.53 if self.download_delay < 1 else self.download_delay)
                # ???????????????????????????????????????????????????????????? 5??????
                WaitListChecker.judgement(self.driver.page_source)

                # cookie??????
                if len(request.cookies.items()) > 0:
                    self.driver.delete_all_cookies()
                    for cookie_name, cookie_value in request.cookies.items():
                        self.driver.add_cookie(
                            {
                                'name': cookie_name,
                                'value': cookie_value
                            }
                        )
                    self.driver.get(request.url)

                # ??????
                _delay = selenium_meta.get('delay')
                _until = selenium_meta.get('until', False)
                # ???????????????
                time.sleep(_delay)
                # ????????????
                if _until is not None and '' != _until:
                    WebDriverWait(self.driver, _delay, 0.5).until(
                        EC.presence_of_element_located((By.XPATH, _until))
                    )
            except TimeoutException:
                self.driver.execute_script('window.stop()')

            try:
                # ????????????
                _script = selenium_meta.get('script')
                if _script is not None and '' != _script:
                    selenium_logger.debug('??????????????? %s', _script)
                    self.driver.execute_script(_script)

                # ??????
                _screenshot = selenium_meta.get('screenshot')
                if _screenshot is not None and '' != _screenshot:
                    if 'single' == _screenshot:
                        selenium_meta['screenshot_result'] = self.driver.get_screenshot_as_base64()
                    else:
                        ele = self.driver.find_element(By.XPATH, _screenshot)
                        selenium_meta['screenshot_result'] = ele.screenshot_as_base64

                # headers ??????
                selenium_cookies = self.driver.get_cookies()
                if len(selenium_cookies) > 0:
                    cookie_list = [item['name'] + '=' + item['value'] for item in selenium_cookies]
                    cookies = ';'.join(item for item in cookie_list)
                    selenium_meta['cookies'] = cookies

                request_headers, response_headers = self.get_headers(self.driver.current_url,
                                                                     SeleniumCrawlMiddleware._save_log_list)
                selenium_meta['request_headers'] = request_headers
                selenium_meta['response_headers'] = response_headers

                # ??????????????????
                element_source = self.driver.find_element(By.TAG_NAME, 'html').parent.page_source

                # ??????
                SeleniumCrawlMiddleware._save_log_list.clear()

                # ????????????
                self.stats.inc_value('downloader/request_count', spider=spider)
                self.stats.inc_value(F'downloader/request_method_count/{request.method}', spider=spider)
                self.stats.inc_value('downloader/request_bytes', len(request_httprepr(request)), spider=spider)

                # ??????????????????
                return HtmlResponse(url=self.driver.current_url,
                                    body=element_source,
                                    encoding='utf-8',
                                    request=request,
                                    status=200)

            except WebDriverException as e:
                selenium_logger.error('WebDriver ?????? ==> [%s]' % e)
                raise e
        return None

    def spider_closed(self):
        try:
            # ?????????????????????
            self.driver.get('chrome://settings/clearBrowserData')
            # 2S ????????????
            time.sleep(2)
            self.driver.execute_script(
                'return document.querySelector("body > settings-ui").shadowRoot.querySelector("#main").shadowRoot.querySelector("settings-basic-page").shadowRoot.querySelector("#basicPage > settings-section:nth-child(9) > settings-privacy-page").shadowRoot.querySelector("settings-clear-browsing-data-dialog").shadowRoot.querySelector("#clearFromBasic").shadowRoot.querySelector("#dropdownMenu").value = 4')
            time.sleep(1)
            clear_button = self.driver.execute_script(
                'return document.querySelector("body > settings-ui").shadowRoot.querySelector("#main").shadowRoot.querySelector("settings-basic-page").shadowRoot.querySelector("#basicPage > settings-section:nth-child(9) > settings-privacy-page").shadowRoot.querySelector("settings-clear-browsing-data-dialog").shadowRoot.querySelector("#clearBrowsingDataConfirm")')
            time.sleep(1)
            clear_button.click()
            time.sleep(6)
        except ElementNotInteractableException:
            pass
        finally:
            self.driver.quit()


class ProxyExtension:
    manifest_json = """
    {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Chrome Proxy",
        "permissions": [
            "proxy",
            "tabs",
            "unlimitedStorage",
            "storage",
            "<all_urls>",
            "webRequest",
            "webRequestBlocking"
        ],
        "background": {"scripts": ["background.js"]},
        "minimum_chrome_version": "76.0.0"
    }
    """

    background_js = """
    var config = {
        mode: "fixed_servers",
        rules: {
            singleProxy: {
                scheme: "http",
                host: "%s",
                port: %d
            },
            bypassList: ["localhost"]
        }
    };

    chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

    function callbackFn(details) {
        return {
            authCredentials: {
                username: "%s",
                password: "%s"
            }
        };
    }

    chrome.webRequest.onAuthRequired.addListener(
        callbackFn,
        { urls: ["<all_urls>"] },
        ['blocking']
    );
    """

    def __init__(self, host, port, user, password):
        self._dir = os.path.normpath(tempfile.mkdtemp())

        manifest_file = os.path.join(self._dir, "manifest.json")
        with open(manifest_file, mode="w") as f:
            f.write(self.manifest_json)

        background_js = self.background_js % (host, port, user, password)
        background_file = os.path.join(self._dir, "background.js")
        with open(background_file, mode="w") as f:
            f.write(background_js)

    @property
    def directory(self):
        return self._dir

    def __del__(self):
        shutil.rmtree(self._dir)
