import sys
import os

# 添加项目目录到 Python 路径
project_home = '/home/你的用戶名/mysite'  # 部署時需要修改成你的實際路徑
if project_home not in sys.path:
    sys.path.insert(0, project_home)

from server import app as application