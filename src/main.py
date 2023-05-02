import requests, re, os, threading, config, json, sqlite3
from typing import List, Tuple, Dict, Union
from check import get_list_urls
from html import unescape
from db import insert_article_db
from util import init_data_dir, lock, sem


def get_article_list(
    list_url: str, has_retry: int = 0, max_retry: int = 5
) -> List[Tuple[str, str]]:
    '''获取文章列表'''
    try:
        res = requests.get(list_url, timeout=2)
    except:
        has_retry += 1
        if has_retry > max_retry:
            return
        return get_article_list(list_url, has_retry)
    res_text = res.content.decode('gbk', 'ignore')
    try:
        ul_html = re.search(
            r'class="tleft".*?<ul.*?>(.*?)</ul>', res_text, re.DOTALL
        ).group(1)
    except:
        return print('get_article_list 正则解析错误：' + list_url)
    link_htmls = re.findall(r'href="(.*?)".*?>(.*?)<', ul_html, re.DOTALL)
    return link_htmls


def get_article(
    article_url: str, has_retry: int = 0, max_retry: int = 5
) -> Tuple[str, str, str]:
    '''获取文章数据'''
    try:
        res = requests.get(article_url, timeout=2)
    except:
        has_retry += 1
        if has_retry > 5:
            return
        # print(f'遇到错误，正在重试第 {has_retry} 次')
        return get_article(article_url, has_retry)
    res_text = res.content.decode('gbk', 'ignore')
    try:
        title = re.search(r'<h1>(.*?)</h1>', res_text).group(1)
        pattern = r'<div class="artbody">(.*?<p.*?>.*?)</div>'
        content = re.search(pattern, res_text, re.DOTALL).group(1)
        pattern = r'<div class="artinfo">.*?(\d{4}-\d{2}-\d{2})'
        time = re.search(pattern, res_text, re.DOTALL).group(1)
        types_html = re.search(
            r'<div class="weizhi">(.*?)</div>', res_text, re.DOTALL
        ).group(1)
    except:
        return print(f'get_article 正则解析错误：{article_url}')
    content = re.sub(r'<.*?>', '', content)
    content = unescape(content)
    types = re.findall(r'\'>(.*?)</a>', types_html)
    types.append('')
    main_type = types[1]
    sub_type = types[2]
    article_id = article_url
    return title, time, content, main_type, sub_type


def get_all_page_num(list_url: str, has_retry: int = 0, max_retry: int = 5) -> int:
    '''获取文章列表页的总页数'''
    try:
        res = requests.get(list_url, timeout=2)
    except:
        has_retry += 1
        if has_retry > max_retry:
            return
        print(f'遇到错误，正在重试第 {has_retry} 次：{list_url}')
        return get_all_page_num(list_url, has_retry)
    res_text = res.content.decode('gbk', 'ignore')
    page = re.search(r'<span class="pageinfo">.*?共.*?(\d+).*?页', res_text)
    page = page.group(1) if page else ''
    key = re.search(r'(list|index)_\d+.html', res_text)
    key = key.group(1) if key else ''
    return int(page), key


def thread_get_article_list(list_url: str, all_article_list, task_info):
    article_list = get_article_list(list_url)
    lock.acquire()
    task_info['finish'] += 1
    print(f'\r文章列表采集进度：{task_info["finish"]}/{task_info["all"]}', end='')
    all_article_list += article_list
    lock.release()
    sem.release()


def thread_get_all_article_list(list_urls: List[str]) -> List[Tuple[str, str]]:
    '''多线程获取所有文章列表'''
    threads = []
    all_article_list = []
    task_info = {'finish': 0, 'all': 0}
    for list_url in list_urls:
        all_page, key = get_all_page_num(list_url)
        print(f'页码载入完成，共 {all_page} 页')
        task_info['all'] += all_page
        for i in range(all_page):
            page = i + 1
            list_url_now = list_url
            if page > 1:
                list_url_now = f'{list_url}{key}_{page}.html'
            thread = threading.Thread(
                target=thread_get_article_list,
                args=(list_url_now, all_article_list),
                kwargs={'task_info': task_info},
            )
            threads.append(thread)
    for thread in threads:
        sem.acquire()
        thread.start()
    for thread in threads:
        thread.join()
    print()
    return all_article_list


def save_data(data, file_name: str):
    '''保存文件到 data 目录'''
    file_path = os.path.join(init_data_dir(), file_name)
    json.dump(
        data,
        open(file_path, 'w', encoding='utf-8'),
        indent=4,
        ensure_ascii=False,
    )
    print(f'文件保存成功：{os.path.abspath(file_path)}')


def get_data(file_name):
    path = os.path.join(os.path.dirname(__file__), '..', 'data')
    if not os.path.exists(path):
        os.mkdir(path)
    file_path = os.path.join(path, file_name)
    return json.load(open(file_path, 'r', encoding='utf-8'))


def thread_get_article(
    article_url: str,
    all_article_data: list,
    task_info: Dict[Union['finish', 'all'], int],
):
    article_data = get_article(article_url)
    lock.acquire()
    task_info['finish'] += 1
    print(f'\r文章内容采集进度：{task_info["finish"]}/{task_info["all"]}', end='')
    if article_data:
        all_article_data.append(article_data)
    lock.release()
    sem.release()


def thread_get_all_article(all_article_list: List[Tuple[str, str]]):
    '''多线程获取所有文章内容'''
    threads = []
    all_article_data = []
    task_info = {'finish': 0, 'all': len(all_article_list)}
    for article in all_article_list:
        article_url = article[0]
        thread = threading.Thread(
            target=thread_get_article,
            args=(article_url, all_article_data),
            kwargs={'task_info': task_info},
        )
        threads.append(thread)
        sem.acquire()
        thread.start()
    for thread in threads:
        thread.join()
    print()
    return all_article_data


if __name__ == '__main__':
    list_urls = get_list_urls()
    all_article_list = thread_get_all_article_list(list_urls)
    save_data(all_article_list, 'all_article_list.json')
    all_article = thread_get_all_article(all_article_list)
    save_data(all_article, 'all_article.json')
    insert_article_db(all_article)
    # list_urls: List[str] = config.list_urls
    # all_article_list = get_data('all_article_list.json')
    # all_article = get_data('all_article.json')
