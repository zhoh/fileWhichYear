import os
import shutil
import sys
from datetime import datetime

import piexif
from PIL import Image
from pillow_heif import register_heif_opener

LOG_FILE_NAME = f'move_files_{datetime.now().strftime("%Y%m%d-%H%M%S")}.log'

# 注册HEIF格式的 opener
# 为 PIL 提供 HEIF 格式的支持
register_heif_opener()

def get_file_date (file_path):
    """
    获取文件的日期，优先使用照片拍摄日期，文件创建日期兜底
    """
    # 先用文件创建时间来兜底
    if sys.platform.startswith("darwin"):
        creation_time = datetime.fromtimestamp(os.stat(file_path).st_birthtime)
    else:
        creation_time = datetime.fromtimestamp(os.path.getctime(file_path))
    # 如果是图片则优先使用拍摄日期
    try:
        if file_path.lower().endswith(('.jpg', '.jpeg', '.heif', '.heic')):
            image = Image.open(file_path)
            exif_dict = piexif.load(image.info['exif'])
            date_str = exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal].decode('utf-8')
            date_str = date_str.replace('上午', '').replace('下午', '')
            try:
                creation_time = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
            except ValueError:
                creation_time = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    except (KeyError, AttributeError, ValueError, OSError) as e:
        # 出现异常还是继续使用文件创建日期
        print(f'图片文件 {file_path} 无Exif或Exif中无拍摄信息，使用文件创建时间 {creation_time} 处理。原因：{e}')
    return creation_time

def create_target_folder(user_destination_folder, year, month, user_mode_option):
    """
    创建目标文件夹并返回path
    """
    if user_mode_option == 'year':
        year_folder = os.path.join(user_destination_folder, str(year))
        os.makedirs(year_folder, exist_ok=True)
        return year_folder
    elif user_mode_option == 'year_month':
        year_folder = os.path.join(user_destination_folder, str(year))
        month_folder = os.path.join(year_folder, str(month).zfill(2))
        os.makedirs(year_folder, exist_ok=True)
        os.makedirs(month_folder, exist_ok=True)
        return month_folder

def process_file(file_path, file, user_destination_folder, user_mode_option, log_file):
    """
    处理文件
    """
    try:
        # 获取文件日期信息
        creation_time = get_file_date(file_path)
        year = creation_time.year
        month = creation_time.month

        # 目标文件
        target_folder = create_target_folder(user_destination_folder, year, month, user_mode_option)
        target_file_path = os.path.join(target_folder, file)
        if os.path.exists(target_file_path):
            log_entry = f"【跳过】 {file_path} 的目标文件 {target_file_path} 已存在，跳过移动操作。\n"
            log_file.write(log_entry)
            print(f"【跳过】 {file_path} 的目标文件 {target_file_path} 已存在，跳过")
            return False
        else:
            log_entry = f"【成功】 {file_path} 移动到 {target_file_path}\n"
            log_file.write(log_entry)
            print(f"【成功】 {file_path} 移动到 {target_file_path}")
            shutil.move(file_path, target_file_path)
            return True
    except (OSError, shutil.Error) as e:
        log_entry = f"【异常】 {file_path} 处理异常，跳过。异常原因: {e}\n"
        log_file.write(log_entry)
        print(f"【异常】 {file_path} 处理异常，跳过。异常原因: {e}")
        return False

def move_files_by_year_month(user_source_folder, user_destination_folder, user_mode_option, user_scope_option):
    # 确保目标文件夹存在
    os.makedirs(user_destination_folder, exist_ok=True)

    # 遍历源文件夹及其所有嵌套子文件夹
    total_count = 0
    success_count = 0
    log_file_path = os.path.join(os.getcwd(), LOG_FILE_NAME)
    with open(log_file_path, 'w') as log_file:
        if user_scope_option == 'allFiles':
            for root, dirs, files in os.walk(user_source_folder):
                for file in files:
                    # 忽略掉一些常见的系统自动生成的非目标文件
                    if file == '.DS_Store' or file == 'Thumbs.db' or file == 'Desktop.ini':
                        continue
                    # 源文件路径
                    file_path = os.path.join(root, file)
                    # 处理文件
                    total_count += 1
                    if process_file(file_path, file, user_destination_folder, user_mode_option, log_file):
                        success_count += 1
        elif user_scope_option == 'subFiles':
            # 只遍历源文件夹下的直接子文件，不进入子文件夹
            for file in os.listdir(user_source_folder):
                file_path = os.path.join(user_source_folder, file)
                if os.path.isfile(file_path):
                    # 忽略掉一些常见的系统自动生成的非目标文件
                    if file == '.DS_Store' or file == 'Thumbs.db' or file == 'Desktop.ini':
                        continue
                    # 处理文件
                    total_count += 1
                    if process_file(file_path, file, user_destination_folder, user_mode_option, log_file):
                        success_count += 1
        else:
            print('处理范围模式入参有误，请确认。')
        print(f'共处理文件：{total_count} | 成功：{success_count} | 失败：{total_count - success_count} | 移动日志请查看：{log_file_path}')

if __name__ == "__main__":
    # 获取分类模式
    print("请选择目标文件分类方式：")
    print("1. 按照年份文件夹（年）")
    print("2. 按照年份+月份文件夹（年 + 月）")
    mode_choice = input("请输入你的选择（1 or 2）：")
    if mode_choice == "1":
        mode_option = "year"
    elif mode_choice == "2":
        mode_option = "year_month"
    else:
        print("无效的选择，请重新运行。")
        exit()

    # 获取源文件夹地址
    print("请输入待处理文件夹路径（可拖入文件夹获取地址）：")
    source_folder = input()
    source_folder = str.strip(source_folder).replace(r"\ ", " ")
    if not os.path.exists(source_folder):
        print("无效的文件夹路径，请重新运行")
        exit()

    # 确定源文件夹处理的范围
    print("请选择待处理文件夹中文件处理范围")
    print("1. 处理待处理文件夹中所有文件，包括所有子孙文件夹下的文件（推荐）")
    print("2. 只处理待处理文件夹中的文件，忽略子孙文件夹下的文件（适用于增量）")
    scope_choice = input("请输入你的选择（1 or 2）：")
    if scope_choice == "1":
        scope_option = "allFiles"
    elif scope_choice == "2":
        scope_option = "subFiles"
    else:
        print("无效的选择，请重新运行。")
        exit()

    # 获取目标文件夹地址
    print("请输入目标文件夹路径（可拖入文件夹获取地址）：")
    destination_folder = input()
    destination_folder = str.strip(destination_folder).replace(r"\ ", " ")
    os.makedirs(destination_folder, exist_ok=True)

    # 执行逻辑
    move_files_by_year_month(source_folder, destination_folder, mode_option, scope_option)