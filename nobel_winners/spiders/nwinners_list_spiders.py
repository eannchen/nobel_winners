# -*- coding: utf-8 -*-

import scrapy
import re


# 定義要爬取的資料
class NWinnerItem(scrapy.Item):
    country = scrapy.Field()
    name = scrapy.Field()
    link_text = scrapy.Field()


# 建立具名蜘蛛
class NWinnerSpider(scrapy.Spider):
    """ 爬取諾貝爾得獎主的國籍及連結文字 """
    name = 'nwinners_list'
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
                    text = w.xpath('descendant-or-self::text()').extract()
                    yield NWinnerItem(
                        country=country[0],
                        name=text[0],
                        link_text=' '.join(text))
