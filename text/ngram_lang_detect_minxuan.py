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
from tqdm import tqdm
from pathlib import Path

# 加载模型
model = fasttext.load_model('/nlp_group/baixue05/tools/lid.176.bin')

def detect_language(text):
    text = text.replace('\n', ' ').strip()
    predictions = model.predict(text, k=1)
    language = predictions[0][0].replace('__label__', '')
    probability = predictions[1][0]
    return language, probability

def filter_by_language(text, allowed_languages=('zh', 'en'), threshold=0.65):
    lang, prob = detect_language(text)
    if lang in allowed_languages:
        return lang, prob
    return None, None

# 初始化tokenizer
tokenizer = subprocess.Popen(['./detection/tokenizer_bin/cstokenizer', '--encode', './detection/tokenizer/tokenizer.model'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)

# 加载token映射
id2token = {}
token2id = {}
with open('./detection/tokenizer/tokenizer.model', encoding='utf-8-sig') as f:
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
    tk_j['text'] = text
    s = str(json.dumps(tk_j, ensure_ascii=False))
    tokenizer.stdin.write(s + "\n")
    tokenizer.stdin.flush()
    segs = tokenizer.stdout.readline().strip().split(',')
    segs = [int(one) for one in segs]
    pieces = [id2token[one] for one in segs]
    return pieces


def replace_multiple_rtl_marks(text):
    # 只替换字符串开头和结尾的多个 \u200f 为一个
    text = re.sub(r'(^[\u200f]+|[\u200f]+$)', '\u200f', text)
    text = re.sub(r'(^[\u200b]+|[\u200b]+$)', '\u200b', text)
    text = re.sub(r'(^[\u200c]+|[\u200c]+$)', '\u200c', text)
    text = re.sub(r'(^[\u200d]+|[\u200d]+$)', '\u200d', text)
    text = re.sub(r'(^[\u200e]+|[\u200e]+$)', '\u200e', text)
    return text


def get_repetition_n_gram_ratio(text, words):
    def get_n_grams(words, n):
        return [b"".join(words[i: i + n]) for i in range(len(words) - n + 1)]

    def find_top_duplicate(x):
        counter = Counter(x)
        top_n_gram = counter.most_common(1)[0]
        return top_n_gram

    doc_type = 'normal'
    info = {}
    bytes_len = len(text.encode('utf-8'))

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
        return repeated_chars, counter

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

def process_file(input_file, output_file):
    stats = {
        'total_num': 0,
        'filtered_num': 0,
        'saved_num': 0
    }
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(input_file, 'r', encoding='utf-8') as f_in, \
         open(output_file, 'w', encoding='utf-8') as f_out:
        
        for line in f_in:
            stats['total_num'] += 1
            try:
                line_json = json.loads(line.strip('\n'))
                clean_conversations = []
                md5_set = set()
                is_valid = True
                
                for conversation in line_json['data']:
                    question = conversation['question']
                    answer = conversation['answer']
                    
                    # 清洗RTL标记
                    question = replace_multiple_rtl_marks(question)
                    answer = replace_multiple_rtl_marks(answer)
                    
                    # 检查标点符号比例
                    if is_punctuation_ratio_too_high(question) or not question:
                        is_valid = False
                        break
                    
                    # 检查语言
                    lang, score = filter_by_language(question)
                    if not lang:
                        is_valid = False
                        break
                    
                    # 检查n-gram重复
                    tokenized_bytes = text2token(question)
                    cur_final_type, _ = get_repetition_n_gram_ratio(question, tokenized_bytes)
                    if cur_final_type != 'normal':
                        is_valid = False
                        break
                    
                    # 标准化问题文本
                    question = ModifyingDocuments.normalization(
                        question,
                        remove_non_printing_characters=True,
                        strip=True,
                        lower_case=True,
                        uniform_whitespace=True,
                        replace_digits_with_zeros=False,
                        replace_unicode_punctuation=True
                    )
                    
                    # 检查重复
                    md5 = hashlib.md5(question.encode(encoding='utf-8')).hexdigest()
                    if md5 in md5_set:
                        is_valid = False
                        break
                    md5_set.add(md5)
                    
                    # 更新清洗后的问题
                    conversation['question'] = question
                    conversation['answer'] = answer
                    clean_conversations.append(conversation)
                
                if is_valid and clean_conversations:
                    line_json['data'] = clean_conversations
                    f_out.write(json.dumps(line_json, ensure_ascii=False) + '\n')
                    stats['saved_num'] += 1
                else:
                    stats['filtered_num'] += 1
                    
            except json.JSONDecodeError:
                print(f"Error decoding JSON in file {input_file}")
                stats['filtered_num'] += 1
                continue
            except Exception as e:
                print(f"Error processing line in file {input_file}: {str(e)}")
                stats['filtered_num'] += 1
                continue
                
    return stats

def process_directory(input_dir, output_dir):
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    
    # 获取所有jsonl文件
    files = list(input_dir.glob('**/*.jsonl'))
    print(f"Found {len(files)} files to process")
    
    total_stats = {
        'total_num': 0,
        'filtered_num': 0,
        'saved_num': 0
    }
    
    # 处理每个文件
    for input_file in tqdm(files, desc="Processing files"):
        # 构建输出文件路径，保持相对路径结构
        relative_path = input_file.relative_to(input_dir)
        output_file = output_dir / relative_path
        
        print(f"\nProcessing: {input_file} -> {output_file}")
        
        try:
            stats = process_file(input_file, output_file)
            
            # 更新总统计信息
            for key in total_stats:
                total_stats[key] += stats[key]
            
            # 打印当前文件的统计信息
            print(f"Results for {input_file}:")
            print(f"Total documents: {stats['total_num']}")
            print(f"Filtered documents: {stats['filtered_num']}")
            print(f"Saved documents: {stats['saved_num']}")
            print("-" * 50)
                
        except Exception as e:
            print(f"Error processing file {input_file}: {str(e)}")
            continue
    
    # 打印总统计信息
    print("\nOverall Statistics:")
    print(f"Total documents processed: {total_stats['total_num']}")
    print(f"Total documents filtered: {total_stats['filtered_num']}")
    print(f"Total documents saved: {total_stats['saved_num']}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <input_directory> <output_directory>")
        sys.exit(1)
        
    input_dir = sys.argv[1]
    output_dir = sys.argv[2]
    
    if not os.path.isdir(input_dir):
        print(f"Error: {input_dir} is not a valid directory")
        sys.exit(1)
        
    process_directory(input_dir, output_dir)