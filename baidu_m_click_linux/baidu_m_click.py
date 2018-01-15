#! /usr/bin/env python
# -*- coding:utf-8 -*-
#====#====#====#====
# __author__ = "blackang"
#FileName: *.py
#Version:1.0.0
#====#====#====#====

import logging
import os
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import time
import datetime
import traceback
import random
from time import sleep
from function import logInit
from selenium import webdriver
from seleniumrequests import Chrome
from selenium.webdriver.common.action_chains import ActionChains #引入ActionChains鼠标操作类
from selenium.webdriver.common.keys import Keys
import selenium.webdriver.support.ui as ui
from selenium.common.exceptions import NoSuchElementException
from proxy import proxy

# os.system('export LANG=zh_CN.UTF-8')
os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.ZHS16GBK'
import cx_Oracle


class MBaiduKeyword():
    def __init__(self):
        self.logger = logging.getLogger('MBaiduKeyword')
        self.init_oracle()
        self.proxy = proxy('phantomjs')
        # self.init_browser(browser_type)


    def __del__(self):
        self.browser_quit()

    def init_oracle(self):
        self.oracle_db = cx_Oracle.connect('match_manual/jkn65#ud@192.168.100.61:1521/bjdt')

    def init_browser(self,browser_type):
        self.browser = self.proxy.get_new_webdriver_with_proxy()
        # self.browser = webdriver.PhantomJS()
        # self.browser = webdriver.PhantomJS(service_args=['--load-images=false'])
        self.browser.maximize_window()
        self.pid = self.browser.service.process.pid
        self.wait = ui.WebDriverWait(self.browser, 40)

    def browser_quit(self):
        try:
            if self.browser:
                self.browser.quit()
                # os.kill(self.pid, 9)
        except Exception, e:
            self.logger.warning("browser quit error:%s" % (str(e)))
        finally:
            self.browser = None

    def get_keyword_from_oracle(self):
        oracle_cur = self.oracle_db.cursor()
        oracle_handle = oracle_cur.execute("select distinct(a.keyword) from  p4p_malad_keyword a where a.state=0 and a.begindate < sysdate and a.enddate > sysdate")
        keywords = oracle_handle.fetchall()
        oracle_cur.close()
        #self.oracle_db.close()
        return keywords
        # pass

    ## page down
    def page_down_click(self):
        c =0
        while c < 10:
            c+=1
            ac = ActionChains(self.browser)
            ac.send_keys(Keys.PAGE_DOWN).perform()
            time.sleep(0.1)

    def back_quit(self):
        self.browser.back()

    def back_back_quit(self):
        self.browser.back()
        self.browser.back()
        self.browser_quit()
        

    def click(self, keyword):
        # self.init_browser('chrome')
        self.init_browser('phantomjs')
        self.browser.get('https://m.baidu.com')
        ele = self.browser.find_element_by_xpath("//input[@id='index-kw']")

        ele.clear()
        ele.send_keys(keyword, Keys.ENTER)
        self.page_down_click()

        on_sale = None
        on_sale_nextpage = None
        try:
            ## 在售商品的xpath
            on_sale = self.browser.find_element_by_xpath("//a[@class='WA_LOG_SF c-blocka wa-tour-route-title']/h3[@class='c-title c-gap-top-small']")
            if on_sale:
                logging.info('the keyword on first page , browser quit!')
                self.browser_quit()
 #           //a[@class='WA_LOG_SF c-blocka wa-tour-route-title c-visited']/h3[@class='c-title c-gap-top-small']
        except NoSuchElementException as e:
            logging.error(' first page cant find xpath (%s)' % e)
            ## 如果第一页不存在，则点击下一页
            self.browser.find_element_by_xpath("//a[@class='new-nextpage-only']").click()
            logging.info('into next page ')
            self.page_down_click()

            try:
                on_sale_nextpage = self.browser.find_element_by_xpath("//a[@class='WA_LOG_SF c-blocka wa-tour-route-title']/h3[@class='c-title c-gap-top-small']")
                if on_sale_nextpage:
                    on_sale_nextpage.click()
                    logging.info('into detail title page ')
                    self.page_down_click()
                    time.sleep(random.choice([3, 5]))
                    ## 判断detail page 商机条数
                    try:
                        detail_titles = self.browser.find_elements_by_xpath(
                            "//div[@class='c-span8']/div[@class='c-line-clamp1']")
                        logging.info('detail titles len is : %d' % len(detail_titles))
                    except NoSuchElementException as e:
                        logging.error(' cant find detail xpath (%s)' % e)
                        pass
                    ## 商品条数<=6，则返回上一页，后关闭浏览器
                    if len(detail_titles) <= 6:
                        logging.info('titles less than 6, browser quit!')
                        self.back_quit()
                        self.browser_quit()
                    else:  ##坑 要点击的xpath是选取对应标题的href
                        logging.info('click the No.7 title !')
                        ## 先点击第7条商品，进入对应页面后停留2秒钟后，返回大标题落地页
                        self.browser.find_element_by_xpath(
                            "//*[@id='super-frame']/div/b-superframe-body/div/div[2]/div/div/div[3]/b-infinitescroll/div/div[1]/ul[1]/a[7]").click()
                        logging.info('into the ---No.7--- detail page and sleep 2s')
                        self.back_quit()
                        logging.info('back titles page and if or No.8')
                        if len(detail_titles) > 7:
                            ##点击第8条，进入对应页面后停留2秒钟，返回大标题落地页，再返回上一页，再关闭浏览器
                            self.browser.find_element_by_xpath(
                                "//*[@id='super-frame']/div/b-superframe-body/div/div[2]/div/div/div[3]/b-infinitescroll/div/div[1]/ul[2]/a[1]").click()
                            logging.info('into the ---No.8--- detail page and sleep 2s')
                            self.back_back_quit()
                            logging.info('the No.8 back and back and browser quit')
                        ## 商品条数=7，则继续返回上一页，再关闭浏览器
                        elif len(detail_titles) == 7:
                            self.browser.back()
                            # time.sleep(0.5)
                            self.browser_quit()
                            logging.info('only No.7 and back and browser quit')
            except NoSuchElementException as e:
                logging.error(' next page cant find xpath (%s)' % e)
                time.sleep(0.5)
                logging.info('the keyword not in first_and_second page , browser quit!')
                self.browser_quit()


if __name__ == '__main__':
    dirname = os.path.split(os.path.abspath(sys.argv[0]))[0]
    log_file = dirname + '/logs/spider.log'
    logInit(log_file, logging.INFO, True, 0)


    # keyword = u'安全钩'
    m_baidu = MBaiduKeyword()
    count = 1
    while count < 2:
        try:
            keywords = m_baidu.get_keyword_from_oracle()
            # keywords = [u'安全钩',]
            for index, keyword in enumerate(keywords):
                keyword = keyword[0].decode('gb18030')
                logging.info('spider keyword : %s, index : %d, count : %d' % (keyword, index, count))
                m_baidu.click(keyword)
            count += 1
        except Exception, e:
            logging.error(str(traceback.format_exc()))
            m_baidu.browser_quit()
