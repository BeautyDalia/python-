# coding:utf-8


from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
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
        self.driver.get('https://www.ap.org/en-us/')

        self.wait.until(ec.presence_of_element_located((By.ID, "search-input")))
        time.sleep(2)

        input_field = self.driver.find_element_by_id('search-input')
        input_field.click()

        input_field.send_keys(self.keywords)
        input_field.send_keys(Keys.ENTER)
        time.sleep(4)

        return self.driver.page_source

    def get_news_list(self, pages):      # 列表

        ps = etree.HTML(pages, parser=etree.HTMLParser(encoding='utf-8'))

        news_list = ps.xpath('.//div[@id="searchResultsContent"]/article')

        url_list = []
        time_list = []

        for new in news_list:
            url = new.xpath('.//h3/a/@href')[0].strip()
            url = 'https://www.ap.org' + url
            ntime = new.xpath('.//time/text()')
            ntime = ntime[0] if ntime else ''

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
        js = "window.scrollTo(0,document.body.scrollHeight)"  # 滚动到底部
        self.driver.execute_script(js)
        time.sleep(1)

        nb = './/ul[@class="c-pager__list u-list-reset u-clearfix"]//a[contains(text(),"Next")]'

        return self.driver.find_elements_by_xpath(nb)


if __name__ == '__main__':
    with open('./meilian_data.csv', 'a', newline='', encoding='utf-8') as f:
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
                         "government work report",
                         "NPC session",
                         "China-People’s Congress",
                         "two sessions"]

        for keyword in keywords_list:
            print('==============>>>当前 关键字：', keyword)
            n = News(keyword, f)

            n.parse_detail()

