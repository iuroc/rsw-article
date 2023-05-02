import json, os
from typing import List

base_url = 'http://www.rensheng5.com'  # 基础网址

# 从文件载入样本
list_urls: List[str] = json.load(
    open(os.path.dirname(__file__) + './list_urls.json', 'r')
)
