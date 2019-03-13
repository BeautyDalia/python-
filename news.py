# coding:utf-8

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select
import time
from selenium.webdriver.chrome.options import Options
from lxml import etree
from newspaper import Article
import dateparser
import csv


class News(object):

    def __init__(self, keywords, file):
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--disable-gpu')

        self.driver = webdriver.Chrome()
        self.wait = WebDriverWait(self.driver, 10)
        # self.driver.set_page_load_timeout(10)
        # self.driver.set_script_timeout(10)

        self.keywords = keywords

        self.num = 0   # 翻页
        self.s = 0     # 是否起始页
        self.f = file

    def get_select_content(self):     # 首页
        self.driver.get('https://www.reuters.com')

        self.wait.until(ec.presence_of_element_located((By.CLASS_NAME, "search-icon")))
        time.sleep(2)

        search = self.driver.find_element_by_class_name('search-icon')
        search.click()
        time.sleep(2)
        input_field = self.driver.find_element_by_id('searchfield')
        input_field.click()

        input_field.send_keys(self.keywords)
        input_field.send_keys(Keys.ENTER)
        time.sleep(4)

        Select(self.driver.find_element_by_class_name('sort-selector')).select_by_visible_text('Date')
        time.sleep(3)
        return self.driver.page_source

    def get_news_list(self, pages):      # 列表

        before = self.num * 10
        after = (self.num + 1) * 10 + 1

        ps = etree.HTML(pages, parser=etree.HTMLParser(encoding='utf-8'))

        news_list = ps.xpath('.//div[@class="search-result-indiv"][position()>{}][position()<{}]'.format(before, after))

        url_list = []
        time_list = []

        for new in news_list:
            url = new.xpath('.//a/@href')[0].strip()
            url = 'https://www.reuters.com' + url
            ntime = new.xpath('.//h5/text()')[0].strip()

            url_list.append(url)
            time_list.append(ntime)

        return zip(url_list, time_list)

    def parse_detail(self, p=''):      # 详情解析
        if self.s == 0:
            news_info = self.get_news_list(self.get_select_content())
        else:
            news_info = self.get_news_list(p)

        nwriter = csv.writer(self.f, dialect='excel')
        for url, ntime in news_info:
            try:
                a = Article(url)
                a.download()
                a.parse()

                news_url = url
                content = a.text
                title = a.title
                news_time = dateparser.parse(ntime)

                info = [news_url, title, content, news_time]
                # try:
                nwriter.writerow(info)
                print('======>>>写入成功：', news_url)
                # except UnicodeEncodeError as e:
                #     print('写入错误，错误为：', e)
                #     continue
            except Exception as e:
                print('======>>>发生错误:', e)
                print('======>>>下载失败，url:', url)
                continue
        load_more_ele = self.load_more()

        if load_more_ele:
            load_more_ele[0].click()
            time.sleep(4)
            self.s = 1

            ps = self.driver.page_source
            self.parse_detail(ps)

        else:
            print('====>>>当前关键字爬完：', self.keywords)
            self.driver.quit()

    def load_more(self):
        self.num += 1
        js = "window.scrollTo(0,document.body.scrollHeight)"  # 滚动到底部
        self.driver.execute_script(js)
        time.sleep(1)

        nb = './/div[@class="search-result-more"]/div[@class="search-result-more-txt"]'
        return self.driver.find_elements_by_xpath(nb)


if __name__ == '__main__':
    with open('./lianghui_data.csv', 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, dialect='excel')
        index = ['news_url', 'title', 'content', 'news_time']
        writer.writerow(index)

        keywords_list = [# 'annual session of China',
                         # 'China’s annual meeting of parliament',
                         # "National People's Congress",
                         # "Chinese People's Political Consultative Conference （NPC &CPPCC）",
                         # "Supreme People's Court (SPC)",
                         # "Zhou Qiang, the President of the Supreme People's Court",
                         # "Report on the Work of the Government",
                         # "government work report",
                         # "NPC session",
                         # "China-People’s Congress",
                         "two sessions"]

        for keyword in keywords_list:
            print('==============>>>当前 关键字：', keyword)
            n = News(keyword, f)

            n.parse_detail()
