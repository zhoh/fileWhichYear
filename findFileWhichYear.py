import os
import shutil
import sys
from datetime import datetime
from PIL import Image
import piexif
from pillow_heif import register_heif_opener

# 注册HEIF格式的 opener
# 为 PIL 提供 HEIF 格式的支持
register_heif_opener()

SOURCE_FOLDER = './待处理'
DESTINATION_FOLDER = './完成处理'

def get_file_date (file_path):
    # 先用文件创建时间来兜底
    if sys.platform.startswith("darwin"):
        creation_time = datetime.fromtimestamp(os.stat(file_path).st_birthtime)
    else:
        creation_time = datetime.fromtimestamp(os.path.getctime(file_path))
    # 如果是图片则优先使用拍摄日期
    try:
        if file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.heif', '.heic')):
            image = Image.open(file_path)
            exif_dict = piexif.load(image.info['exif'])
            date_str = exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal].decode('utf-8')
            creation_time = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
    except (KeyError, AttributeError, ValueError, OSError) as e:
        # 出现异常还是继续使用文件创建日期
        print(f'图片文件 {file_path} 无Exif或Exif中无拍摄信息，使用文件创建时间 {creation_time} 处理。原因：{e}')
    return creation_time

def move_files_by_year(source_folder, destination_folder, user_option):
    # 确保目标文件夹存在
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)

    # 遍历源文件夹及其所有嵌套子文件夹
    for root, dirs, files in os.walk(source_folder):
        for file in files:
            try:
                # 忽略掉一些常见的系统自动生成的非目标文件
                if file == '.DS_Store' or file == 'Thumbs.db' or file == 'Desktop.ini':
                    continue
                file_path = os.path.join(root, file)
                creation_time = get_file_date(file_path)
                year = creation_time.year
                month = creation_time.month

                # 移动文件到对应的文件夹
                target_file_path = ''
                if user_option == 'year':
                    # 年维度
                    year_folder = os.path.join(destination_folder, str(year))
                    os.makedirs(year_folder, exist_ok=True)
                    target_file_path = os.path.join(year_folder, file)
                elif user_option == 'year_month':
                    # 年 + 月 维度
                    year_folder = os.path.join(destination_folder, str(year))
                    month_folder = os.path.join(year_folder, str(month).zfill(2)) # 不足2位补0
                    os.makedirs(year_folder, exist_ok=True)
                    os.makedirs(month_folder, exist_ok=True)
                    target_file_path = os.path.join(month_folder, file)

                # 检查目标文件是否已存在
                if os.path.exists(target_file_path):
                    # # 询问用户是否覆盖、重命名源文件等
                    # print(f"目标文件 {target_file_path} 已存在，是否覆盖？(y/n)")
                    # user_choice = input()
                    # if user_choice.lower() == 'y':
                    #     print(f"文件 {file_path} 移动到 {target_file_path}")
                    #     shutil.move(file_path, target_file_path)
                    # else:
                    #     print("移动操作取消")
                    print(f"目标文件 {target_file_path} 已存在，跳过")
                    continue
                else:
                    # print(f"文件 {file_path} 移动到 {target_file_path}")
                    shutil.move(file_path, target_file_path)
            except (OSError, shutil.Error) as e:
                print(f"文件 {file} 处理异常，跳过。异常原因: {e}")
                continue


if __name__ == "__main__":
    # 做一些初始化工作
    if not os.path.exists(SOURCE_FOLDER):
        print("文件不存在，请在 待处理 文件夹中放入要处理的文件")
        os.mkdir(SOURCE_FOLDER)
        exit()

    print("请选择目标文件分类方式：")
    print("1. 按照年份文件夹（年）")
    print("2. 按照年份+月份文件夹（年 + 月）")
    choice = input("请输入你的选择（1 or 2）：")

    if choice == "1":
        option = "year"
    elif choice == "2":
        option = "year_month"
    else:
        print("无效的选择，请重新运行。")
        exit()
    move_files_by_year(SOURCE_FOLDER, DESTINATION_FOLDER, option)