from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import json

browser_options = Options()
browser = webdriver.Chrome(chrome_options=browser_options)
headers = {'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) '
                         'AppleWebKit/537.36 (KHTML, like Gecko) Chrome'
                         '/103.0.0.0 Safari/537.36'}
print("浏览器已成功创建。")


def get_cookie(url='https://weibo.com/login.php'):
    url = url
    browser.get(url)
    print('请在25秒内，使用微博APP扫码登录你的账号...')
    time.sleep(25)
    with open('cookies.txt', 'w') as f:
        f.write(json.dumps(browser.get_cookies()))
        f.close()
    print('已成功保存cookie信息。')


if __name__ == '__main__':
    get_cookie()
