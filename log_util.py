#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''=================================================
@Author ：baixue
@Date   ：2022/9/15 16:23
=================================================='''


import os
import sys
import datetime
from pathlib import Path
import logging
from logging.handlers import TimedRotatingFileHandler

########################################### 示例1: ###########################################
def init_logger(name=datetime.datetime.now().strftime("%y-%m-%d_%H.%M.%S"), root_dir=None, level=logging.INFO):
    logFormatter = logging.Formatter(fmt="%(asctime)s %(levelname)s %(message)s", datefmt='%y-%m-%d %H:%M:%S')
    rootLogger = logging.getLogger(name)
    rootLogger.setLevel(level)
    rootLogger.propagate = False

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    attached_to_std = False
    for handler in rootLogger.handlers:
        # 查看rootLogger是否已经有StreamHandler
        if isinstance(handler, logging.StreamHandler):
            if handler.stream == sys.stderr or handler.stream == sys.stdout:
                attached_to_std = True
                break
    if not attached_to_std:
        rootLogger.addHandler(consoleHandler)
    consoleHandler.setLevel(level)

    if root_dir:
        os.makedirs(root_dir, exist_ok=True)
        fileHandler = TimedRotatingFileHandler(
            filename="{0}/{1}.log".format(root_dir, name),
            when="midnight",
            interval=1,
            backupCount=7)
        fileHandler.setFormatter(logFormatter)
        rootLogger.addHandler(fileHandler)
        fileHandler.setLevel(level)
    return rootLogger


########################################### 示例2: ###########################################
def set_logger(log_dir, model_name, dataset_name, verbose_level):

    # base logger
    log_file_path = Path(log_dir) / f"{model_name}-{dataset_name}.log"
    logger = logging.getLogger('MMSA')
    logger.setLevel(logging.DEBUG)

    # file handler
    fh = logging.FileHandler(log_file_path)
    fh_formatter = logging.Formatter('%(asctime)s - %(name)s [%(levelname)s] - %(message)s')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fh_formatter)
    logger.addHandler(fh)

    # stream handler
    stream_level = {0: logging.ERROR, 1: logging.INFO, 2: logging.DEBUG}
    ch = logging.StreamHandler()
    ch.setLevel(stream_level[verbose_level])
    ch_formatter = logging.Formatter('%(name)s - %(message)s')
    ch.setFormatter(ch_formatter)
    logger.addHandler(ch)

    return logger


# 使用：
log_dir = Path(__file__).parent / "logs"
model_name = 'lmf'
dataset_name = 'mosi'
verbose_level = 1
logger = set_logger(log_dir, model_name, dataset_name, verbose_level)
logger.info("===Program Start ===")