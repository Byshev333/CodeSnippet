#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''=================================================
@Author  :   baixue
@Date    :   2025/01/07 11:23:48
@Desc    :   文本去重
================================================='''

import hashlib
import json
from simhash import Simhash
import jieba
import jieba.analyse
import re
from typing import Dict

non_printing_characters_re = re.compile(
    f"[{''.join(map(chr, list(range(0,32)) + list(range(127,160))))}]"
)

digits_re: re.Pattern = re.compile(r"\d")

unicode_punctuation: Dict[str, str] = {
    "，": ",",
    "。": ".",
    "、": ",",
    "„": '"',
    "”": '"',
    "“": '"',
    "«": '"',
    "»": '"',
    "１": '"',
    "」": '"',
    "「": '"',
    "《": '"',
    "》": '"',
    "´": "'",
    "∶": ":",
    "：": ":",
    "？": "?",
    "！": "!",
    "（": "(",
    "）": ")",
    "；": ";",
    "–": "-",
    "—": " - ",
    "．": ". ",
    "～": "~",
    "’": "'",
    "…": "...",
    "━": "-",
    "〈": "<",
    "〉": ">",
    "【": "[",
    "】": "]",
    "％": "%",
    "►": "-",
}

normalization = {
    "non_printing_characters_re": non_printing_characters_re,
    "digits_re": digits_re,
    "unicode_punctuation": unicode_punctuation,
}


class ModifyingDocuments:

    @staticmethod
    def remove_non_printing_characters(document, non_printing_characters_re):
        return non_printing_characters_re.sub("", document)

    @staticmethod
    def uniform_whitespace(
        document,
        whitespace=[
            " ",
            " ",
            " ",
            " ",
            " ",
            "　",
            " ",
            " ",
            " ",
            " ",
            "￼",
            "",
        ],
    ):
        """There are different whitespace characters."""
        whitespace = set(whitespace)
        document = "".join(
            [char if char not in whitespace else " " for char in document]
        )
        return document

    @staticmethod
    def replace_digits_with_zeros(document, digits_re):
        return digits_re.sub("0", document)

    @staticmethod
    def replace_unicode_punctuation(document, unicode_punctuation):
        return "".join(unicode_punctuation.get(c, c) for c in document)

    @staticmethod
    def normalization(
        document,
        remove_non_printing_characters,
        strip,
        lower_case,
        uniform_whitespace,
        replace_digits_with_zeros,
        replace_unicode_punctuation,
        non_printing_characters_re=normalization["non_printing_characters_re"],
        digits_re=normalization["digits_re"],
        unicode_punctuation=normalization["unicode_punctuation"],
    ):
        if remove_non_printing_characters:
            document = ModifyingDocuments.remove_non_printing_characters(
                document, non_printing_characters_re
            )
        if strip:
            document = document.strip()
        if not document:
            return document
        if lower_case:
            document = document.lower()
        if uniform_whitespace:
            document = ModifyingDocuments.uniform_whitespace(document)
        if replace_digits_with_zeros:
            document = ModifyingDocuments.replace_digits_with_zeros(document, digits_re)
        if replace_unicode_punctuation:
            document = ModifyingDocuments.replace_unicode_punctuation(
                document, unicode_punctuation
            )
        return document


class Cleaner:
    def __init__(self, jsons):
        self.jsons = jsons

    # 判断一个词是否是英文词
    def is_en_word(self, word):
        result = True
        word = word.strip() if word is not None else ''
        if len(word) == 0:
            return False
        for ch in word:
            result = result and self.is_alphabet(ch)
        return result

    # 判断一个unicode是否是数字
    def is_number(self, uchar):
        if u'\u0030' <= uchar <= u'\u0039':
            return True
        else:
            return False

    # 判断一个unicode是否是英文字母
    def is_alphabet(self, uchar):
        if (u'\u0041' <= uchar <= u'\u005a') or (u'\u0061' <= uchar <= u'\u007a'):
            return True
        else:
            return False

    # 判断一个unicode是否是中文
    def is_chinese(self, uchar):
        if u'\u4e00' <= uchar <= u'\u9fa5':
            return True
        else:
            return False

    def norm_content(self, content):
        content = ModifyingDocuments.normalization(content, remove_non_printing_characters=True, strip=True,
                                                   lower_case=True, uniform_whitespace=True,
                                                   replace_digits_with_zeros=True,
                                                   replace_unicode_punctuation=True)
        content = re.sub(r"[-+]?\d*\.\d+|\d+%|\d+", " 0 ", content)

        HTML_TABLE = 'table'
        HTML_UL = 'ul'
        HTML_OL = 'ol'
        HTML_PRE = 'pre'
        HTML_CODE = 'code'
        HTML_CAPTION = 'caption'
        HTML_TH = 'th'
        HTML_TR = 'tr'
        HTML_TD = 'td'
        HTML_LI = 'li'
        HTML_DL = 'dl'
        # 用来包含在输出里头的tag
        RESERVED_OUTPUT_TAGS = frozenset(
            {HTML_TABLE, HTML_UL, HTML_OL, HTML_PRE, HTML_CODE, HTML_CAPTION, HTML_TH, HTML_TR, HTML_TD, HTML_LI,
             HTML_DL})

        for tag in RESERVED_OUTPUT_TAGS:
            content = content.replace('<{0}>'.format(tag), ' ')
            content = content.replace('</{0}>'.format(tag), ' ')
        return content

    def get_code(self, j, k=5):
        # result could be array of string
        # 先取5gram
        def get_simhash(content):
            hashv = Simhash(f=128, value=jieba.analyse.extract_tags(content, topK=False, withWeight=True))
            hashv = str(hashv.value)
            return hashv

        def str_count2(str_):
            num = 0
            for s in str_:
                # 中文字符范围
                if self.is_chinese(s):
                    num += 1
                # elif u'0' <= s <= u'9':
                #     num += 1
                # 英文字符范围
                elif self.is_alphabet(s):
                    num += 1
            return num

        content = j['content']
        content = self.norm_content(content)

        md5 = hashlib.md5(content.encode(encoding='utf-8')).hexdigest()
        j['md5'] = md5

        split_content = list(jieba.cut(content))
        res = []
        for i in range(len(split_content)):
            if i + k <= len(split_content):
                span = ""
                for s in split_content[i:i + k]:
                    if self.is_chinese(s):
                        span += s
                    elif self.is_en_word(s) or self.is_number(s):
                        span += " "
                        span += s
                if str_count2(span) >= 1:
                    res.append(span)

            # 3000个k-gram，这块应该就是消耗内存的主要原因
            if len(res) > 3000:
                break
        j['simhash'] = get_simhash(content)

    def dedup_step(self, key):
        unique_keys = set()
        deduplicated_list = []

        for j in self.jsons:
            if j[key] not in unique_keys:
                unique_keys.add(j[key])
                deduplicated_list.append(j)

        self.jsons = deduplicated_list

    def clean(self):
        for j in self.jsons:
            self.get_code(j)

        self.dedup_step('md5')
        self.dedup_step('simhash')


if __name__ == '__main__':
    jsons = [json.loads(x.strip("\n")) for x in open("corpus.jl", "r", encoding='utf-8').readlines() if x]
    cleaner = Cleaner(jsons)
    cleaner.clean()
    for j in cleaner.jsons:
        print(json.dumps(j, ensure_ascii=False))
