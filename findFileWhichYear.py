import os
import shutil
from datetime import datetime
import exifread

SOURCE_FOLDER = './待处理'
DESTINATION_FOLDER = './完成处理'

def move_files_by_year(source_folder, destination_folder):
    # 确保目标文件夹存在
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)

    # 遍历源文件夹及其所有嵌套子文件夹
    for root, dirs, files in os.walk(source_folder):
        for file in files:
            file_path = os.path.join(root, file)

            year = None
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.heif', '.heic')):
                try:
                    with open(file_path, 'rb') as f:
                        tags = exifread.read_exif(f)
                        if 'EXIF DateTimeOriginal' in tags:
                            date_str = tags['EXIF DateTimeOriginal'].values
                            year = int(date_str.split(':')[0])
                except (KeyError, AttributeError, ValueError, OSError):
                    # 如果无法从EXIF获取年份，使用文件创建时间
                    creation_time = datetime.fromtimestamp(os.path.getctime(file_path))
                    year = creation_time.year
            else:
                # 对于非图片文件，直接使用文件创建时间获取年份
                creation_time = datetime.fromtimestamp(os.path.getctime(file_path))
                year = creation_time.year

            # 创建对应年份的文件夹（如果不存在）
            year_folder = os.path.join(destination_folder, str(year))
            if not os.path.exists(year_folder):
                os.makedirs(year_folder)

            # 移动文件到对应年份的文件夹
            shutil.move(file_path, os.path.join(year_folder, file))

        # 检查当前子文件夹是否为空，如果为空则删除
        if not files:
            try:
                os.rmdir(root)
            except OSError as e:
                print(f"删除子文件夹 {root} 时出错: {e}")


if __name__ == "__main__":
    # 做一些初始化工作
    if not os.path.exists(SOURCE_FOLDER):
        print(f"文件不存在，请在 待处理 文件夹中放入要处理的文件")
        os.mkdir(SOURCE_FOLDER)
        exit()
    move_files_by_year(SOURCE_FOLDER, DESTINATION_FOLDER)