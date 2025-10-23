import os
import re
from datetime import datetime

def sanitize_filename(filename):
    """清理文件名，移除特殊字符"""
    # 替换特殊字符为下划线
    return re.sub(r'[^\w\.-]', '_', filename)

def get_current_time():
    """获取当前时间"""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def ensure_directory(directory):
    """确保目录存在，如果不存在则创建"""
    if not os.path.exists(directory):
        os.makedirs(directory)

def format_file_size(size_bytes):
    """格式化文件大小为人类可读格式"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"