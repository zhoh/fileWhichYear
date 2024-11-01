import os
import shutil
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
    creation_time = datetime.fromtimestamp(os.path.getctime(file_path))
    # 如果是图片则优先使用拍摄日期
    try:
        if file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.heif', '.heic')):
            image = Image.open(file_path)
            exif_dict = piexif.load(image.info['exif'])
            date_str = exif_dict['Exif'][36867].decode('utf-8')
            creation_time = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
    except (KeyError, AttributeError, ValueError, OSError):
        # 出现异常还是继续使用文件创建日期
        creation_time = datetime.fromtimestamp(os.path.getctime(file_path))
    return creation_time

def move_files_by_year(source_folder, destination_folder):
    # 确保目标文件夹存在
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)

    # 遍历源文件夹及其所有嵌套子文件夹
    for root, dirs, files in os.walk(source_folder):
        for file in files:
            if file == '.DS_Store' or file == 'Thumbs.db' or file == 'Desktop.ini':
                continue
            file_path = os.path.join(root, file)
            creation_time = get_file_date(file_path)
            year = creation_time.year

            # 创建对应年份的文件夹（如果不存在）
            year_folder = os.path.join(destination_folder, str(year))
            if not os.path.exists(year_folder):
                os.makedirs(year_folder)

            # 移动文件到对应年份的文件夹
            target_file_path = os.path.join(year_folder, file)

            # 检查目标文件是否已存在
            if os.path.exists(target_file_path):
                # # 询问用户是否覆盖、重命名源文件等
                # print(f"目标文件 {target_file_path} 已存在，是否覆盖？(y/n)")
                # user_choice = input()
                # if user_choice.lower() == 'y':
                #     shutil.move(file_path, target_file_path)
                # else:
                #     print("移动操作取消")
                print(f"目标文件 {target_file_path} 已存在，跳过")
                continue
            else:
                shutil.move(file_path, target_file_path)


if __name__ == "__main__":
    # 做一些初始化工作
    if not os.path.exists(SOURCE_FOLDER):
        print(f"文件不存在，请在 待处理 文件夹中放入要处理的文件")
        os.mkdir(SOURCE_FOLDER)
        exit()
    move_files_by_year(SOURCE_FOLDER, DESTINATION_FOLDER)