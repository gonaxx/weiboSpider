import requests
from lxml import etree
from lxml import html
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import re
import datetime
import time
import pandas
import json

browser_options = Options()
# browser_options.add_argument("--headless")
# browser_options.add_argument('--no-sandbox')
browser = webdriver.Chrome(chrome_options=browser_options)
headers = {'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) '
                         'AppleWebKit/537.36 (KHTML, like Gecko) Chrome'
                         '/103.0.0.0 Safari/537.36'}
print("浏览器已成功创建。")


def get_cookie(url1='https://weibo.com/login.php'):
    url1 = url1
    browser.get(url1)
    print('请登录账号...')
    time.sleep(25)
    # 登录账号获取cookie
    with open('cookies.txt', 'w') as f:
        # 将cookies保存为json格式
        f.write(json.dumps(browser.get_cookies()))
        f.close()
    print('已成功保存cookie信息。')


get_cookie()

