import requests, re, os, config, json


def get_list_urls():
    '''获取文章列表页 URL 列表'''
    url = config.base_url + '/sitemap.html'
    res = requests.get(url, timeout=(5, 10))
    res_text = res.content.decode('gbk', 'ignore')
    all_url = re.findall(
        r'href=[\'"](' + config.base_url + r'/(?:yd/)?\w+/)[\'"]', res_text
    )
    urls = []
    for url in all_url:
        print(f'正在校验 {url}')
        if check_list_url(url) and url not in urls:
            urls.append(url)
    file_path = os.path.dirname(__file__) + './list_urls.json'
    json.dump(urls, open(file_path, 'w', encoding='utf-8'))
    print(f'校验完成，获得 {len(urls)} 个列表 URL，文件保存在 {os.path.abspath(file_path)}')
    return urls


def check_list_url(url: str, has_retry: int = 0, max_retry: int = 5) -> bool:
    '''校验 URL 是否是文章列表页'''
    try:
        res = requests.get(url, timeout=2)
    except:
        has_retry += 1
        if has_retry > max_retry:
            return
        print(f'遇到错误，正在重试第 {has_retry} 次')
        return check_list_url(url, has_retry)
    res_text = res.content.decode('gbk', 'ignore')
    result = re.search(r'class="tleft".*?<ul.*?>(.*?)</ul>', res_text, re.DOTALL)
    return bool(result)


if __name__ == '__main__':
    get_list_urls()
