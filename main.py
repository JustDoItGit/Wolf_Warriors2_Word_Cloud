import requests # 安装request第三方库：pip3 install requests,这里关键是requests库，安装方法视你的具体环境
try:
    import cookielib
except:
    import http.cookiejar as cookielib
import re
import time
import os.path
import json
from bs4 import BeautifulSoup   # 安装第三方库 bs4 ：pip3 install bs4
try:
    from PIL import Image   # 安装第三方库 Pillow ：pip3 install Pillow
except:
    pass

# 从 mywordCloud.py 里导入函数
from mywordCloud import save_jieba_result
from mywordCloud import draw_wordcloud

import threading
import codecs
# 构造Request headers请求头
# agent 的内容视你的系统和浏览器而定：我这里是macOS系统，chrome谷歌浏览器
agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36"
headers = {
    "Host":"www.douban.com",
    "Referer":"https://www.douban.com",
    'User-Agent': agent,
}

# 使用cookie登录信息
session = requests.session()
session.cookies = cookielib.LWPCookieJar(filename='cookies')

try:
    session.cookies.load(ignore_discard=True)
    print("成功加载cookie")
except:
    print("cookie未能加载")

# 获取验证码
def get_captcha(url):
    # 获取验证码：
    print('获取验证码',url)
    captcha_url = url
    r = session.get(captcha_url, headers=headers)
    print('test')
    with open('captcha.jpg', 'wb') as f:
        f.write(r.content)
        f.close()
    # 用pillow 的 Image 显示验证码，如果不就的将来验证码技术发生变化，这里就要另想办法
    # 如果没有安装 pillow 到源代码所在的目录去找到验证码然后手动输入
    try:
        im = Image.open('captcha.jpg')
        im.show()
        im.close()
    except:
        print(u'请到 %s 目录找到captcha.jpg 手动输入' % os.path.abspath('captcha.jpg'))
    captcha = input("please input the captcha 请输入验证码：\n>")
    return captcha
def isLogin():
    # 登录个人主页，查看是否登录成功
    url = "https://www.douban.com/people/zheteng6/"  #这里不同用户不一样,这里是你所登录账户的主页地址
    login_code = session.get(url, headers=headers, allow_redirects=False).status_code
    if login_code == 200:
        return True
    else:
        return False

def login(acount,secret):
    douban = "https://www.douban.com/"
    htmlcha = session.get(douban, headers=headers).text
    patterncha = r'id="captcha_image" src="(.*?)" alt="captcha"'
    httpcha = re.findall(patterncha,htmlcha)
    pattern2 = r'type="hidden" name="captcha-id" value="(.*?)"'
    hidden_value = re.findall(pattern2,htmlcha)
    print(hidden_value)

    post_data = {
        "source": "index_nav",
        'form_email': acount,
        'form_password': secret
    }
    if len(httpcha) > 0:
        print('验证码链接', httpcha)
        capcha = get_captcha(httpcha[0])
        post_data['captcha-solution'] = capcha
        post_data['captcha-id'] = hidden_value[0]

    print(post_data)
    post_url = 'https://www.douban.com/accounts/login'
    login_page = session.post(post_url, data=post_data, headers=headers)
    # 保存cookies
    session.cookies.save()

    if isLogin():
        print('登录成功')
    else:
        print('登录失败')

def get_movie_sort():
    time.sleep(1)
    movie_url = 'https://movie.douban.com/chart'
    html = session.get(movie_url, headers=headers)
    soup = BeautifulSoup(html.text, 'html.parser')
    result = soup.find_all('a', {'class':'nbg'})
    print(result)

