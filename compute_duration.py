# -*- coding:utf-8 -*-
# Author :Zcb

import os
from moviepy.editor import VideoFileClip

file_Dir = u"e:\\test"  # 加个u 是表示unicode 一般用在中文字符前
sum_time = 0


class FileCheck():
    def __init__(self):
        self.file_dir = file_Dir

    def get_fileSize(self, fileName):
        """
            获取文件大小
        """
        file_Byte = os.path.getsize(fileName)
        return self.sizeConvert(file_Byte)

    def get_file_Times(self, filename):
        """
            获取视频时长
        """
        global sum_time
        clip = VideoFileClip(filename)
        sum_time += clip.duration
        file_Times = self.timeConvert(clip.duration)
        clip.close()  # 可以防止程序因为文件过多而报错
        return file_Times

    def sizeConvert(self, size):  # 单位换算
        K, M, G = 1024, 1024**2, 1024**3
        if size >= G:
            return "{:.3f}G".format(size / G)
        elif size >= M:
            return "{:.3f}M".format(size / M)
        elif size >= K:
            return "{:.3f}K".format(size / K)
        else:
            return "{:.3f}Bytes".format(size)

    def timeConvert(self, size):  # 单位换算
        M, H = 60, 60**2
        if size < M:
            return "{:.3f}s".format(size)
        if size < H:
            return "{:}m{:.3f}s".format(int(size // M), size % M)
        else:
            hour = size // H
            min = size % H // M
            sec = size % H % M
            return "{}h{}m{:.3f}s".format(int(hour), int(min), sec)

    def get_all_file(self):
        """
            获取视频下的所有文件
        """
        ls_file = []
        for root, dirs, files in os.walk(file_Dir):
            for file in files:
                if "mp4" in file:  # 只添加mp4文件
                    ls_file.append(os.path.join(root, file))  # 当前路径下所有非目录子文件
        return ls_file


print("============开始，文件较多，请耐心等待...")
fc = FileCheck()

fc.get_all_file()
files = fc.get_all_file()
# print(files)  files 是放文件全名的列表
for file in files:
    file_size = fc.get_fileSize(file)
    file_times = fc.get_file_Times(file)
    print("{} {} {}".format(file, file_size, file_times))
print("总时长：{}h{}m{:.3f}s".format(int(sum_time / 3600), int(sum_time % 3600 // 60), sum_time % 3600 % 60))
