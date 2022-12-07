#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''=================================================
@Author ：baixue
@Date   ：2022/9/15 16:23
=================================================='''

import argparse

parser = argparse.ArgumentParser(description='单品商家预测')
parser.add_argument('--config_file',
                    type=str,
                    default='/home/baixue05/Dianshang/single_product_merchant/single_product_merchant_kml/config/config.json',
                    help='配置文件')
parser.add_argument('--p_date', type=str, default=None, help='需要处理数据的日期')
args = parser.parse_args()

# args.p_date = '20221013'
# SPM = PredictSPM(args.config_file, args.p_date)
# SPM.predict_processing()