#爬取短评论
def get_comment(filename):  #filename为爬取得内容保存的文件
    begin=1
    next_url='?start=20&limit=20&sort=new_score&status=P'
    f=open(filename,'w+',encoding='utf-8')
    while(True):
        time.sleep(5)
        comment_url='https://movie.douban.com/subject/26363254/comments' # 这里是你账户所登录的战狼2影评页面
        data={
            'start':'27',
            'limit':'-20',
            'sort':'new_score',
            'status':'P'
        }
        headers2 = {
            "Host": "movie.douban.com",
            "Referer": "https://www.douban.com/",
            'User-Agent': agent,
            'Connection': 'keep-alive',
        }

        html=session.get(url='https://movie.douban.com/subject/26363254/comments'+next_url,headers=headers2)
        soup=BeautifulSoup(html.text,'html.parser')

        # 爬取当前页面所有评论
        result = soup.find_all('div', {'class': 'comment'}) # 爬取的所有的短评
        pattern4 = r'<p class="">(.*?)</p>'
        for item in result:
            s = str(item)
            count2 = s.find('<p class="">')
            count3 = s.find('</p>')
            s2 = s[count2+12:count3]    # 抽取字符串中的评论
            if 'class' not in s2:
                f.write(s2)

        # 获取下一页的链接
        next_url = soup.find_all('div', {'id':'paginator'})
        pattern3 = r'href="(.*?)">后页'
        if len(next_url) == 0:
            break
        next_url = re.findall(pattern3, str(next_url[0]))   # 得到后页的链接
        if len(next_url) == 0:    # 如果没有后页的链接跳出循环
            break
        next_url = next_url[0]
        print('%d爬取下一页评论...' % begin)
        begin = begin + 1
        # 如果爬取了5次，则多休息2秒
        if begin % 6 == 0:
            time.sleep(30)
            print('休息...')
        print(next_url)
    f.close()

# 多线程爬虫，爬取豆瓣影评
def thread_get_comment(filename):
    next_url = '?start=19&limit=20&sort=new_score&status=P'
    headers2 = {
        "Host": "movie.douban.com",
        "Referer": "https://www.douban.com/",
        'User-Agent': agent,
        'Connection': 'keep-alive',
    }

    f = open(filename, 'w+', encoding='utf-8')
    comment_url = "https://movie.douban.com/subject/26363254/comments"   # 这里是你账户所登录的战狼2影评页面
    crawl_queue = [comment_url+next_url]
    crawl_queue.append('https://movie.douban.com/subject/26363254/comments?start=144&limit=20&sort=new_score&status=P')
    seen = set(crawl_queue)

    def process_queue():
        begin = 1
        while True:
            try:
                url = crawl_queue.pop()
            except IndexError:
                break
            else:
                time.sleep(5)
                html = session.get(url=url, headers=headers2)
                soup = BeautifulSoup(html.text, 'html.parser')

                # 爬取当前页面的所有评论
                result = soup.find_all('div', {'class': 'comment'})     # 爬取的所有的短评
                pattern4 = r'<p class="(.*?)"</p>'
                for item in result:
                    s = str(item)
                    count2 = s.find('<p class="">')
                    count3 = s.find('</p>')
                    s2 = s[count2 + 12:count3] # 抽取字符串中的评论
                    if 'class' not in s2:
                        f.write(s2)

                # 获取下一页的链接
                next_url = soup.find_all('div', {'id': 'paginator'})
                pattern3 = r'href="(.*?)">后页'
                if len(next_url) == 0:
                    break
                next_url = re.findall(pattern3, str(next_url[0])) # 得到后页的链接
                if len(next_url) == 0: # 如果后页没有链接就跳出循环
                    break
                next_url = next_url[0]
                print('%d爬取下一页评论...' % begin)
                begin = begin + 1
                # 如果爬取了6次这多休息2秒
                if begin % 6 == 0:
                    print('休息...')
                    time.sleep(30)

                print(next_url)
                if comment_url+next_url not in seen:
                    seen.add(comment_url+next_url)
                    crawl_queue.append(comment_url+next_url)

    threads = []
    max_threads = 5
    while threads or crawl_queue:
        for thread in threads:
            if not thread.is_alive():
                threads.remove(thread)
        while len(threads) < max_threads and crawl_queue:
            thread = threading.Thread(target=process_queue)
            print('------下一个线程------')
            thread.setDaemon(True)   # set daemon so main thread can exit when receive ctrl + C
            thread.start()
            threads.append(thread)
        time.sleep(2)

    f.close()

if __name__ == '__main__':
    if isLogin():
        print('您已经登录')
    else:
        print('xs')
        login('120852174@qq.com','doubanzt')

    file_name = 'key3.txt'
    # get_comment(file_name)  # 单线程爬虫
    thread_get_comment(file_name)   #多线程爬虫
    save_jieba_result(file_name)
    draw_wordcloud('pjl_jieba.txt')