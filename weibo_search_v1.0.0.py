from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from lxml import etree
import pandas
import requests
import json
import datetime
import random
import time
import re

# from get_cookie import get_cookie


class GetWeibo:
    browser_options = Options()
    # browser_options.add_argument("--headless")
    # browser_options.add_argument('--no-sandbox')
    browser = webdriver.Chrome(chrome_options=browser_options)
    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) '
                             'AppleWebKit/537.36 (KHTML, like Gecko) Chrome'
                             '/103.0.0.0 Safari/537.36'}
    print("浏览器已成功创建。")

    def __init__(self, base_url='https://s.weibo.com/weibo'):
        self.base_url = base_url
        self.keywords = None
        # 如果cookie失效，请重新运行
        # get_cookie()
        self.open_search(base_url)

    def open_search(self, base_url):
        self.browser.get(base_url)
        self.browser.delete_all_cookies()
        time.sleep(8)
        print(f'微博搜索页面{self.browser.current_url}已成功打开...')
        kw = self.browser.find_element(By.XPATH, ('//div[@class="searchbox"]/div[@class="search-input"]/'
                                                  'input[@type="text"]'))
        self.keywords = input('请输入微博搜索的关键词，按回车键确认：')
        print(f'搜索关键词为：{self.keywords}。')
        while True:
            origin = input('搜索所有微博请输入1，按回车键确认，直接按回车键则只搜索原创微博：')
            if origin == '':
                origin = '&scope=ori'
                print('仅搜索原创微博。')
                break
            elif origin == '1':
                origin = '&typeall=1'
                print('搜索全部微博。')
                continue
            else:
                print('输入错误，请重新输入。')
                break
        while True:
            date_time = input('请按年-月-日-时的格式输入抓取微博的发布截止时间（示例：2022-08-03-07），按回车键确认，直接按回车键则截止时间为当前时间：')
            if date_time == '':
                date_format = '%Y-%m-%d-%H'
                date_time = datetime.datetime.now().strftime(date_format)
                date_time = (datetime.datetime.strptime(date_time, date_format) + (datetime.timedelta(hours=+1))).strftime(date_format)
                print('截止时间为：当前时间。')
                break
            elif re.match(r'(2\d{3})-'
                          r'('
                          r'('
                          r'(0[13578]|1[02])-(0[1-9]|[12]\d|3[01])-'
                          r')|'
                          r'('
                          r'(0[469]|11)-(0[1-9]|[12]\d|30)-'
                          r')|'
                          r'('
                          r'02-(0[1-9]|1[\d|2[0-8])-'
                          r')'
                          r'('
                          r'(0)|([01]\d)|(2[0-3])'
                          r')'
                          r')', date_time) is None:
                print('时间格式输入错误，请重新输入！')
                continue
            else:
                print(f'截止时间为：{date_time}。')
                break
        while True:
            page_begin = input('请输入微博列表的抓取起始页（0至50之间），按回车键确认，直接按回车键从第1页开始：')
            if page_begin == '':
                page_begin = ''
                print('抓取起始页为：第1页。')
                break
            elif re.match(r'([1-4]\d|50)', page_begin) is None:
                print('抓取起始页输入错误，请重新输入！')
                continue
            else:
                print(f'抓取起始页为：第{page_begin}页。')
                page_begin = '&page=' + str(page_begin)
                break
        kw.send_keys(self.keywords)
        click_search = self.browser.find_element(By.XPATH, '//div[@class="searchbox"]/button[@class="s-btn-b"]')
        click_search.click()
        time.sleep(1)
        click_list = self.browser.find_element(By.XPATH, '//div[@class ="m-main-nav"]/ul/li[2]/a')
        click_list.click()
        time.sleep(1)
        print(f'微博列表页面{self.browser.current_url}已成功打开，列表按时间倒序排序。')
        with open('cookies.txt', 'r') as f:
            cookies_list = json.load(f)
            for cookie in cookies_list:
                if isinstance(cookie.get('expiry'), float):
                    cookie['expiry'] = int(cookie['expiry'])
                self.browser.add_cookie(cookie)
        self.browser.refresh()
        date_now = time.strptime(date_time, '%Y-%m-%d-%H')
        date_judge = time.strftime('%Y-%m-%d %H', date_now)
        date_now = time.strftime('%Y-%m-%d-%H', date_now)
        date_judge = str(date_judge) + ':00'
        date_judge = time.strptime(date_judge, '%Y-%m-%d %H:%M')
        date_judge = time.strftime('%Y-%m-%d %H:%M', date_judge)
        date_format = '%Y-%m-%d-%H'
        date_past = (datetime.datetime.strptime(date_now, date_format) + datetime.timedelta(days=-31)).strftime(date_format)
        url = self.browser.current_url
        url_change = re.search(r'(.*)(?=q=)', url)
        url = url_change.group() + f'q={self.keywords}{origin}&suball=1&timescope=custom:{date_past}:{date_now}&Refer=g{page_begin}'
        now = datetime.datetime.now()
        print(f'本次抓取的开始时间是：{now}')
        self.auto_search(url, self.keywords, now, origin, date_judge)

    def auto_search(self, url, keywords, now, origin, date_judge, search_times=0):
        if url != self.browser.current_url:
            self.browser.get(url)
        print(f'微博列表页面{self.browser.current_url}已打开，抓取中...')
        time.sleep(1)
        data = etree.HTML(self.browser.page_source)
        post_url = data.xpath('//p[@class="from"]/a[1]/@href')
        df = pandas.DataFrame(
            columns=['微博账号', '发文时间', '发送平台', '微博内容', '转发次数', '评论次数', '点赞次数', '原博地址'])
        for url_single in post_url:
            url = 'https:' + url_single
            print(url)
            self.browser.get(url)
            time.sleep(1)
            post = etree.HTML(self.browser.page_source)
            names = post.xpath('//a[@usercard]/span[@title]/text()')
            print(names)
            times = post.xpath('//a[@title][@href][@class][1]/text()')
            print(times)
            from1 = post.xpath('//div[@class="woo-box-flex"]/div[@title]/text()')
            from2 = post.xpath('//div[@class="woo-box-flex"]/div[contains(@class, "head-info_cut")]/text()')
            from1 = ''.join(from1)
            from2 = ''.join(from2)
            from_all = from1 + from2
            blogs = post.xpath('//div[contains(@class, "detail_text")]/div/text()')
            blogs = ''.join(blogs)
            forward = post.xpath('//span[@class="woo-pop-ctrl"]/div/span/text()')
            forward = [0 if i == ' 转发 ' else i for i in forward]
            if '万' not in forward:
                pass
            else:
                forward = ''.join(forward)
                forward = int(float(forward[0:-1]) * 10000)
            comments = post.xpath('//div[contains(@class, "woo-box-item-flex toolbar_item")]'
                                  '/div[contains(@class, "woo-box-flex")]/span/text()')
            comments = [0 if i == ' 评论 ' else i for i in comments]
            if '万' not in comments:
                pass
            else:
                comments = ''.join(comments)
                comments = int(float(comments[0:-1]) * 10000)
            likes = post.xpath('//div[contains(@class, "toolbar_likebox")]/button/span[@class="woo-like-count"]/text()')
            likes = [0 if i == '赞' else i for i in likes]
            if '万' not in likes:
                pass
            else:
                likes = ''.join(likes)
                likes = int(float(likes[0:-1]) * 10000)
            key_list = ['微博账号', '发文时间', '发送平台', '微博内容', '转发次数', '评论次数', '点赞次数', '原博地址']
            info_list = [names, times, from_all, blogs, forward, comments, likes, url]
            csv_info = dict(zip(key_list, info_list))
            df1 = pandas.DataFrame(csv_info, columns=key_list)
            df = pandas.concat([df, df1])
            self.browser.back()
            search_times += 1
            time.sleep(1)
        df.to_csv('weibo_spider.csv', mode='a', encoding='utf_8_sig', header=False, index=False)
        url = self.browser.current_url
        page_num = url.split('page=')[-1]
        if page_num.isdigit() is False:
            page_num = '1'
        page_num = int(page_num)
        print(f'已成功提取第{page_num}页微博信息并追加写入CSV文件！')
        if page_num == 50:
            post = etree.HTML(self.browser.page_source)
            time_last = (post.xpath('//p[@class="from"]/a[1]/text()'))[-1]
            if '年' in time_last:
                year_num = ''.join(re.findall(r'(\d+)', time_last)[0])
                mon_num = ''.join(re.findall(r'(\d+)', time_last)[1])
                day_num = ''.join(re.findall(r'(\d+)', time_last)[2])
                hour_num = ''.join(re.findall(r'(\d+)', time_last)[3])
                min_num = ''.join(re.findall(r'(\d+)', time_last)[4])
            elif '今天' in time_last:
                year_num = str(datetime.datetime.today().year)
                mon_num = str(datetime.datetime.today().month)
                day_num = str(datetime.datetime.today().day)
                hour_num = ''.join(re.findall(r'(\d+)', time_last)[2])
                min_num = ''.join(re.findall(r'(\d+)', time_last)[3])
            else:
                year_num = str(datetime.datetime.today().year)
                mon_num = ''.join(re.findall(r'(\d+)', time_last)[0])
                day_num = ''.join(re.findall(r'(\d+)', time_last)[1])
                hour_num = ''.join(re.findall(r'(\d+)', time_last)[2])
                min_num = ''.join(re.findall(r'(\d+)', time_last)[3])
            time_last = year_num + '-' + mon_num + '-' + day_num + ' ' + hour_num + ':' + min_num
            time_last = time.strptime(time_last, '%Y-%m-%d %H:%M')
            time_last = time.strftime('%Y-%m-%d-%H', time_last)
            date_format = '%Y-%m-%d-%H'
            time_begin = (datetime.datetime.strptime(time_last, date_format) +
                          datetime.timedelta(days=-31)).strftime(date_format)
            time_end = (datetime.datetime.strptime(time_last, date_format) +
                        datetime.timedelta(hours=+1)).strftime(date_format)
            print(f'提示：本页最后一条微博时间为{time_last}。')
            url = self.browser.current_url
            url_change = re.search(r'(.*)(?=q=)', url)
            url = url_change.group() + f'q={keywords}{origin}&suball=1&timescope=custom:{time_begin}:{time_end}&Refer=g&page=1'
            self.auto_search(url, now, origin, date_judge, search_times)
        click_next = self.browser.find_element(By.XPATH,
                                               '//div[@class="m-page"]/div/a[@class="next"]')
        click_next.click()
        url = self.browser.current_url
        self.auto_search(url, keywords, now, origin, date_judge, search_times)


if __name__ == '__main__':
    gt = GetWeibo()
