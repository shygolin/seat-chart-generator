import sys
import os

# 添加项目目录到 Python 路径
# PythonAnywhere 会自动设置 WSGI 工作目录为项目目录
project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

from server import app as application