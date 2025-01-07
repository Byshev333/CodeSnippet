#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''=================================================
@Author  :   baixue
@Date    :   2025/01/07 11:23:48
@Desc    :   利用fasttext进行语言检测
================================================='''


import fasttext
import json

model = fasttext.load_model('/nlp_group/baixue05/tools/lid.176.bin')

with open('/nlp_group/baixue05/LLM_aries/pretraindata/pdf_data/chatgpt/check_tmp.json', 'r') as fr, open('/nlp_group/baixue05/LLM_aries/pretraindata/pdf_data/chatgpt/check_tmp1.json', 'w') as fw:
    for line in fr:
        line_ori = line
        line = json.loads(line.rstrip())
        text = line['title']
        predict = model.predict(text, k=1)
        lang = predict[0][0].split('__label__')
        if lang not in ['zh', 'en']:
            continue
        else:
            fw.write(line_ori + '\n')

