#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import time
from datetime import datetime
import piexif
from piexif import helper
import shutil
from pathlib import Path


def process_wechat_files(folder_path):
    """
    Process WeChat photos and videos in the given folder.
    Set creation and modification time based on the timestamp in filename.
    """
    if not os.path.isdir(folder_path):
        print(f"错误: 路径 '{folder_path}' 不是一个有效的文件夹")
        return

    # 统计信息
    total_files = 0
    processed_files = 0
    skipped_files = 0
    failed_files = 0
    
    # 正则表达式匹配 "wx_camera_TIMESTAMP.jpg/mp4" 格式的文件
    pattern = re.compile(r'wx_camera_(\d+)\.(jpg|jpeg|mp4|png)$', re.IGNORECASE)
    
    # 遍历文件夹中的所有文件
    for filename in os.listdir(folder_path):
        total_files += 1
        file_path = os.path.join(folder_path, filename)
        
        # 跳过文件夹
        if os.path.isdir(file_path):
            skipped_files += 1
            continue
        
        # 匹配文件名
        match = pattern.match(filename)
        if not match:
            print(f"跳过不匹配的文件: {filename}")
            skipped_files += 1
            continue
        
        try:
            # 提取时间戳并转换为秒
            timestamp_ms = int(match.group(1))
            timestamp_s = timestamp_ms / 1000  # 转换为秒
            
            # 设置文件的创建和修改时间
            os.utime(file_path, (timestamp_s, timestamp_s))
            
            # 如果是照片，还要设置EXIF数据
            file_ext = match.group(2).lower()
            if file_ext in ['jpg', 'jpeg', 'png']:
                try:
                    set_exif_date(file_path, timestamp_s)
                except Exception as e:
                    print(f"设置EXIF数据失败: {filename}, 错误: {e}")
            
            print(f"已处理文件: {filename}")
            processed_files += 1
            
        except Exception as e:
            print(f"处理文件 {filename} 时出错: {e}")
            failed_files += 1
    
    # 打印处理结果
    print("\n处理结果摘要:")
    print(f"总文件数: {total_files}")
    print(f"成功处理: {processed_files}")
    print(f"跳过的文件: {skipped_files}")
    print(f"处理失败: {failed_files}")


def set_exif_date(image_path, timestamp):
    """设置图片的EXIF日期信息"""
    try:
        # 转换时间戳为datetime对象
        dt = datetime.fromtimestamp(timestamp)
        # 格式化为EXIF日期时间字符串: YYYY:MM:DD HH:MM:SS
        date_str = dt.strftime("%Y:%m:%d %H:%M:%S")
        
        # 读取现有的EXIF数据
        try:
            exif_dict = piexif.load(image_path)
        except:
            # 如果没有EXIF数据，创建一个新的
            exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
        
        # 设置各种日期时间标签
        exif_dict["0th"][piexif.ImageIFD.DateTime] = date_str
        exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = date_str
        exif_dict["Exif"][piexif.ExifIFD.DateTimeDigitized] = date_str
        
        # 将EXIF数据写回图片
        exif_bytes = piexif.dump(exif_dict)
        piexif.insert(exif_bytes, image_path)
    except Exception as e:
        raise Exception(f"设置EXIF日期失败: {e}")


def main():
    print("微信文件时间批处理工具")
    print("------------------------")
    folder_path = input("请输入微信文件所在的文件夹路径: ")
    
    # 验证路径是否存在
    if not os.path.exists(folder_path):
        print(f"错误: 路径 '{folder_path}' 不存在")
        return
    
    # 确认用户输入
    print(f"\n将处理文件夹: {folder_path}")
    confirm = input("是否继续? (y/n): ")
    if confirm.lower() != 'y':
        print("操作已取消")
        return
    
    process_wechat_files(folder_path)


if __name__ == "__main__":
    main()
