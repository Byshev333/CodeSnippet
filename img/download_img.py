#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''=================================================
@Author ：baixue
@Date   ：2022/9/15 16:23
=================================================='''

from argparse import ArgumentParser
from pathlib import Path
import urllib.request
import multiprocessing
from multiprocessing import Pool
import logging
import pandas as pd
from PIL import Image
import json
import os
import time

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.86 Safari/537.36"}
opener = urllib.request.build_opener()
opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1941.0 Safari/537.36')]
urllib.request.install_opener(opener)


def get_chunk_data(data, chunk_size=100, ignore_last=False):
    """对数据分块, 按照每块的数据量切分.
    Args:
        data: 数据, 格式需要支持索引切片.
        chunk_size: 块大小.
        ignore_last: 是否忽略最后一片长度不足的数据, 默认False.
    Returns:
        分块后的数据, 列表形式.
    """
    data_chunk = list()
    for index in range(0, len(data), chunk_size):
        data_chunk.append(data[index: index + chunk_size])

    if ignore_last and data_chunk and len(data_chunk[-1]) != chunk_size:
        return data_chunk[:-1]
    else:
        return data_chunk


def __download_one(url, out_path, mylist):
    """下载一个"""

    try:
        urllib.request.urlretrieve(url, out_path)
        img = Image.open(out_path).convert('RGB')
    except BaseException as e:
        print(f"下载失败 {url}")
    else:
        mylist.append(out_path)


def download_imgs(url_lines, item_ids, out_dir):
    params_list = list()
    mylist = multiprocessing.Manager().list()  # 主进程与子进程共享这个List
    for url_suffix, id in zip(url_lines, item_ids):
        if url_suffix:
            complete_url = f"{url_suffix}"
            out_path = out_dir + '/' + str(id) + '.jpg'
            params_list.append((complete_url, out_path, mylist))

    param_chunks = get_chunk_data(params_list, 100, False)

    for chunk_index, param_chunk in enumerate(param_chunks):
        with Pool(50) as pool:
            _ = pool.starmap(__download_one, param_chunk)
        print(f"下载完成 {(chunk_index + 1) * 100} 个图片.")
    return mylist


if __name__ == "__main__":
    """命令行参数"""
    parser = ArgumentParser(description="下载图片")
    parser.add_argument('origin_file', type=Path, help='原始数据')
    parser.add_argument('out_dir', type=str, help="下载图片的保存路径.")
    args = parser.parse_args()
    # url = 'https://ali-ad.a.yximgs.com/bs2/image-kwaishop-product/d7cc244d-cc84-44fb-aefd-07348668ab1b-i17136202.jpg'
    # out_dir = '/ec42/baixue/dataset/plc_course/data401/item_imgs/122536978796.jpg'
    # mylist = multiprocessing.Manager().list()  # 主进程与子进程共享这个List
    # __download_one(url, out_dir, mylist)

    print('Conda deactivate...')  # 避免Image读取错误
    os.system('conda deactivate')
    time.sleep(10)

    print('Connect the internet...')
    os.system('export http_proxy=http://bjrz-squid4.lf:11080 && export https_proxy=http://bjrz-squid4.lf:11080')
    time.sleep(10)

    print('Download imgs...')
    df = pd.read_excel(args.origin_file)
    df = df.fillna('None')
    item_img_urls = df['item_img_url'].to_list()
    item_ids = df['item_id'].to_list()
    print(item_img_urls[:5])

    valid_img = download_imgs(item_img_urls, item_ids, args.out_dir)

    print('Need to download {} item imgs.'.format(len(item_ids)))
    print('Download {} valid item imgs.'.format(len(valid_img)))
