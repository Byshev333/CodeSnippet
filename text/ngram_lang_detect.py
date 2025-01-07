#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''=================================================
@Author  :   baixue
@Date    :   2025/01/07 11:27:12
@Desc    :   N-gram 检测
================================================='''


import fasttext
import json
import sys
from sys import *
import math
import hashlib
import random
import os
import re
from collections import Counter, defaultdict
import emoji
import time
import unicodedata
import jieba
import subprocess
from dedup import ModifyingDocuments

model = fasttext.load_model('/nlp_group/baixue05/tools/lid.176.bin')


def detect_language(text):
    # 使用模型预测语言
    text = text.replace('\n', ' ').strip()
    predictions = model.predict(text, k=1)  # k=1 表示返回概率最高的语言
    language = predictions[0][0].replace('__label__', '')  # 提取语言代码
    probability = predictions[1][0]  # 提取预测概率
    return language, probability


def filter_by_language(text, allowed_languages=('zh', 'en'), threshold=0.65):
    lang, prob = detect_language(text)
    if lang in allowed_languages:
        return lang, prob
    return None, None


tokenizer = subprocess.Popen(['./tokenizer_bin/cstokenizer', '--encode', './tokenizer/tokenizer.model'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
id2token = {}
token2id = {}
with open('./tokenizer/tokenizer.model', encoding='utf-8-sig') as f:
    json_dict = json.load(f)
    for one in json_dict["CommonTokens"]:
        id2token[one['TokenID']] = bytes(one['TokenBytes'])
        token2id[bytes(one['TokenBytes'])] = one['TokenID']
    for one in json_dict["SpecialTokens"]:
        id2token[one['TokenID']] = one['TokenStr'].encode('utf8')
        token2id[one['TokenStr'].encode('utf8')] = one['TokenID']

        
def text2token(text):
    if len(text) == 0:
        return []
    tk_j = {}
    #删除sp token
    tk_j['text'] = text
    #去除自定义标签
    s = str(json.dumps(tk_j, ensure_ascii= False))
    tokenizer.stdin.write(s + "\n")
    tokenizer.stdin.flush()
    segs = tokenizer.stdout.readline().strip().split(',')
    segs = [int(one) for one in segs]
    pieces = [id2token[one] for one in segs]
    return pieces


def get_repetition_n_gram_ratio(text, words):
    '''21. 统计n-gram的词频（先用tokenize切分），n取1/2/3/4，使用一个dict统计所有n-gram的词频，然后按照词频从高到低排序
    假设频率最高的词是s，那么计算s中包含的字符数量为 len(s) * dict[s]，除以整个doc的字符数量
    超过一定比例的，整个doc丢掉
    Gopher里头2-gram的阈值是0.2, 3-gram是0.18, 4-gram是0.16，可以参考，但是最好调一下，而且1-gram也需要设置一下。
    参考https://github.com/huggingface/datatrove/blob/main/src/datatrove/pipeline/filters/gopher_repetition_filter.py中关于find_top_duplicate函数的实现。

    22. 统计n-gram的词频（先用tokenize切分），n取5/6/7/8/9/10
    使用一个set统计所有n-gram是否前面出现过，如果是，则将相应的字符数量累计起来，作为重复n-gram的字符数量
    （注意，这里是n-gram的n对应的是word，但是累计的时候，是这些word对应的字符的总量）
    而一旦重复，就需要跳过n的长度产生下一个n-gram，避免重复计算
    最后将重复n-gram的字符总数，除以整个doc的字符数量，超过一定比例的，整个doc丢掉
    Gopher里头5-gram的阈值是0.15, 6-gram是0.14, 7-gram是0.13, 8-gram是0.12, 9-gram是0.11, 10-gram是0.10，可以参考，但是最好调一下。
    参考https://github.com/huggingface/datatrove/blob/main/src/datatrove/pipeline/filters/gopher_repetition_filter.py中关于find_all_duplicate函数的实现。    
    '''
    def get_n_grams(words, n):
        return [b"".join(words[i: i + n]) for i in range(len(words) - n + 1)]

    def find_top_duplicate(x):
        counter = Counter(x)
        top_n_gram = counter.most_common(1)[0]
        return top_n_gram

    doc_type = 'normal'
    info = {}
    bytes_len = len(text.encode('utf-8'))

    top_n_grams = ((1, 0.3), (2, 0.2), (3, 0.18), (4, 0.16))
    top_n_grams = ((1, 0.8), (2, 0.8), (3, 0.8), (4, 0.8))
    for n, n_frac in top_n_grams:
        n_grams = get_n_grams(words, n)
        if not n_grams:
            continue
        top_n_grams, top_n_grams_freq = find_top_duplicate(n_grams)
        top_char_length = len(top_n_grams) * top_n_grams_freq
        ratio = (top_char_length / bytes_len) if bytes_len else 0
        info[f"top_{n}_grams_ratio"] = ratio
        info[f"top_{n}_grams_ratio_th"] = n_frac
        info[f"top_{n}_grams"] = [top_n_grams_freq, top_n_grams.decode('utf-8', errors='replace')]
        if ratio > n_frac:
            doc_type = f"top_{n}_grams_ratio"

    def find_all_duplicate(words, n):
        n_words = len(words)
        unique = set()
        repeated_chars, idx = 0, 0
        counter = defaultdict(lambda: 1)
        while idx < n_words - n + 1:
            n_gram = b"".join(words[idx: idx + n])
            if n_gram in unique:
                repeated_chars += len(n_gram)
                idx += n
                counter[n_gram.decode('utf-8', errors='replace')] += 1
            else:
                unique.add(n_gram)
                idx += 1
        assert repeated_chars <= len(b"".join(words))
        return repeated_chars, counter

    # dup_n_grams = ((5, 0.12), (6, 0.12), (7, 0.11), (8, 0.11), (9, 0.11), (10, 0.10))
    dup_n_grams = ((5, 0.55), (6, 0.55), (7, 0.55), (8, 0.55), (9, 0.55), (10, 0.55))
    for n, n_frac in dup_n_grams:
        duplicate_n_grams_length, duplicate_n_grams_freq = find_all_duplicate(words, n)
        ratio = (duplicate_n_grams_length / bytes_len) if bytes_len else 0
        info[f"duplicate_{n}_grams_ratio"] = ratio
        info[f"duplicate_{n}_grams_ratio_th"] = n_frac
        info[f"duplicate_{n}_grams"] = duplicate_n_grams_freq
        if ratio > n_frac:
            doc_type = f"duplicate_{n}_grams_ratio"
    return doc_type, info 


def is_punctuation_ratio_too_high(text, threshold=0.3):
    punctuation_pattern = re.compile(r'[，。、：；！？,\.!?:;…．\"„”“’～—％]')
    punctuation_count = len(re.findall(punctuation_pattern, text))
    total_characters = len(text)
    punctuation_ratio = punctuation_count / total_characters if total_characters > 0 else 0
    return punctuation_ratio > threshold

total_num = 0 
invalid_punctuation_num = 0
invalid_lang_num = 0
invalid_ngram_num = 0
repeated_num = 0

for line in stdin:
    md5_set = set()
    total_num += 1
    line = line.rstrip('\n')
    line_json = json.loads(line)
    final_type = 'normal'
    final_info = {}
    
    for conversation in line_json['data']:
        question = conversation['question']
        
        # 检测标点符号
        if is_punctuation_ratio_too_high(question) or not question:
            print(f"Too many punctuation: {question}")
            invalid_punctuation_num += 1
            print('#'*50)
            break
        
        # 语言检测
        lang, score = filter_by_language(question)
        if not lang:
            print(f"Invalid lang: {question}")
            invalid_lang_num += 1
            print('#'*50)
            break
        
        # n-gram检测
        tokenized_bytes = text2token(question)
        cur_final_type, tmp_info = get_repetition_n_gram_ratio(question, tokenized_bytes)
        if cur_final_type != 'normal':
            print(f'Invalid n-gram ratio:{cur_final_type}')
            print(tmp_info)
            print(question)
            print('#'*50)
            invalid_ngram_num += 1
            break
        
        # 重复query检测
        question = ModifyingDocuments.normalization(question, remove_non_printing_characters=True, strip=True,
                                                    lower_case=True, uniform_whitespace=True,
                                                    replace_digits_with_zeros=False,
                                                    replace_unicode_punctuation=True)
        md5 = hashlib.md5(question.encode(encoding='utf-8')).hexdigest()
        if md5 not in md5_set:
            md5_set.add(md5)
        else:
            print(f'Invalid repeated questions')
            print(line)
            print('#'*50)
            repeated_num += 1
            break


print(f'total_num: {total_num}')
print(f'invalid_punctuation_num: {invalid_punctuation_num}')
print(f'invalid_lang_num: {invalid_lang_num}')
print(f'invalid_ngram_num: {invalid_ngram_num}')
print(f'repeated_num: {repeated_num}')
