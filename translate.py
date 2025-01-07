#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''=================================================
@Author  :   baixue
@Date    :   2025/01/07 11:27:48
@Desc    :   翻译接口调用
================================================='''


from pygtrans import Translate
import argparse
import json
import pandas as pd

# client = Translate(target='zh-CN', proxies={'https': 'http://localhost:10809'})
client = Translate(target='zh-CN', proxies={'https': 'http://oversea-squid2.ko.txyun:11080'})


def example():
    # 批量翻译
    texts = client.translate([
        'Good morning. What can I do for you?',
        'Read aloud and underline the sentences about booking a flight.',
        'May I have your name and telephone number?'
    ])

    for text in texts:
        print(text.translatedText)
        print(text.detectedSourceLanguage)


def trans_batch(input, output):
    texts = []
    texts_trans = []
    scores_bx = []
    scores_sz = []

    with open(input, 'r') as fr:
        for line in fr:
            line = line.rstrip('\n')
            line = line.split('\x01')
            try:
                content = json.loads(line[4])['content']
                score_bx = line[6]
                score_sz = line[7]
                # 翻译文本
                texts.append(content)
                translated_text = client.translate([content])[0].translatedText
                texts_trans.append(translated_text)
                scores_bx.append(score_bx)
                scores_sz.append(score_sz)
            except IndexError as e:
                print(f"Error processing line: {line}. Error: {e}")

        data_dict = {'texts': texts, 'texts_trans': texts_trans, 'scores_bx': scores_bx, 'scores_sz': scores_sz}
        df = pd.DataFrame(data_dict)
        df.to_excel(output, index=False)


def main():
    parser = argparse.ArgumentParser(description='通过GPT对CC数据进行分类')
    parser.add_argument('input', help='输入文件路径')
    parser.add_argument('output', help='输出文件路径')

    args = parser.parse_args()
    trans_batch(args.input, args.output)


if __name__ == '__main__':
    main()
