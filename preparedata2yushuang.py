#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''=================================================
@Author ：baixue
@Date   ：2022/9/15 16:21
=================================================='''

import pandas as pd
import json


def preparedata2yushuang(input, output):
    relabel_id = []
    with open('../test_data/商业化/std_test_set/relabel.txt', 'r') as fr:
        for line in fr:
            relabel_id.append(int(line.strip().split('.')[0]))
            print(int(line.strip().split('.')[0]))
    df = pd.read_excel(input)
    df = df.fillna('')
    row_num = df.shape[0]
    info_list = []
    pid_list = []

    file = open(output, 'a', encoding='utf-8')
    for i in range(row_num):
        item_id = df.loc[i, 'item_id']
        if int(item_id) in relabel_id:
            item_title = df.loc[i, 'item_title']
            item_url = df.loc[i, 'img_url']
            category = df.loc[i, 'category']
            item_short_title = df.loc[i, 'pred_short_title']
            brand = df.loc[i, 'brand']

            item_info = "<img style=\"width: 200px; height: 200px;\" src=\"" + item_url + "\"/><br>" + item_title + '(' + category + ' ' + \
                        brand + ')' + '<br>' + item_short_title

            dic_ = {"text": item_info, 'category': str(item_id)}
            dic_ = json.dumps(dic_, ensure_ascii=False)
            file.write(dic_ + '\n')
    file.close()


def label_for_yushuang(input, output):
    df = pd.read_excel(input)
    df = df.fillna('')
    pid_list = df['photo_id'].to_list()
    title_list = df['item_title'].to_list()
    desc_list = df['course_desc'].to_list()
    img_url_list = df['item_img_url'].to_list()
    category1_list = df['first_level_category_name'].to_list()
    category2_list = df['second_level_category_name'].to_list()
    category3_list = df['third_level_category_name'].to_list()
    # category4_list = df['fourth_level_category_name'].to_list()
    valid_pid = []
    hetu_info = []
    item_img_info = []
    merchandise_info = []

    frameIds = []

    print(len(list((set(pid_list)))))
    print(len(df))
    for i in range(len(df)):
        key_list = ['剪辑', '影视', '录制', '特效', '快影']
        if any(key in title_list[i] for key in key_list):
            continue
        if pid_list[i] in set(valid_pid):
            continue
        valid_pid.append(pid_list[i])
        hetu_info.append('{}<sep>{}<sep>{}'.format(category1_list[i], category2_list[i], category3_list[i]))
        merchandise_info.append('{}<sep>{}'.format(title_list[i], desc_list[i]))
        item_img_info.append('<img src = "' + img_url_list[i] + '", style=" width: 200px;"/>')
        frameIds.append("h,0,1,2,3,4,5,6,7,8")

    print(len(valid_pid))
    print(len(hetu_info))
    print(len(merchandise_info))
    print(len(item_img_info))
    data = {'photoId': valid_pid,
            'hetuInfo': hetu_info,
            'category': merchandise_info,
            'extData': item_img_info,
            'frameIds': frameIds}

    df_label = pd.DataFrame(data)
    df_label.to_excel(output, index=False)