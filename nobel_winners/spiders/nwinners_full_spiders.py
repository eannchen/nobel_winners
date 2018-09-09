# -*- coding: utf-8 -*-

import scrapy
import re

BASE_URL = 'https://en.wikipedia.org'


# 國家、姓名、年份、獎項分類、個人履歷網址
def process_winner_li(w, country=None):
    """ 處理得主的 <li> 標籤，加入出身國家或國籍，視情況而定。 """
    wdata = {}
    wdata['link'] = BASE_URL + w.xpath('a/@href').extract()[0]
    text = ' '.join(w.xpath('descendant-or-self::text()').extract())
    # 從逗號前取得姓名，並清除左右空白
    wdata['name'] = text.split(',')[0].strip()
    # \d{4} 四個數字
    year = re.findall('\d{4}', text)
    if year:
        wdata['year'] = int(year[0])
    else:
        wdata['year'] = 0
        print('Oops, no year in ', text)

    category = re.findall(
        'Physics|Chemistry|Physiology or Medicine|Literature|Peace|Economics',
        text)
    if category:
        wdata['category'] = category[0]
    else:
        wdata['category'] = ''
        print('Oops, no category in ', text)

    if country:
        # 得主姓名後面跟著星號，代表國家是得主的出生地
        if text.find('*') != -1:
            wdata['country'] = ''
            wdata['born_in'] = country
        else:
            wdata['country'] = country
            wdata['born_in'] = ''

    # 提供後續修正
    wdata['text'] = text
    return wdata


# 定義要爬取的資料
class NWinnerItem(scrapy.Item):
    name = scrapy.Field()
    link = scrapy.Field()
    year = scrapy.Field()
    category = scrapy.Field()
    country = scrapy.Field()
    gender = scrapy.Field()
    born_in = scrapy.Field()
    date_of_birth = scrapy.Field()
    date_of_death = scrapy.Field()
    place_of_birth = scrapy.Field()
    place_of_death = scrapy.Field()
    text = scrapy.Field()


# 建立具名蜘蛛
class NWinnerSpider(scrapy.Spider):
    """ 爬取諾貝爾得獎主的國籍及連結文字 """
    name = 'nwinners_full'
    allowed_domains = ['en.wikipedia.org']
    start_urls = [
        'https://en.wikipedia.org/wiki/List_of_Nobel_laureates_by_country'
    ]

    # parse 處理 HTTP 回應
    def parse(self, response):
        h2s = response.xpath('//h2')

        for h2 in h2s:
            country = h2.xpath('span[@class="mw-headline"]//text()').extract()
            print(country)
            if country:
                winners = h2.xpath('following-sibling::ol[1]')
                for w in winners.xpath('li'):
                    wdata = process_winner_li(w, country[0])
                    request = scrapy.Request(
                        wdata['link'],
                        callback=self.parse_bio,  # 回呼函式
                        dont_filter=True)
                    # 將 process_winner_li 爬取到的資料初始化，附加到請求的後設資料，讓回呼函式能夠存取
                    request.meta['item'] = NWinnerItem(**wdata)
                    # 請求，使 parse 成為請求產生器
                    yield request

    def parse_bio(self, response):
        # 從後設資料取得 item
        item = response.meta['item']
        href = response.xpath("//li[@id='t-wikibase']/a/@href").extract()
        if href:
            href = ''.join(href[0].split('/Special:EntityPage'))
            request = scrapy.Request(
                href, callback=self.parse_wikidata, dont_filter=True)
            request.meta['item'] = item
            yield request

    def parse_wikidata(self, response):
        item = response.meta['item']
        property_codes = [{
            'name': 'date_of_birth',
            'code': 'P569'
        }, {
            'name': 'date_of_death',
            'code': 'P570'
        }, {
            'name': 'place_of_birth',
            'code': 'P19',
            'link': True
        }, {
            'name': 'place_of_death',
            'code': 'P20',
            'link': True
        }, {
            'name': 'gender',
            'code': 'P21',
            'link': True
        }]

        p_template = '//*[@id="{code}"]/div[2]/div[1]/div/div[2]/div[2]/div[1]{link_html}/text()'

        for prop in property_codes:
            link_html = ''
            if prop.get('link'):
                link_html = '/a'
            sel = response.xpath(
                p_template.format(code=prop['code'], link_html=link_html))
            if sel:
                item[prop['name']] = sel[0].extract()

        yield item
