import scrapy
import re
from bs4 import BeautifulSoup

BASE_URL = 'https://en.wikipedia.org'


class NWinnerItemBio(scrapy.Item):
    link = scrapy.Field()
    name = scrapy.Field()
    mini_bio = scrapy.Field()
    image_urls = scrapy.Field()
    bio_image = scrapy.Field()
    images = scrapy.Field()


class NWinnerSpiderBio(scrapy.Spider):
    name = 'nwinners_minbio'
    custom_settings = {
        'ITEM_PIPLINES': {
            'nobel_winners.pipelines.NobelImagesPipeline': 1
        },
        'IMAGES_STORE': 'images'
    }
    allowed_domains = ['en.wikipedia.org']
    start_urls = [
        'https://en.wikipedia.org/wiki/List_of_Nobel_laureates_by_country'
    ]

    def parse(self, response):
        # filename = response.url.split('/')[-1]
        # h2s = response.xpath('//h2')
        soup = BeautifulSoup(response.body, 'html.parser')
        h2s = soup.find_all('h2')

        for h2 in h2s:
            country = h2.find('span', class_='mw-headline')
            if country:
                winners = h2.find_next_sibling('ol')
                for w in winners.find_all('li'):
                    wdata = {}
                    wdata['link'] = BASE_URL + w.find('a').attrs['href']
                    request = scrapy.Request(
                        wdata['link'], callback=self.get_mini_bio)
                    request.meta['item'] = NWinnerItemBio(**wdata)
                    yield request

    def get_mini_bio(self, response):
        """ 取得得主傳記描述與照片 """
        BASE_URL_ESCAPED = 'https:\/\/en.wikipedia.org'
        item = response.meta['item']
        soup = BeautifulSoup(response.body, 'html.parser')

        item['image_urls'] = []

        img_src = soup.find('table', class_='infobox').find('img').attrs['src']
        if img_src:
            item['image_urls'] = ['https:' + img_src]

        mini_bio = ''
        paras = soup.find(id='mw-content-text').find_all('p')

        for p in paras:
            if p.string == None:
                mini_bio += str(p)

        mini_bio = mini_bio.replace('href="/wiki',
                                    'href="' + BASE_URL + '/wiki')
        mini_bio = mini_bio.replace('href="#', item['link'] + '#')
        item['mini_bio'] = mini_bio
        yield item