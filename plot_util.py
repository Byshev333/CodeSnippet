#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''=================================================
@Author  :   baixue
@Date    :   2023/01/30 19:44:45
@Desc    :   绘制相关图像
================================================='''

from sklearn.metrics import confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd

plt.rcParams["font.sans-serif"] = ["SimHei"]
plt.rcParams["font.family"] = "sans-serif"


def plot_confusion_matrix(pred_label, true_label, labels):
    """绘制混淆矩阵

    Args:
        pred_label (list): 预测标签
        true_label (list): 真实标签
        labels (list): 标签类别
    """    

    sns.set()
    f, ax = plt.subplots()
    cmap = sns.cm.rocket_r
    # cmap = plt.cm.Blues
    cm = confusion_matrix(true_label, pred_label)
    cm_normalized = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]  # np.newaxis用于增加维度
    sns.heatmap(cm_normalized, cmap=cmap, annot=True, ax=ax)
    ax.set_title('confusion matrix')
    ax.set_xlabel('Predicted label')
    ax.set_ylabel('True label')
    xlocations = np.array(range(len(labels)))
    ax.set_xticklabels(labels, fontproperties='SimHei')
    ax.set_yticklabels(labels, fontproperties='SimHei')


if __name__ == '__main__':
    # load labels.
    labels = ['宁静舒缓', '忧伤忧郁', '悬疑紧张', '激昂恢弘', '轻松欢快']
    invalid_labels = ['无背景音乐', '无法标注', '无法播放']

    input_file = './dataset/ad_all_photoid_results_ana_process.xlsx'
    df = pd.read_excel(input_file)
    df = df.fillna('')
    pred_label = []
    true_label = []
    for index, line in df.iterrows():
        if line['pred_label'] in invalid_labels:
            continue
        if line['true_label'] in invalid_labels:
            continue
        pred_label.append(line['pred_label'])
        true_label.append(line['true_label'])


    correct = (np.asarray(true_label) == np.asarray(pred_label)).sum()
    print('accuracy:', correct / len(true_label))

    plot_confusion_matrix(pred_label, true_label, labels)
