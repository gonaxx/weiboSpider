import requests
from urllib3.exceptions import ProtocolError
from lxml import etree
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from http.client import RemoteDisconnected
from socket import timeout
from datetime import datetime
from datetime import timedelta
import time
import re
import pandas
import json
import random


class GetWeibo:
    browser_options = Options()
    # browser_options.add_argument("--headless")
    # browser_options.add_argument('--no-sandbox')
    browser = webdriver.Chrome(chrome_options=browser_options)
    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) '
                             'AppleWebKit/537.36 (KHTML, like Gecko) Chrome'
                             '/103.0.0.0 Safari/537.36'}
    print("浏览器已成功创建。")

    def __init__(self, url1='https://s.weibo.com/weibo'):
        self.url1 = url1
        # self.get_cookie(url1)
        self.open_search(url1)

    def open_search(self, url1):
        self.url1 = url1
        self.browser.get(url1)
        self.browser.delete_all_cookies()
        time.sleep(7)
        print(f'微博搜索页面{self.browser.current_url}已成功打开...')
        kw = self.browser.find_element(By.XPATH, ('//div[@class="searchbox"]/div[@class="search-input"]/'
                                                  'input[@type="text"]'))
        keywords = input('请输入微博搜索的关键词，按回车键确认：')
        print(f'搜索关键词为：{keywords}。')
        while True:
            origin = input('是否只搜索原创微博？是输入1，否输入0，按回车键确认：')
            if origin == '1':
                origin = '&scope=ori'
                print('仅搜索原创微博。')
                break
            elif origin == '0':
                origin = '&typeall=1'
                print('搜索全部微博。')
                continue
            else:
                print('输入错误，请重新输入。')
                break
        while True:
            date_now = input('请按年-月-日-时的格式输入抓取微博的发布截止时间（示例：2022-08-03-07），按回车键确认，直接按回车键则截止时间为当前时间：')
            if date_now == '':
                date_now = time.strftime('%Y-%m-%d-%H', time.localtime())
                print('截止时间为：当前时间。')
                break
            elif re.match(r'([0-9]{3}[1-9]|[0-9]{2}[1-9][0-9]{1}|[0-9]{1}[1-9][0-9]{2}|[1-9][0-9]{3})-'
                          r'(((0[13578]|1[02])-(0[1-9]|[12][0-9]|3[01]))|((0[469]|11)-(0[1-9]|[12][0-9]|30))|'
                          r'(02-(0[1-9]|[1][0-9]|2[0-8])))', date_now) is None:
                print('时间格式输入错误，请重新输入！')
                continue
            else:
                print(f'截止时间为：{date_now}。')
                break
        while True:
            page_begin = input('请输入微博列表的抓取起始页（示例：17），按回车键确认，直接按回车键从第1页开始：')
            if page_begin == '':
                page_begin = ''
                print('抓取起始页为：第1页。')
                break
            elif re.match(r'\d{1,3}', page_begin) is None:
                print('抓取起始页输入错误，请重新输入！')
                continue
            else:
                print(f'抓取起始页为：第{page_begin}页。')
                page_begin = '&page=' + page_begin
                break
        kw.send_keys(keywords)
        click_search = self.browser.find_element(By.XPATH, '//div[@class="searchbox"]/button[@class="s-btn-b"]')
        click_search.click()
        time.sleep(1)
        click_list = self.browser.find_element(By.XPATH, '//div[@class ="m-main-nav"]/ul/li[2]/a')
        click_list.click()
        time.sleep(1)
        print(f'微博列表页面{self.browser.current_url}已成功打开，列表按时间倒序排序。')
        with open('cookies.txt', 'r') as f:
            # 使用json读取cookies 注意读取的是文件 所以用load而不是loads
            cookies_list = json.load(f)
            for cookie in cookies_list:
                # 并不是所有cookie都含有expiry 所以要用dict的get方法来获取
                if isinstance(cookie.get('expiry'), float):
                    cookie['expiry'] = int(cookie['expiry'])
                self.browser.add_cookie(cookie)
        self.browser.refresh()
        # print(url1)
        date_now = time.strptime(date_now, '%Y-%m-%d-%H')
        times_judge0 = time.strftime('%Y-%m-%d %H', date_now)
        date_now = time.strftime('%Y-%m-%d-%H', date_now)
        times_judge0 = str(times_judge0) + ':00'
        times_judge0 = time.strptime(times_judge0, '%Y-%m-%d %H:%M')
        times_judge0 = time.strftime('%Y-%m-%d %H:%M', times_judge0)
        date_format = '%Y-%m-%d-%H'
        date_past = (datetime.strptime(date_now, date_format) + timedelta(days=-31)).strftime(date_format)
        url1 = self.browser.current_url
        try:
            url1_change = re.search(r'(.*%..)(?=&)', url1)
            # print(url1_change)
            url1 = url1_change.group() + f'{origin}&suball=1&timescope=custom:{date_past}:{date_now}&Refer=g{page_begin}'
            # print(url1)
        except AttributeError:
            print(repr(AttributeError))
            print('请运行getcookie.py，重新登录微博以获取cookie信息。')
        now = datetime.now()
        print(f'本次抓取的开始时间是：{now}')
        self.auto_search(url1, now, origin, times_judge0)

    def auto_search(self, url1, now, origin, times_judge0, search_times=0):
        global post_url
        self.url1 = url1
        page_num = url1.split('page=')[-1]
        if page_num.isdigit() is False:
            page_num = '1'
        page_num = int(page_num)
        if page_num < 50:
            if search_times > 0 and search_times % 50 == 0:
                now_run = datetime.now()
                cd = int(search_times / 50)
                if (now_run - now).seconds * cd >= 3600 * cd:
                    print(f'目前已抓取{search_times}页，一小时内的抓取数量未达到限制，将继续抓取...')
                    while True:
                        try:
                            if url1 != self.browser.current_url:
                                self.browser.get(url1)
                            print(f'微博列表页面{self.browser.current_url}已打开，抓取中...')
                            for i in range(1, 6):
                                i = random.random() * 3
                                time.sleep(i)
                            session = requests.Session()
                            cookies = self.browser.get_cookies()
                            for cookie in cookies:
                                session.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'],
                                                    path=cookie['path'])
                            while True:
                                try:
                                    response = session.get(url=url1, headers=self.headers, cookies=session.cookies,
                                                           timeout=(30, 50)).text
                                    data = etree.HTML(response)
                                    post_url = data.xpath(
                                        '//div[@node-type="like"]/p[@class="from"]/a[@target]/@href[1]')
                                    break
                                except (TimeoutError, AttributeError) as e1:
                                    print(repr(e1))
                                    print('在auto_search-1号处连接超时或解析错误，正在重试...')
                                    time.sleep(5)
                                    continue
                                except (ConnectionResetError, RemoteDisconnected, requests.ConnectionError,
                                        ProtocolError, ConnectionAbortedError, ConnectionRefusedError) as e2:
                                    print(repr(e2))
                                    sleeping = random.uniform(1, 1.1) * 3600
                                    start_time = time.strftime("%Y-%m-%d %X", time.localtime())
                                    print(f'在auto_search-1号处远程服务器被关闭，开始睡眠...睡眠开始时间：{start_time}    本次睡眠时长：{sleeping}秒')
                                    print('睡眠中...')
                                    time.sleep(sleeping)
                                    url1 = self.browser.current_url
                                    page_num = url1.split('page=')[-1]
                                    if page_num.isdigit() is False:
                                        page_num = '1'
                                    page_num = int(page_num)
                                    self.auto_search(url1, now, origin, times_judge0, search_times)
                            df = pandas.DataFrame(
                                columns=['微博账号', '发文时间', '发送平台', '微博内容', '收藏次数', '转发次数', '评论次数', '点赞次数', '原博地址'])
                            times = ''
                            for url0 in post_url:
                                url = 'http:' + url0
                                for i in range(1, 6):
                                    i = random.random() * 3
                                    time.sleep(i)
                                while True:
                                    try:
                                        post_web = session.get(url=url, headers=self.headers, cookies=session.cookies,
                                                               timeout=(30, 50)).text
                                        post_detail = re.search(r'{.*"Pl_Official_WeiboDetail__[\d]{2}".*}', post_web)
                                        # print(post_detail)
                                        post_detail = post_detail.group()
                                        # print(post_detail)
                                        break
                                    except (TimeoutError, AttributeError) as e1:
                                        print(repr(e1))
                                        print('在auto_search-1号处连接超时或解析错误，正在重试...')
                                        time.sleep(5)
                                        continue
                                    except (ConnectionResetError, RemoteDisconnected, requests.ConnectionError,
                                            ProtocolError, ConnectionAbortedError, ConnectionRefusedError) as e2:
                                        print(repr(e2))
                                        sleeping = random.uniform(1, 1.1) * 3600
                                        start_time = time.strftime("%Y-%m-%d %X", time.localtime())
                                        print(
                                            f'在auto_search-1号处远程服务器被关闭，开始睡眠...睡眠开始时间：{start_time}    本次睡眠时长：{sleeping}秒')
                                        print('睡眠中...')
                                        time.sleep(sleeping)
                                        url1 = self.browser.current_url
                                        page_num = url1.split('page=')[-1]
                                        if page_num.isdigit() is False:
                                            page_num = '1'
                                        page_num = int(page_num)
                                        self.auto_search(url1, now, origin, times_judge0, search_times)
                                post_json = json.loads(post_detail, strict=False)
                                post = etree.HTML(str(post_json.get('html')))
                                names = post.xpath('//div[@class="WB_detail"]/div[@class="WB_info"]/a/text()')
                                times = post.xpath('//div[@class="WB_detail"]/div[@class="WB_from S_txt2"]/a/@title')
                                from1 = post.xpath('//div[@class="WB_detail"]/div[@class="WB_from S_txt2"]//text()[2]')
                                from2 = post.xpath('//div[@class="WB_detail"]/div[@class="WB_from S_txt2"]/a[2]/text()')
                                from1 = ''.join(from1)
                                from2 = ''.join(from2)
                                froms = from1 + from2
                                froms = froms.replace(' ', '')
                                froms = froms.split('空%%%%值')
                                blogs = post.xpath('//div[@class="WB_detail"]/div[@class="WB_text W_f14"]//text()')
                                blogs = ''.join(blogs)
                                blogs = blogs.replace(' ', '')
                                blogs = blogs.replace('\n', '')
                                blogs = blogs.split('空%%%%%%%%值')
                                collects = post.xpath(
                                    '//span[@class="pos"]/span[@node-type="favorite_btn_text"]/span/em[2]/text()')
                                collects = [0 if i == '收藏' else int(i) for i in collects]
                                replies = post.xpath(
                                    '//span[@class="pos"]/span[@node-type="forward_btn_text"]/span/em[2]/text()')
                                replies = [0 if i == '转发' else int(i) for i in replies]
                                comments = post.xpath(
                                    '//span[@class="pos"]/span[@node-type="comment_btn_text"]/span/em[2]/text()')
                                comments = [0 if i == '评论' else int(i) for i in comments]
                                likes = post.xpath('//span[@class="pos"]//span[@node-type="like_status"]/em[2]/text()')
                                likes = [0 if i == '赞' else int(i) for i in likes]
                                url = url[:-23]
                                url = url.split('空%%%%值')
                                time.sleep(1)
                                key_list = ['微博账号', '发文时间', '发送平台', '微博内容', '收藏次数', '转发次数', '评论次数', '点赞次数', '原博地址']
                                info_list = [names, times, froms, blogs, collects, replies, comments, likes, url]
                                excel_info = dict(zip(key_list, info_list))
                                df1 = pandas.DataFrame(excel_info)
                                df = pandas.concat([df, df1])
                            times_judge1 = times[0]
                            times_judge1 = time.strptime(times_judge1, '%Y-%m-%d %H:%M')
                            times_judge1 = time.strftime('%Y-%m-%d %H:%M', times_judge1)
                            if times_judge1 < times_judge0:
                                df.to_csv('weibo_search.csv', mode='a', encoding='utf_8_sig', header=False, index=False)
                                url1 = self.browser.current_url
                                page_num = url1.split('page=')[-1]
                                if page_num.isdigit() is False:
                                    page_num = '1'
                                page_num = int(page_num)
                                print(f'已成功提取第{page_num}页微博信息并追加写入CSV文件！')
                                search_times += 1
                                for i in range(1, 6):
                                    i = random.random() * 3
                                    time.sleep(i)
                                click_next = self.browser.find_element(By.XPATH,
                                                                       '//div[@class="m-page"]/div/a[@class="next"]')
                                click_next.click()
                                time.sleep(1)
                                url1 = self.browser.current_url
                                self.auto_search(url1, now, origin, times_judge0, search_times)
                            else:
                                self.browser.back()
                                url1 = self.browser.current_url
                                page_change0 = url1.split('page=')[0]
                                page_change1 = int(url1.split('page=')[-1])
                                url1 = page_change0 + str(page_change1 + 2)
                                print(f'提示：因本阶段日期的微博已在上一页结束，现已后退至上一页，并采取绕过措施。')
                                self.auto_search(url1, now, origin, times_judge0, search_times)
                        except NoSuchElementException:
                            break
                    url1 = self.browser.current_url
                    page_num = url1.split('page=')[-1]
                    if page_num.isdigit() is False:
                        page_num = '1'
                    page_num = int(page_num)
                    during_time = re.search(r'(?<=custom:)(.*\d)(?=&)', url1)
                    during_time = during_time.group()
                    # print(f'发布日期在{during_time}之间的微博已在第{page_num}页结束，准备跳转下一阶段日期...')
                    print(f'本阶段日期的微博已在第{page_num}页结束，准备跳转下一阶段日期...')
                    print(f'目前已抓取{search_times}页。')
                    for i in range(1, 6):
                        i = random.random() * 3
                        time.sleep(i)
                    session = requests.Session()
                    cookies = self.browser.get_cookies()
                    for cookie in cookies:
                        session.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'],
                                            path=cookie['path'])
                    while True:
                        try:
                            response = session.get(url=url1, headers=self.headers, cookies=session.cookies,
                                                   timeout=(30, 50)).text
                            data = etree.HTML(response)
                            post_url = data.xpath('//div[@node-type="like"]/p[@class="from"]/a[@target]/@href[1]')
                            break
                        except (TimeoutError, AttributeError) as e1:
                            print(repr(e1))
                            print('在auto_search-5号处连接超时或解析错误，正在重试...')
                            time.sleep(5)
                            continue
                        except (ConnectionResetError, requests.ConnectionError, ProtocolError, ConnectionAbortedError,
                                RemoteDisconnected, ConnectionRefusedError) as e2:
                            print(repr(e2))
                            sleeping = random.uniform(1, 1.1) * 3600
                            start_time = time.strftime("%Y-%m-%d %X", time.localtime())
                            print(f'在auto_search-5号处远程服务器被关闭，开始睡眠...睡眠开始时间：{start_time}    本次睡眠时长：{sleeping}秒')
                            print('睡眠中...')
                            time.sleep(sleeping)
                            url1 = self.browser.current_url
                            page_num = url1.split('page=')[-1]
                            if page_num.isdigit() is False:
                                page_num = '1'
                            page_num = int(page_num)
                            self.auto_search(url1, now, origin, times_judge0, search_times)
                    url = 'http:' + post_url[-1]
                    for i in range(1, 6):
                        i = random.random() * 3
                        time.sleep(i)
                    while True:
                        try:
                            post_web = session.get(url=url, headers=self.headers, cookies=session.cookies,
                                                   timeout=(30, 50)).text
                            post_detail = re.search(r'{.*"Pl_Official_WeiboDetail__[\d]{2}".*}', post_web)
                            # print(post_detail)
                            post_detail = post_detail.group()
                            # print(post_detail)
                            break
                        except (TimeoutError, AttributeError) as e1:
                            print(repr(e1))
                            print('在auto_search-6号处连接超时或解析错误，正在重试...')
                            time.sleep(5)
                            continue
                        except (ConnectionResetError, requests.ConnectionError, ProtocolError, ConnectionAbortedError,
                                RemoteDisconnected, ConnectionRefusedError) as e2:
                            print(repr(e2))
                            sleeping = random.uniform(1, 1.1) * 3600
                            start_time = time.strftime("%Y-%m-%d %X", time.localtime())
                            print(f'在auto_search-6号处远程服务器被关闭，开始睡眠...睡眠开始时间：{start_time}    本次睡眠时长：{sleeping}秒')
                            print('睡眠中...')
                            time.sleep(sleeping)
                            url1 = self.browser.current_url
                            page_num = url1.split('page=')[-1]
                            if page_num.isdigit() is False:
                                page_num = '1'
                            page_num = int(page_num)
                            self.auto_search(url1, now, origin, times_judge0, search_times)
                    post_json = json.loads(post_detail, strict=False)
                    # print(post_json)
                    post = etree.HTML(str(post_json.get('html')))
                    times_last = post.xpath('//div[@class="WB_detail"]/div[@class="WB_from S_txt2"]/a/@title')
                    # print(times)
                    times_last = times_last[0]
                    times_last = time.strptime(times_last, '%Y-%m-%d %H:%M')
                    times_last = time.strftime('%Y-%m-%d-%H', times_last)
                    # print(times_last)
                    date_format = '%Y-%m-%d-%H'
                    times_change0 = (datetime.strptime(times_last, date_format) + timedelta(days=-31)).strftime(
                        date_format)
                    times_change = (datetime.strptime(times_last, date_format) + timedelta(hours=+1)).strftime(
                        date_format)
                    # print(times_change0)
                    # print(times_change)
                    print(f'提示：本页最后一条微博时间为{times_last}。')
                    url1 = self.browser.current_url
                    url1_change = re.search(r'(.*%..)(?=&)', url1)
                    url1 = url1_change.group() + f'{origin}&suball=1&timescope=custom:{times_change0}:{times_change}&Refer=g'
                    page_num = url1.split('page=')[-1]
                    if page_num.isdigit() is False:
                        page_num = '1'
                    page_num = int(page_num)
                    self.auto_search(url1, now, origin, times_judge0, search_times)
                else:
                    url1 = self.browser.current_url
                    session = requests.Session()
                    cookies = self.browser.get_cookies()
                    for cookie in cookies:
                        session.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'],
                                            path=cookie['path'])
                    while True:
                        try:
                            response = session.get(url=url1, headers=self.headers, cookies=session.cookies,
                                                   timeout=(30, 50)).text
                            data = etree.HTML(response)
                            post_url = data.xpath('//div[@node-type="like"]/p[@class="from"]/a[@target]/@href[1]')
                            break
                        except (TimeoutError, AttributeError) as e1:
                            print(repr(e1))
                            print('在auto_search-7号处连接超时或解析错误，正在重试...')
                            time.sleep(5)
                            continue
                        except (ConnectionResetError, requests.ConnectionError, ProtocolError, ConnectionAbortedError,
                                RemoteDisconnected, ConnectionRefusedError) as e2:
                            print(repr(e2))
                            sleeping = random.uniform(1, 1.1) * 3600
                            start_time = time.strftime("%Y-%m-%d %X", time.localtime())
                            print(f'在auto_search-7号处远程服务器被关闭，开始睡眠...睡眠开始时间：{start_time}    本次睡眠时长：{sleeping}秒')
                            print('睡眠中...')
                            time.sleep(sleeping)
                            url1 = self.browser.current_url
                            page_num = url1.split('page=')[-1]
                            if page_num.isdigit() is False:
                                page_num = '1'
                            page_num = int(page_num)
                            self.auto_search(url1, now, origin, times_judge0, search_times)
                    url = 'http:' + post_url[-1]
                    for i in range(1, 6):
                        i = random.random() * 3
                        time.sleep(i)
                    while True:
                        try:
                            post_web = session.get(url=url, headers=self.headers, cookies=session.cookies,
                                                   timeout=(30, 50)).text
                            post_detail = re.search(r'{.*"Pl_Official_WeiboDetail__[\d]{2}".*}', post_web)
                            # print(post_detail)
                            post_detail = post_detail.group()
                            # print(post_detail)
                            break
                        except (TimeoutError, AttributeError) as e1:
                            print(repr(e1))
                            print('在auto_search-8号处连接超时或解析错误，正在重试...')
                            time.sleep(5)
                            continue
                        except (ConnectionResetError, requests.ConnectionError, ProtocolError, ConnectionAbortedError,
                                RemoteDisconnected, ConnectionRefusedError) as e2:
                            print(repr(e2))
                            sleeping = random.uniform(1, 1.1) * 3600
                            start_time = time.strftime("%Y-%m-%d %X", time.localtime())
                            print(f'在auto_search-8号处远程服务器被关闭，开始睡眠...睡眠开始时间：{start_time}    本次睡眠时长：{sleeping}秒')
                            print('睡眠中...')
                            time.sleep(sleeping)
                            url1 = self.browser.current_url
                            page_num = url1.split('page=')[-1]
                            if page_num.isdigit() is False:
                                page_num = '1'
                            page_num = int(page_num)
                            self.auto_search(url1, now, origin, times_judge0, search_times)
                    post_json = json.loads(post_detail, strict=False)
                    # print(post_json)
                    post = etree.HTML(str(post_json.get('html')))
                    times_last = post.xpath('//div[@class="WB_detail"]/div[@class="WB_from S_txt2"]/a/@title')
                    times_last = times_last[0]
                    times_last = time.strptime(times_last, '%Y-%m-%d %H:%M')
                    times_last = time.strftime('%Y-%m-%d-%H', times_last)
                    # print(times_last)
                    date_format = '%Y-%m-%d-%H'
                    times_change0 = (datetime.strptime(times_last, date_format) + timedelta(days=-31)).strftime(
                        date_format)
                    times_change = (datetime.strptime(times_last, date_format) + timedelta(hours=+1)).strftime(
                        date_format)
                    # print(times_change0)
                    # print(times_change)
                    print(f'提示：本页最后一条微博时间为{times_last}。')
                    url1_change = re.search(r'(.*%..)(?=&)', url1)
                    url1 = url1_change.group() + f'{origin}&suball=1&timescope=custom:{times_change0}:{times_change}&Refer=g'
                    now_sleep = datetime.now()
                    sleeping = (3600 * cd) - (now_sleep - now).seconds * cd + (random.uniform(1, 1.1) * 60)
                    start_time = time.strftime("%Y-%m-%d %X", time.localtime())
                    print(f'目前已抓取{search_times}页,因一小时内的抓取页数已达到限制，开始睡眠...睡眠开始时间：{start_time}    本次睡眠时长：{sleeping}秒')
                    print('睡眠中...')
                    time.sleep(sleeping)
                    page_num = url1.split('page=')[-1]
                    if page_num.isdigit() is False:
                        page_num = '1'
                    page_num = int(page_num)
                    self.auto_search(url1, now, origin, times_judge0, search_times)
            else:
                while True:
                    try:
                        if url1 != self.browser.current_url:
                            self.browser.get(url1)
                        print(f'微博列表页面{self.browser.current_url}已打开，抓取中...')
                        for i in range(1, 6):
                            i = random.random() * 3
                            time.sleep(i)
                        session = requests.Session()
                        cookies = self.browser.get_cookies()
                        for cookie in cookies:
                            session.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'], path=cookie['path'])
                        while True:
                            try:
                                response = session.get(url=url1, headers=self.headers, cookies=session.cookies,
                                                       timeout=(30, 50)).text
                                data = etree.HTML(response)
                                post_url = data.xpath('//div[@node-type="like"]/p[@class="from"]/a[@target]/@href[1]')
                                break
                            except (TimeoutError, AttributeError, timeout) as e1:
                                print(repr(e1))
                                print('在auto_search-9号处连接超时或解析错误，正在重试...')
                                time.sleep(5)
                                continue
                            except (ConnectionResetError, RemoteDisconnected, requests.ConnectionError, ProtocolError,
                                    ConnectionAbortedError, ConnectionRefusedError) as e2:
                                print(repr(e2))
                                sleeping = random.uniform(1, 1.1) * 3600
                                start_time = time.strftime("%Y-%m-%d %X", time.localtime())
                                print(f'在auto_search-9号处远程服务器被关闭，开始睡眠...睡眠开始时间：{start_time}    本次睡眠时长：{sleeping}秒')
                                print('睡眠中...')
                                time.sleep(sleeping)
                                url1 = self.browser.current_url
                                self.auto_search(url1, now, origin, times_judge0, search_times)
                        df = pandas.DataFrame(
                            columns=['微博账号', '发文时间', '发送平台', '微博内容', '收藏次数', '转发次数', '评论次数', '点赞次数', '原博地址'])
                        times = ''
                        for url0 in post_url:
                            url = 'http:' + url0
                            for i in range(1, 6):
                                i = random.random() * 3
                                time.sleep(i)
                            while True:
                                try:
                                    post_web = session.get(url=url, headers=self.headers, cookies=session.cookies,
                                                           timeout=(30, 50)).text
                                    post_detail = re.search(r'{.*"Pl_Official_WeiboDetail__[\d]{2}".*}', post_web)
                                    # print(post_detail)
                                    post_detail = post_detail.group()
                                    # print(post_detail)
                                    break
                                except (TimeoutError, AttributeError, timeout) as e1:
                                    print(repr(e1))
                                    print('在auto_search-10号处连接超时或解析错误，正在重试...')
                                    time.sleep(5)
                                    continue
                                except (ConnectionResetError, RemoteDisconnected, requests.ConnectionError,
                                        ProtocolError, ConnectionAbortedError, ConnectionRefusedError) as e2:
                                    print(repr(e2))
                                    sleeping = random.uniform(1, 1.1) * 3600
                                    start_time = time.strftime("%Y-%m-%d %X", time.localtime())
                                    print(f'在auto_search-10号处远程服务器被关闭，开始睡眠...睡眠开始时间：{start_time}    本次睡眠时长：{sleeping}秒')
                                    print('睡眠中...')
                                    time.sleep(sleeping)
                                    url1 = self.browser.current_url
                                    self.auto_search(url1, now, origin, times_judge0, search_times)
                            post_json = json.loads(post_detail, strict=False)
                            post = etree.HTML(str(post_json.get('html')))
                            names = post.xpath('//div[@class="WB_detail"]/div[@class="WB_info"]/a/text()')
                            times = post.xpath('//div[@class="WB_detail"]/div[@class="WB_from S_txt2"]/a/@title')
                            from1 = post.xpath('//div[@class="WB_detail"]/div[@class="WB_from S_txt2"]//text()[2]')
                            from2 = post.xpath('//div[@class="WB_detail"]/div[@class="WB_from S_txt2"]/a[2]/text()')
                            from1 = ''.join(from1)
                            from2 = ''.join(from2)
                            froms = from1 + from2
                            froms = froms.replace(' ', '')
                            froms = froms.split('空%%%%值')
                            blogs = post.xpath('//div[@class="WB_detail"]/div[@class="WB_text W_f14"]//text()')
                            blogs = ''.join(blogs)
                            blogs = blogs.replace(' ', '')
                            blogs = blogs.replace('\n', '')
                            blogs = blogs.split('空%%%%%%%%值')
                            collects = post.xpath(
                                '//span[@class="pos"]/span[@node-type="favorite_btn_text"]/span/em[2]/text()')
                            collects = [0 if i == '收藏' else int(i) for i in collects]
                            replies = post.xpath('//span[@class="pos"]/span[@node-type="forward_btn_text"]/span/em[2]/text()')
                            replies = [0 if i == '转发' else int(i) for i in replies]
                            comments = post.xpath(
                                '//span[@class="pos"]/span[@node-type="comment_btn_text"]/span/em[2]/text()')
                            comments = [0 if i == '评论' else int(i) for i in comments]
                            likes = post.xpath('//span[@class="pos"]//span[@node-type="like_status"]/em[2]/text()')
                            likes = [0 if i == '赞' else int(i) for i in likes]
                            url = url[:-23]
                            url = url.split('空%%%%值')
                            time.sleep(1)
                            key_list = ['微博账号', '发文时间', '发送平台', '微博内容', '收藏次数', '转发次数', '评论次数', '点赞次数', '原博地址']
                            info_list = [names, times, froms, blogs, collects, replies, comments, likes, url]
                            excel_info = dict(zip(key_list, info_list))
                            df1 = pandas.DataFrame(excel_info)
                            df = pandas.concat([df, df1])
                        times_judge1 = times[0]
                        times_judge1 = time.strptime(times_judge1, '%Y-%m-%d %H:%M')
                        times_judge1 = time.strftime('%Y-%m-%d %H:%M', times_judge1)
                        if times_judge1 < times_judge0:
                            if search_times == 0:
                                df.to_csv('weibo_search.csv', mode='a', encoding='utf_8_sig', header=True, index=False)
                            else:
                                df.to_csv('weibo_search.csv', mode='a', encoding='utf_8_sig', header=False, index=False)

                            url1 = self.browser.current_url
                            page_num = url1.split('page=')[-1]
                            if page_num.isdigit() is False:
                                page_num = '1'
                            page_num = int(page_num)
                            print(f'已成功提取第{page_num}页微博信息并追加写入CSV文件！')
                            search_times += 1
                            for i in range(1, 6):
                                i = random.random() * 3
                                time.sleep(i)
                            click_next = self.browser.find_element(By.XPATH,
                                                                   '//div[@class="m-page"]/div/a[@class="next"]')
                            click_next.click()
                            time.sleep(1)
                            url1 = self.browser.current_url
                            self.auto_search(url1, now, origin, times_judge0, search_times)
                        else:
                            self.browser.back()
                            url1 = self.browser.current_url
                            page_change0 = url1.split('page=')[0]
                            page_change1 = int(url1.split('page=')[-1])
                            url1 = page_change0 + str(page_change1 + 2)
                            print(f'提示：因本阶段日期的微博已在上一页结束，现已后退至上一页，并采取绕过措施。')
                            self.auto_search(url1, now, origin, times_judge0, search_times)
                    except NoSuchElementException:
                        break
                url1 = self.browser.current_url
                page_num = url1.split('page=')[-1]
                if page_num.isdigit() is False:
                    page_num = '1'
                page_num = int(page_num)
                during_time = re.search(r'(?<=custom:)(.*\d)(?=&)', url1)
                during_time = during_time.group()
                print(f'发布日期在{during_time}之间的微博已在第{page_num}页结束，准备跳转下一阶段日期...')
                print(f'目前已抓取{search_times}页。')
                for i in range(1, 6):
                    i = random.random() * 3
                    time.sleep(i)
                session = requests.Session()
                cookies = self.browser.get_cookies()
                for cookie in cookies:
                    session.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'], path=cookie['path'])
                while True:
                    try:
                        response = session.get(url=url1, headers=self.headers, cookies=session.cookies,
                                               timeout=(30, 50)).text
                        data = etree.HTML(response)
                        post_url = data.xpath('//div[@node-type="like"]/p[@class="from"]/a[@target]/@href[1]')
                        break
                    except (TimeoutError, AttributeError, timeout) as e1:
                        print(repr(e1))
                        print('在auto_search-13号处连接超时或解析错误，正在重试...')
                        time.sleep(5)
                        continue
                    except (ConnectionResetError, requests.ConnectionError, ProtocolError, ConnectionAbortedError,
                            RemoteDisconnected, ConnectionRefusedError) as e2:
                        print(repr(e2))
                        sleeping = random.uniform(1, 1.1) * 3600
                        start_time = time.strftime("%Y-%m-%d %X", time.localtime())
                        print(f'在auto_search-13号处远程服务器被关闭，开始睡眠...睡眠开始时间：{start_time}    本次睡眠时长：{sleeping}秒')
                        print('睡眠中...')
                        time.sleep(sleeping)
                        url1 = self.browser.current_url
                        page_num = url1.split('page=')[-1]
                        if page_num.isdigit() is False:
                            page_num = '1'
                        page_num = int(page_num)
                        self.auto_search(url1, now, origin, times_judge0, search_times)
                url = 'http:' + post_url[-1]
                for i in range(1, 6):
                    i = random.random() * 3
                    time.sleep(i)
                while True:
                    try:
                        post_web = session.get(url=url, headers=self.headers, cookies=session.cookies,
                                               timeout=(30, 50)).text
                        post_detail = re.search(r'{.*"Pl_Official_WeiboDetail__[\d]{2}".*}', post_web)
                        # print(post_detail)
                        post_detail = post_detail.group()
                        # print(post_detail)
                        break
                    except (TimeoutError, AttributeError, timeout) as e1:
                        print(repr(e1))
                        print('在auto_search-14号处连接超时或解析错误，正在重试...')
                        time.sleep(5)
                        continue
                    except (ConnectionResetError, requests.ConnectionError, ProtocolError, ConnectionAbortedError,
                            RemoteDisconnected, ConnectionRefusedError) as e2:
                        print(repr(e2))
                        sleeping = random.uniform(1, 1.1) * 3600
                        start_time = time.strftime("%Y-%m-%d %X", time.localtime())
                        print(f'在auto_search-14号处远程服务器被关闭，开始睡眠...睡眠开始时间：{start_time}    本次睡眠时长：{sleeping}秒')
                        print('睡眠中...')
                        time.sleep(sleeping)
                        url1 = self.browser.current_url
                        page_num = url1.split('page=')[-1]
                        if page_num.isdigit() is False:
                            page_num = '1'
                        page_num = int(page_num)
                        self.auto_search(url1, now, origin, times_judge0, search_times)
                post_json = json.loads(post_detail, strict=False)
                # print(post_json)
                post = etree.HTML(str(post_json.get('html')))
                times_last = post.xpath('//div[@class="WB_detail"]/div[@class="WB_from S_txt2"]/a/@title')
                # print(times)
                times_last = times_last[0]
                times_last = time.strptime(times_last, '%Y-%m-%d %H:%M')
                times_last = time.strftime('%Y-%m-%d-%H', times_last)
                # print(times_last)
                date_format = '%Y-%m-%d-%H'
                times_change0 = (datetime.strptime(times_last, date_format) + timedelta(days=-31)).strftime(date_format)
                times_change = (datetime.strptime(times_last, date_format) + timedelta(hours=+1)).strftime(date_format)
                # print(times_change0)
                # print(times_change)
                print(f'提示：本页最后一条微博时间为{times_last}。')
                url1 = self.browser.current_url
                url1_change = re.search(r'(.*%..)(?=&)', url1)
                url1 = url1_change.group() + f'{origin}&suball=1&timescope=custom:{times_change0}:{times_change}&Refer=g'
                page_num = url1.split('page=')[-1]
                if page_num.isdigit() is False:
                    page_num = '1'
                page_num = int(page_num)
                self.auto_search(url1, now, origin, times_judge0, search_times)
        if page_num == 50:
            if url1 != self.browser.current_url:
                self.browser.get(url1)
            print(f'微博列表页面{self.browser.current_url}已打开，抓取中...')
            now_run = datetime.now()
            cd = int(search_times / 50)
            if (now_run - now).seconds * cd >= 3600 * cd:
                print(f'目前已抓取{search_times}页，一小时内的抓取数量未达到限制，将继续抓取...')
                during_time = re.search(r'(?<=custom:)(.*\d)(?=&)', url1)
                # during_time = during_time.group()
                # print(f'发布日期在{during_time}之间的微博已在第{page_num}页结束，准备跳转下一阶段日期...')
                for i in range(1, 6):
                    i = random.random() * 3
                    time.sleep(i)
                session = requests.Session()
                cookies = self.browser.get_cookies()
                for cookie in cookies:
                    session.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'],
                                        path=cookie['path'])
                while True:
                    try:
                        response = session.get(url=url1, headers=self.headers, cookies=session.cookies,
                                               timeout=(30, 50)).text
                        data = etree.HTML(response)
                        post_url = data.xpath('//div[@node-type="like"]/p[@class="from"]/a[@target]/@href[1]')
                        break
                    except (TimeoutError, AttributeError, timeout) as e1:
                        print(repr(e1))
                        print('在auto_search-15号处连接超时或解析错误，正在重试...')
                        time.sleep(5)
                        continue
                    except (ConnectionResetError, requests.ConnectionError, ProtocolError, ConnectionAbortedError,
                            RemoteDisconnected, ConnectionRefusedError) as e2:
                        print(repr(e2))
                        sleeping = random.uniform(1, 1.1) * 3600
                        start_time = time.strftime("%Y-%m-%d %X", time.localtime())
                        print(f'在auto_search-15号处远程服务器被关闭，开始睡眠...睡眠开始时间：{start_time}    本次睡眠时长：{sleeping}秒')
                        print('睡眠中...')
                        time.sleep(sleeping)
                        url1 = self.browser.current_url
                        page_num = url1.split('page=')[-1]
                        if page_num.isdigit() is False:
                            page_num = '1'
                        page_num = int(page_num)
                        self.auto_search(url1, now, origin, times_judge0, search_times)
                df = pandas.DataFrame(
                    columns=['微博账号', '发文时间', '发送平台', '微博内容', '收藏次数', '转发次数', '评论次数', '点赞次数', '原博地址'])
                times = ''
                for url0 in post_url:
                    url = 'http:' + url0
                    for i in range(1, 6):
                        i = random.random() * 3
                        time.sleep(i)
                    while True:
                        try:
                            post_web = session.get(url=url, headers=self.headers, cookies=session.cookies,
                                                   timeout=(30, 50)).text
                            post_detail = re.search(r'{.*"Pl_Official_WeiboDetail__[\d]{2}".*}', post_web)
                            # print(post_detail)
                            post_detail = post_detail.group()
                            # print(post_detail)
                            break
                        except (TimeoutError, AttributeError, timeout) as e1:
                            print(repr(e1))
                            print('在auto_search-16号处连接超时或解析错误，正在重试...')
                            time.sleep(5)
                            continue
                        except (ConnectionResetError, RemoteDisconnected, requests.ConnectionError,
                                ProtocolError, ConnectionAbortedError, ConnectionRefusedError) as e2:
                            print(repr(e2))
                            sleeping = random.uniform(1, 1.1) * 3600
                            start_time = time.strftime("%Y-%m-%d %X", time.localtime())
                            print(f'在auto_search-16号处远程服务器被关闭，开始睡眠...睡眠开始时间：{start_time}    本次睡眠时长：{sleeping}秒')
                            print('睡眠中...')
                            time.sleep(sleeping)
                            url1 = self.browser.current_url
                            self.auto_search(url1, now, origin, times_judge0, search_times)
                    post_json = json.loads(post_detail, strict=False)
                    post = etree.HTML(str(post_json.get('html')))
                    names = post.xpath('//div[@class="WB_detail"]/div[@class="WB_info"]/a/text()')
                    times = post.xpath('//div[@class="WB_detail"]/div[@class="WB_from S_txt2"]/a/@title')
                    from1 = post.xpath('//div[@class="WB_detail"]/div[@class="WB_from S_txt2"]//text()[2]')
                    from2 = post.xpath('//div[@class="WB_detail"]/div[@class="WB_from S_txt2"]/a[2]/text()')
                    from1 = ''.join(from1)
                    from2 = ''.join(from2)
                    froms = from1 + from2
                    froms = froms.replace(' ', '')
                    froms = froms.split('空%%%%值')
                    blogs = post.xpath('//div[@class="WB_detail"]/div[@class="WB_text W_f14"]//text()')
                    blogs = ''.join(blogs)
                    blogs = blogs.replace(' ', '')
                    blogs = blogs.replace('\n', '')
                    blogs = blogs.split('空%%%%%%%%值')
                    collects = post.xpath(
                        '//span[@class="pos"]/span[@node-type="favorite_btn_text"]/span/em[2]/text()')
                    collects = [0 if i == '收藏' else int(i) for i in collects]
                    replies = post.xpath('//span[@class="pos"]/span[@node-type="forward_btn_text"]/span/em[2]/text()')
                    replies = [0 if i == '转发' else int(i) for i in replies]
                    comments = post.xpath(
                        '//span[@class="pos"]/span[@node-type="comment_btn_text"]/span/em[2]/text()')
                    comments = [0 if i == '评论' else int(i) for i in comments]
                    likes = post.xpath('//span[@class="pos"]//span[@node-type="like_status"]/em[2]/text()')
                    likes = [0 if i == '赞' else int(i) for i in likes]
                    url = url[:-23]
                    url = url.split('空%%%%值')
                    time.sleep(1)
                    key_list = ['微博账号', '发文时间', '发送平台', '微博内容', '收藏次数', '转发次数', '评论次数', '点赞次数', '原博地址']
                    info_list = [names, times, froms, blogs, collects, replies, comments, likes, url]
                    excel_info = dict(zip(key_list, info_list))
                    df1 = pandas.DataFrame(excel_info)
                    df = pandas.concat([df, df1])
                times_judge1 = times[0]
                times_judge1 = time.strptime(times_judge1, '%Y-%m-%d %H:%M')
                times_judge1 = time.strftime('%Y-%m-%d %H:%M', times_judge1)
                if times_judge1 < times_judge0:
                    if search_times == 0:
                        df.to_csv('weibo_search.csv', mode='a', encoding='utf_8_sig', header=True, index=False)
                    else:
                        df.to_csv('weibo_search.csv', mode='a', encoding='utf_8_sig', header=False, index=False)
                    url1 = self.browser.current_url
                    page_num = url1.split('page=')[-1]
                    if page_num.isdigit() is False:
                        page_num = '1'
                    page_num = int(page_num)
                    print(f'已成功提取第{page_num}页微博信息并追加写入CSV文件！')
                    search_times += 1
                    for i in range(1, 6):
                        i = random.random() * 3
                        time.sleep(i)
                    session = requests.Session()
                    cookies = self.browser.get_cookies()
                    for cookie in cookies:
                        session.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'], path=cookie['path'])
                    while True:
                        try:
                            response = session.get(url=url1, headers=self.headers, cookies=session.cookies,
                                                   timeout=(30, 50)).text
                            data = etree.HTML(response)
                            post_url = data.xpath('//div[@node-type="like"]/p[@class="from"]/a[@target]/@href[1]')
                            break
                        except (TimeoutError, AttributeError, timeout) as e1:
                            print(repr(e1))
                            print('在auto_search-17号处连接超时或解析错误，正在重试...')
                            time.sleep(5)
                            continue
                        except (ConnectionResetError, requests.ConnectionError, ProtocolError, ConnectionAbortedError,
                                RemoteDisconnected, ConnectionRefusedError) as e2:
                            print(repr(e2))
                            sleeping = random.uniform(1, 1.1) * 3600
                            start_time = time.strftime("%Y-%m-%d %X", time.localtime())
                            print(f'在auto_search-17号处远程服务器被关闭，开始睡眠...睡眠开始时间：{start_time}    本次睡眠时长：{sleeping}秒')
                            print('睡眠中...')
                            time.sleep(sleeping)
                            url1 = self.browser.current_url
                            page_num = url1.split('page=')[-1]
                            if page_num.isdigit() is False:
                                page_num = '1'
                            page_num = int(page_num)
                            self.auto_search(url1, now, origin, times_judge0, search_times)
                    url = 'http:' + post_url[-1]
                    for i in range(1, 6):
                        i = random.random() * 3
                        time.sleep(i)
                    while True:
                        try:
                            post_web = session.get(url=url, headers=self.headers, cookies=session.cookies,
                                                   timeout=(30, 50)).text
                            post_detail = re.search(r'{.*"Pl_Official_WeiboDetail__[\d]{2}".*}', post_web)
                            # print(post_detail)
                            post_detail = post_detail.group()
                            # print(post_detail)
                            break
                        except (TimeoutError, AttributeError, timeout) as e1:
                            print(repr(e1))
                            print('在auto_search-18号处连接超时或解析错误，正在重试...')
                            time.sleep(5)
                            continue
                        except (ConnectionResetError, requests.ConnectionError, ProtocolError, ConnectionAbortedError,
                                RemoteDisconnected, ConnectionRefusedError) as e2:
                            print(repr(e2))
                            sleeping = random.uniform(1, 1.1) * 3600
                            start_time = time.strftime("%Y-%m-%d %X", time.localtime())
                            print(f'在auto_search-18号处远程服务器被关闭，开始睡眠...睡眠开始时间：{start_time}    本次睡眠时长：{sleeping}秒')
                            print('睡眠中...')
                            time.sleep(sleeping)
                            url1 = self.browser.current_url
                            page_num = url1.split('page=')[-1]
                            if page_num.isdigit() is False:
                                page_num = '1'
                            page_num = int(page_num)
                            self.auto_search(url1, now, origin, times_judge0, search_times)
                    post_json = json.loads(post_detail, strict=False)
                    # print(post_json)
                    post = etree.HTML(str(post_json.get('html')))
                    times_last = post.xpath('//div[@class="WB_detail"]/div[@class="WB_from S_txt2"]/a/@title')
                    # print(times)
                    times_last = times_last[0]
                    times_last = time.strptime(times_last, '%Y-%m-%d %H:%M')
                    times_last = time.strftime('%Y-%m-%d-%H', times_last)
                    # print(times_last)
                    date_format = '%Y-%m-%d-%H'
                    times_change0 = (datetime.strptime(times_last, date_format) + timedelta(days=-31)).strftime(
                        date_format)
                    times_change = (datetime.strptime(times_last, date_format) + timedelta(hours=+1)).strftime(
                        date_format)
                    # print(times_change0)
                    # print(times_change)
                    print(f'本阶段日期的微博已在第{page_num}页结束，准备跳转下一阶段日期...')
                    print(f'提示：本页最后一条微博时间为{times_last}。')
                    url1 = self.browser.current_url
                    url1_change = re.search(r'(.*%..)(?=&)', url1)
                    url1 = url1_change.group() + f'{origin}&suball=1&timescope=custom:{times_change0}:{times_change}&Refer=g'
                    page_num = url1.split('page=')[-1]
                    if page_num.isdigit() is False:
                        page_num = '1'
                    page_num = int(page_num)
                    self.auto_search(url1, now, origin, times_judge0, search_times)
                else:
                    self.browser.back()
                    url1 = self.browser.current_url
                    page_change0 = url1.split('page=')[0]
                    page_change1 = int(url1.split('page=')[-1])
                    url1 = page_change0 + str(page_change1 + 2)
                    print(f'提示：因本阶段日期的微博已在上一页结束，现已后退至上一页，并采取绕过措施。')
                    self.auto_search(url1, now, origin, times_judge0, search_times)
            else:
                url1 = self.browser.current_url
                session = requests.Session()
                cookies = self.browser.get_cookies()
                for cookie in cookies:
                    session.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'], path=cookie['path'])
                while True:
                    try:
                        response = session.get(url=url1, headers=self.headers, cookies=session.cookies,
                                               timeout=(30, 50)).text
                        data = etree.HTML(response)
                        post_url = data.xpath('//div[@node-type="like"]/p[@class="from"]/a[@target]/@href[1]')
                        break
                    except (TimeoutError, AttributeError, timeout) as e1:
                        print(repr(e1))
                        print('在auto_search-19号处连接超时或解析错误，正在重试...')
                        time.sleep(5)
                        continue
                    except (ConnectionResetError, requests.ConnectionError, ProtocolError, ConnectionAbortedError,
                            RemoteDisconnected, ConnectionRefusedError) as e2:
                        print(repr(e2))
                        sleeping = random.uniform(1, 1.1) * 3600
                        start_time = time.strftime("%Y-%m-%d %X", time.localtime())
                        print(f'在auto_search-19号处远程服务器被关闭，开始睡眠...睡眠开始时间：{start_time}    本次睡眠时长：{sleeping}秒')
                        print('睡眠中...')
                        time.sleep(sleeping)
                        url1 = self.browser.current_url
                        page_num = url1.split('page=')[-1]
                        if page_num.isdigit() is False:
                            page_num = '1'
                        page_num = int(page_num)
                        self.auto_search(url1, now, origin, times_judge0, search_times)
                url = 'http:' + post_url[-1]
                for i in range(1, 6):
                    i = random.random() * 3
                    time.sleep(i)
                while True:
                    try:
                        post_web = session.get(url=url, headers=self.headers, cookies=session.cookies,
                                               timeout=(30, 50)).text
                        post_detail = re.search(r'{.*"Pl_Official_WeiboDetail__[\d]{2}".*}', post_web)
                        # print(post_detail)
                        post_detail = post_detail.group()
                        # print(post_detail)
                        break
                    except (TimeoutError, AttributeError, timeout) as e1:
                        print(repr(e1))
                        print('在auto_search-20号处连接超时或解析错误，正在重试...')
                        time.sleep(5)
                        continue
                    except (ConnectionResetError, requests.ConnectionError, ProtocolError, ConnectionAbortedError,
                            RemoteDisconnected, ConnectionRefusedError) as e2:
                        print(repr(e2))
                        sleeping = random.uniform(1, 1.1) * 3600
                        start_time = time.strftime("%Y-%m-%d %X", time.localtime())
                        print(f'在auto_search-20号处远程服务器被关闭，开始睡眠...睡眠开始时间：{start_time}    本次睡眠时长：{sleeping}秒')
                        print('睡眠中...')
                        time.sleep(sleeping)
                        url1 = self.browser.current_url
                        page_num = url1.split('page=')[-1]
                        if page_num.isdigit() is False:
                            page_num = '1'
                        page_num = int(page_num)
                        self.auto_search(url1, now, origin, times_judge0, search_times)
                post_json = json.loads(post_detail, strict=False)
                # print(post_json)
                post = etree.HTML(str(post_json.get('html')))
                times_last = post.xpath('//div[@class="WB_detail"]/div[@class="WB_from S_txt2"]/a/@title')
                times_last = times_last[0]
                times_last = time.strptime(times_last, '%Y-%m-%d %H:%M')
                times_last = time.strftime('%Y-%m-%d-%H', times_last)
                # print(times_last)
                date_format = '%Y-%m-%d-%H'
                times_change0 = (datetime.strptime(times_last, date_format) + timedelta(days=-31)).strftime(date_format)
                times_change = (datetime.strptime(times_last, date_format) + timedelta(hours=+1)).strftime(date_format)
                # print(times_change0)
                # print(times_change)
                print(f'提示：本页最后一条微博时间为{times_last}。')
                url1_change = re.search(r'(.*%..)(?=&)', url1)
                url1 = url1_change.group() + f'{origin}&suball=1&timescope=custom:{times_change0}:{times_change}&Refer=g'
                page_num = url1.split('page=')[-1]
                if page_num.isdigit() is False:
                    page_num = '1'
                page_num = int(page_num)
                now_sleep = datetime.now()
                sleeping = (3600 * cd) - (now_sleep - now).seconds * cd + (random.uniform(1, 1.1) * 60)
                start_time = time.strftime("%Y-%m-%d %X", time.localtime())
                print(f'目前已抓取{search_times}页,因一小时内的抓取页数已达到限制，开始睡眠...睡眠开始时间：{start_time}    本次睡眠时长：{sleeping}秒')
                print('睡眠中...')
                time.sleep(sleeping)
                self.auto_search(url1, now, origin, times_judge0, search_times)


gt = GetWeibo()
