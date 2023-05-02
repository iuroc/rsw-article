import os, threading

def init_data_dir() -> str:
    '''初始化 data 目录，返回路径'''
    path = os.path.join(os.path.dirname(__file__), '..', 'data')
    if not os.path.exists(path):
        os.mkdir(path)
    return path

lock = threading.Lock()
sem = threading.Semaphore(100)