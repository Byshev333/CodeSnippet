#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''=================================================
@Author  :   baixue
@Date    :   2024/08/05 15:41:44
@Desc    :   迭代搜索关键词
此脚本的目的是：从百度文库网页中迭代搜索关键，比如先用“试题”去搜到一大堆结果，对这些结果做分词，统计词频，可能还能发现高频的“小学”、“初中”之类的词，然后再加入到搜索词里头，迭代几轮，构成较完整的关键词库
================================================='''
import json
import requests
from bs4 import BeautifulSoup
import re
import jieba
from collections import defaultdict
import time
import random
import traceback
import sys


def custom_keywords():
    ceval_subjects = ['注册电气工程师', '注册计量', '环境影响评价工程师', '注册城乡规划师', '注册消防工程师', '医师资格', '税务师', '注册会计师', '公务员', '导游资格', '法律职业资格', '教师资格',
                        '大学编程', '计算机组成', '操作系统', '计算机网络', '离散数学', '概率统计', '高等数学', '大学化学', '大学物理', '兽医学', '临床医学', '基础医学', '植物保护', '体育学', '艺术学', '中国语言文学', '法学', '逻辑学', '思想道德修养与法律基础', '近代史纲要', '工商管理', '毛泽东思想和中国特色社会主义理论体系概论', '马克思主义基本原理', '大学经济学', '教育学',
                        '高中生物', '高中化学', '高中物理', '高中数学', '高中地理', '高中政治', '高中语文', '高中历史',
                        '初中化学', '初中物理', '初中生物', '初中数学', '初中地理', '初中政治', '初中历史']

    cmmlu_subjects = ['商业伦理学', '经济学', '教育学', '大学教育学', '新闻学', 
                        '市场营销学', '专业会计学', '专业心理学', '公共关系学', '安全研究学', 
                        '高中地理', '管理学', '社会学', '电气工程', '工程水文学',
                        '天文学', '精算学', '遗传学', '大学数学', '医学统计', 
                        '病毒学', '计算机科学', '概念物理学', '解剖学', '机器学习',
                        '高中物理', '高中数学', '高中化学', '高中生物', '初等数学',
                        '法律与道德基础', '计算机安全', '食品科学', '大学医学', '临床',
                        '专业医学', '人类性行为', '农学', '体育学', '营养学', 
                        '小学信息技术', '马克思主义理论', '大学法律', '全球事实', '国际法学', 
                        '法理学', '世界宗教', '逻辑学', '专业法', '哲学', 
                        '世界历史', '艺术学']

    supplement_subjects = ['小学数学', '小学语文', '初中语文', '考研', 'c语言', 'c++', 'c#', 'java', 'javascript', 'python', 'swift', 'go', 'ruby', '编程', 'cet4', 'cet6', '英语专业八级', 'gre', 'gmat', '奥数', '化学竞赛', '物理竞赛', '生物竞赛']
    sources = [ceval_subjects, cmmlu_subjects, supplement_subjects]
    keywords = set()
    for source in sources:
        for subject in source:
            if subject in ['全球事实']:
                keywords.add(subject)
            else:
                if subject in ['考研', 'cet4', 'cet6', '英语专业八级', 'gre', 'gmat']:
                    pass
                else:
                    keywords.add(subject + '基础知识')

                keywords.add(subject + '习题')
                keywords.add(subject + '试题')
                keywords.add(subject + '真题')

    keywords.add("高考试题及答案")
    keywords.add("高考真题及答案")
    keywords.add("中考试题及答案")
    keywords.add("中考真题及答案")
    keywords.add("雅思考试")
    keywords.add("托福考试")
    keywords.add("司法考试")
    keywords.add("行测考试")

    with open('keywors.json', 'w') as fw:
        json.dump(sorted(list(keywords)), fw, indent=4, ensure_ascii=False)
    
    return keywords


def get_one_page_info(url):
    keywords = []
    response = requests.get(url)

    # 确保请求成功
    if response.status_code == 200:
        html_content = response.text
        soup = BeautifulSoup(html_content, 'lxml')
        
        # 使用正则表达式提取JavaScript中的JSON数据
        script_content = soup.find_all("script")[2].decode_contents()
        json_data_match = re.search(r'window\.pageData\s*=\s*(\{.*?\});', script_content, re.DOTALL)
        
        if json_data_match:
            json_data = json_data_match.group(1)
            data = json.loads(json_data)
            
            # 提取title和tagList
            items = data['sulaData']['__sula_prefetchData']['items']['PCSearch']['result']['items']
            for item in items:
                title = item['data']['title']
                tag_list = item['data']['tagList']
                
                # 去除HTML标签并分词
                clean_title = re.sub(r'<[^>]+>', '', title)
                seg_list = jieba.lcut(clean_title)
                keywords.extend(seg_list)
                keywords.extend(tag_list)

        else:
            print("No JSON data found in the script content.")
    else:
        print("Failed to retrieve the webpage")
    
    return keywords


def get_keywords_by_snowball(base_url):
    keywords_dict = defaultdict(int)
    
    for i in range(0, 500):
        print(i)
        second = random.randint(0, 3)  
        time.sleep(second)
        try:
            url = base_url + str(i)
            for word in get_one_page_info(url):
                keywords_dict[word] += 1
        except Exception as e:
            traceback.print_exc()
            print(f"Fail {i}")
            continue
    sorted_keywords_dict = dict(sorted(keywords_dict.items(), key=lambda item: item[1], reverse=True))
    
    return sorted_keywords_dict


if __name__ == '__main__':

    
    if sys.argv[1] == '1':

        base_url = 'https://wenku.baidu.com/search?word=%E8%AF%95%E9%A2%98&searchType=0&lm=0&od=0&fr=search&ie=utf-8&_wkts_=1722860671857&wkQuery=%E8%80%83%E8%AF%95&pn='

        base_url = 'https://wenku.baidu.com/search?word=%E7%AD%94%E6%A1%88&_wkts_=1722913507931&searchType=0&pn='
        base_url = 'https://wenku.baidu.com/search?word=%E7%9C%9F%E9%A2%98&_wkts_=1722915886546&searchType=0&pn='
        base_url = 'https://wenku.baidu.com/search?word=%E4%B9%A0%E9%A2%98&_wkts_=1722916050421&searchType=0&pn='
        sorted_keywords_dict = get_keywords_by_snowball(base_url)
        print(sorted_keywords_dict)
        # with open('shiti.json', 'w') as fw:
        #     json.dump(sorted_keywords_dict, fw, indent=4, ensure_ascii=False)
        # with open('daan.json', 'w') as fw:
        #     json.dump(sorted_keywords_dict, fw, indent=4, ensure_ascii=False)
        # with open('zhenti.json', 'w') as fw:
        #     json.dump(sorted_keywords_dict, fw, indent=4, ensure_ascii=False)
        
        with open('xiti.json', 'w') as fw:
            json.dump(sorted_keywords_dict, fw, indent=4, ensure_ascii=False)

    if sys.argv[1] == '2':
        cities = [
        "北京市", "扬州市", "沙岗子小学", "信阳市", "西安市未央区", "西安市", "长沙市", 
        "苏州市", "江苏省苏州市", "哈尔滨市", "邯郸市", "青岛科技大学", "黑龙江省", 
        "九江市", "厦门市", "湖北省", "湖南省长沙市", "南京外国语学校", "武汉外校", 
        "黑龙江", "宜宾职业技术学院", "云南省", "泰安市", "盘锦市", "德阳市", "重庆市", 
        "江西省", "广州市", "广东省广州市", "西沙群岛", "荷花淀", "荷花淀派", "未央区", "东城区", "河北", "北京", "山东", "江苏", "海淀区", "广东", "美国", "四川", "河南", "天津"
        ]
        prepositions = ["and", "关于", "以及", "about", "there", "here"]
        invalues_words = cities + prepositions + ['推荐', 'what', '天姥吟', '梦游天姥吟留别', "xxx", "...", "new", "ip地址", "错误码", "志愿者", "三个臭皮匠", "努学习", "工作表", "母版页", "下拉菜单", "牵大手", "百度", "--", "doc", "老师", "docx", "少先队", "上海大学", "pptx", "青铜葵花", '判断', "主观", "客观", "选择", "填空", "打印", "分数线", "完整", "招聘", "句子", "内能", "听力", "及其", "字数统计", "答题卡", "最新", "整理", "报录", "问题", "质点", "公倍数", "质量", "转动惯量", "运动", "文档", "过去", "word", "excel", "二真题"]
        dest_dic = {}
        dest_dic_new = {}
        with open('xiti.json', 'r') as fr_xiti, open('shiti.json', 'r') as fr_shiti, open('zhenti.json', 'r') as fr_zhenti:
            xiti = json.load(fr_xiti)
            shiti = json.load(fr_shiti)
            zhenti = json.load(fr_zhenti)
        
        with open('keywords.json', 'r') as fr_keyword:
            keywords = json.load(fr_keyword)

        for source in [xiti, shiti, zhenti]:
            for key, value in source.items():
                if key in dest_dic:
                    dest_dic[key] += value
                else:
                    dest_dic[key] = value

        for key, value in dest_dic.items():
            key = key.lower()
            if len(key) == 1:
                continue
            if re.search(r'[\d.]+', key):
                continue
            if int(value) < 5:
                continue
                # if len(key) < 3:
                #     continue
            if key.lower() in set(invalues_words):
                continue
            if '招生' in key or '表' in key or '第' in key:
                continue
            if '市' in key or '省' in key:
                continue
            
            dest_dic_new[key] = value

        sorted_keywords = dict(sorted(dest_dic_new.items(), key=lambda item: item[1], reverse=True))
        res_set = set(list(keywords) + list(sorted_keywords.keys()))
        # print(res_set) 
        with open('res.json', 'w') as fw:
            json.dump(list(res_set), fw, indent=4, ensure_ascii=False)
            # json.dump(sorted_keywords, fw, indent=4, ensure_ascii=False)
        
        


