# -*- coding: utf-8 -*-
import os
import logging
from logging.handlers import TimedRotatingFileHandler

ERR_CODE = {'OK':0, 'CLOSE':1, 'TEMP':2, 'BLOCK':3, 'IGNORE':4}
USERNAMES_STATUS = {'STANDBY':0, 'OK':1, 'FAILED':2}

def logInit(log_file, loglevel=logging.INFO, consoleshow=False, backup_count=0):
    dirname, filename = os.path.split(log_file)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    fileTimeHandler = logging.FileHandler(log_file)
    formatter = logging.Formatter('[%(levelname)s] %(asctime)s %(message)s')
    fileTimeHandler.setFormatter(formatter)
    logging.getLogger('').addHandler(fileTimeHandler)
    logging.getLogger('').setLevel(loglevel)
    if consoleshow:
      console = logging.StreamHandler()
      console.setLevel(loglevel)
      console.setFormatter(formatter)
      logging.getLogger('').addHandler(console)


def get_errcode(jump_url):
    err_str = {
        '/wrongpage.html': ERR_CODE['CLOSE'],
        '/noshop.html': ERR_CODE['CLOSE'],
        '/close.html': ERR_CODE['CLOSE'],
        '/weidaoda.html': ERR_CODE['CLOSE'],
        '//wo.1688.com': ERR_CODE['CLOSE'],
        '/wgxj.html': ERR_CODE['CLOSE'],
        'login': ERR_CODE['BLOCK'],
        'anti': ERR_CODE['BLOCK'],
        'checkcodev': ERR_CODE['BLOCK'],
        'kylin': ERR_CODE['BLOCK'],
        'creditdetail': ERR_CODE['OK']}
    for k in err_str:
        if jump_url.find(k) >= 0:
            return err_str[k]
    return ERR_CODE['TEMP']
