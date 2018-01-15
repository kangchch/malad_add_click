# -*- coding: utf-8 -*-

from pymongo import MongoClient
from random import choice
import os
import sys
from selenium import webdriver
from seleniumrequests import Chrome
from seleniumrequests import PhantomJS
from selenium.webdriver.chrome.options import Options
import logging
import random

class proxy():
    def __init__(self, browser_type='chrome', ua='', log_dir=''):
        self.browser_type = browser_type
        self.logger = logging.getLogger("PORXY")
        if not log_dir:
            log_dir, filename = os.path.split(os.path.abspath(sys.argv[0]))
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        self.service_log_path = log_dir + '/logs/ghostdriver.log'

        self.ua = ua if ua else "user-agent=Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36"

        mongo_db = MongoClient('192.168.60.65', 10010).anti_ban
        TJ_IP_MAPS = {'10.10.10.21': '125.39.72.11',
              '10.10.10.22': '125.39.72.118',
              '10.10.10.23': '125.39.72.225',
              '10.10.10.24': '125.39.0.146',
              '10.10.10.25': '60.28.110.66',
              '10.10.10.26': '125.39.149.48',
              '10.10.10.27': '111.161.24.2'
              }
        self.proxy_list = []
        for item in mongo_db.tj_proxy.find():
            ip = item['ip']
            proxy_host = ip[ip.find('://')+3 : ip.rfind(':')]
            proxy_port = ip[ip.rfind(':') + 1 :]
            proxy_username, proxy_password = item['user_pass'].split(':')
            source_ip = item['source_ip']
            self.proxy_list.append({'proxy_host': proxy_host,
                                    'proxy_port': int(proxy_port),
                                    'proxy_username': proxy_username,
                                    'proxy_password': proxy_password,
                                    'source_ip': source_ip,
                                    'type': 2})
        random.shuffle(self.proxy_list)

    def init_proxy_queue(self):
        from Queue import Queue
        self.proxy_queue = Queue()
        tj_ips = {}
        for i in self.proxy_list:
            ip_head =  i['source_ip'].split('.')[0]
            if ip_head not in tj_ips:
                tj_ips[ip_head] = []
            tj_ips[ip_head].append(i)

        short_length = 99999
        for k in tj_ips:
            if short_length > len(tj_ips[k]):
                short_length = len(tj_ips[k])

        for _ in range(short_length):
            for k in tj_ips:
                self.proxy_queue.put(tj_ips[k].pop())

        # mongo_db = MongoClient('192.168.60.65', 10010).proxy
        # for item in mongo_db.ip_tbl.find({"status": 1}).sort([("update_time", -1)]):
        #     proxy_host = item['ip']
        #     proxy_port = item['port']
        #     source_ip = item['ip']
        #     proxy_type = item['type']
        #     self.proxy_queue.put({'proxy_host': proxy_host,
        #                             'proxy_port': int(proxy_port),
        #                             'source_ip': source_ip,
        #                             'type': proxy_type})
        logging.info('proxy initialization complete %d', self.proxy_queue.qsize())

    def browser_quit(self, browser):
        try:
            if browser:
                pid = browser.service.process.pid
                browser.quit()
                os.kill(pid, 9)
        except:
            pass
        finally:
            browser = None

    def get_chrome_driver_with_proxy(self, proxy_info, scheme='http', plugin_path=None):
        """Proxy Auth Extension

        args:
            proxy_host (str): domain or ip address, ie proxy.domain.com
            proxy_port (int): port
            proxy_username (str): auth username
            proxy_password (str): auth password
        kwargs:
            scheme (str): proxy scheme, default http
            plugin_path (str): absolute path of the extension

        return str -> plugin_path
        """
        import string
        import zipfile

        if plugin_path is None:
            plugin_path = 'c://chrome_proxyauth_plugin.zip'

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
            "background": {
                "scripts": ["background.js"]
            },
            "minimum_chrome_version":"22.0.0"
        }
        """

        background_js = string.Template(
        """
        var config = {
                mode: "fixed_servers",
                rules: {
                  singleProxy: {
                    scheme: "${scheme}",
                    host: "${host}",
                    port: parseInt(${port})
                  },
                  bypassList: ["foobar.com"]
                }
              };

        chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

        function callbackFn(details) {
            return {
                authCredentials: {
                    username: "${username}",
                    password: "${password}"
                }
            };
        }

        chrome.webRequest.onAuthRequired.addListener(
                    callbackFn,
                    {urls: ["<all_urls>"]},
                    ['blocking']
        );
        """
        ).substitute(
            host=proxy_info['proxy_host'],
            port=proxy_info['proxy_port'],
            username=proxy_info.get('proxy_username', ''),
            password=proxy_info.get('proxy_password', ''),
            scheme=scheme,
        )
        with zipfile.ZipFile(plugin_path, 'w') as zp:
            zp.writestr("manifest.json", manifest_json)
            zp.writestr("background.js", background_js)

        opts = Options()
        opts.add_argument("--start-maximized")
        # opts.add_argument("--headless")
        # opts.add_argument("--disable-gpu")
        opts.add_argument(self.ua)
        if 'proxy_username' in proxy_info and 'proxy_password' in proxy_info:
            opts.add_extension(plugin_path)
        else:
            opts.add_argument('--proxy-server=%s://%s:%d' % (scheme, proxy_info['proxy_host'], proxy_info['proxy_port']))
        chrome_driver = os.path.abspath("./chromedriver.exe")
        browser = Chrome(chrome_driver, service_log_path=self.service_log_path, chrome_options=opts)
        self.logger.info('set proxy %s:%s source ip: %s type: %d',
                         proxy_info['proxy_host'], proxy_info.get('proxy_username', ''), proxy_info['source_ip'], proxy_info['type'])
        return browser

    def get_phantomjs_driver_with_proxy(self, proxy_info, scheme='http'):
        webdriver.DesiredCapabilities.PHANTOMJS['phantomjs.page.settings.userAgent'] = self.ua
        webdriver.DesiredCapabilities.PHANTOMJS['phantomjs.page.settings.resourceTimeout'] = '5000'
        if 'proxy_username' in proxy_info and 'proxy_password' in proxy_info:
            service_args = [
                '--proxy=%s:%s' % (proxy_info['proxy_host'], proxy_info['proxy_port']),
                '--proxy-auth=%s:%s' % (proxy_info['proxy_username'], proxy_info['proxy_password']),
                '--proxy-type=%s' % (scheme),
                '--ignore-ssl-errors=true',
            ]
        else:
            service_args = [
                '--proxy=%s:%s' % (proxy_info['proxy_host'], proxy_info['proxy_port']),
                '--proxy-type=%s' % (scheme),
                '--ignore-ssl-errors=true',
            ]
        browser = PhantomJS(service_args=service_args)
        self.logger.info('set proxy %s:%s source ip: %s type: %d',
                         proxy_info['proxy_host'], proxy_info.get('proxy_username'), proxy_info['source_ip'], proxy_info['type'])
        return browser

    def get_new_webdriver_with_proxy(self, browser=None):
        if browser:
            self.browser_quit(browser)

        self.proxy_info = choice(self.proxy_list)
        if self.browser_type.lower() == 'chrome':
            return self.get_chrome_driver_with_proxy(self.proxy_info)
        elif self.browser_type.lower() == 'phantomjs':
            return self.get_phantomjs_driver_with_proxy(self.proxy_info)
        else:
            self.logger.error('invalid browser type!')
            return None

    def get_test_proxy_webdriver(self, browser=None):
        if browser:
            self.browser_quit(browser)

        proxy_info = self.proxy_queue.get()
        if self.browser_type.lower() == 'chrome':
            return self.get_chrome_driver_with_proxy(proxy_info)
        elif self.browser_type.lower() == 'phantomjs':
            return self.get_phantomjs_driver_with_proxy(proxy_info)
        else:
            self.logger.error('invalid browser type!')
            return None

