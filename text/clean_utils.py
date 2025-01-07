#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''=================================================
@Author  :   baixue
@Date    :   2024/09/11 16:07:44
@Desc    :   清理文本杂质常用函数
================================================='''


import json
import sys
import jieba
import re
from collections import defaultdict


def replace_punctuation_with_space(text):
    # 定义一个正则表达式，匹配所有标点符号
    punctuation_pattern = r'[^\w\s]'
    # 使用 re.sub() 将所有标点符号替换为空格
    clean_text = re.sub(punctuation_pattern, ' ', text)
    # 将多个连续的空格替换为单个空格
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    return clean_text


def is_garbled_string(st, lang=None):

    # 1.� 篇幅占5%，则为真
    if '�' in st or '□' in st:
        garbled_pattern = re.compile(r'[�□]')
        matches = garbled_pattern.findall(st)
        l = len(matches)
        ratio = l / len(st)
        if matches and ratio > 0.01:
            return True, f"luanma ratio: {ratio}"
        
    # 2.若为中文，jieba分词统计平均长度
    if lang == 'zh':
        seg_list = jieba.cut(st)
        words = len(list(seg_list))
        ratio = len(st) / words
        if ratio < 1.2:
            return True, f"jieba ratio：{ratio}"

    # 3. 兜底策略：检查字符频率，如果有字符频率过高，信息量不大。
    st = replace_punctuation_with_space(st)
    if st.count(' ') > len(st) * 0.05:
        # 空格占比超5%，判定为以空格分割的语言
        word_cnter = defaultdict(int)
        max_cnt = 0
        max_word = None
        words = st.split(' ')
        for word in words:
            word_cnter[word] += 1
            if max_cnt < word_cnter[word]:
                max_cnt = word_cnter[word]
                max_word = word
        if max_cnt > len(words) * 0.40:
            return True, f'is garbled. word = {max_word}'
    else:
        # 单字符语言
        char_cnter = defaultdict(int)
        max_cnt = 0
        max_char = None
        for char in st:
            char_cnter[char] += 1
            if max_cnt < char_cnter[char]:
                max_cnt = char_cnter[char]
                max_char = char
        if max_cnt > len(st) * 0.40:
            return True, f'is garbled. char = {max_char}'
    return False, ""


def remove_emails(text):
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
    no_emails_text = re.sub(email_pattern, '[EMAIL]', text)
    return no_emails_text


def clean_content(content):
    #用于匹配非常规空格
    space_re = re.compile(r'[^\S\n\t\r\v\f ]', re.IGNORECASE)
    content = space_re.sub(' ', content)
    # 将连续多个换行符（\n）或回车符（\r）替换为两个换行符
    content = re.sub(r'\r\n|\r', '\n', content)  # 统一换行符为 \n
    content = re.sub(r'\n{2,}', '\n\n', content)  # 将连续多个换行符替换为两个换行符
    return content






    
