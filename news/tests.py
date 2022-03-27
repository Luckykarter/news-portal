import pytest

from requests import HTTPError
from news import models, serializers, views
from news.utils import NewsApi
from news.management.commands.get_articles_from_newsapi import Command as GetArticles
from django.conf import settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

ARTICLES = [
    {
        "author": None,
        "title": "Swiss stocks - Factors to watch on March 7 - Reuters.com",
        "description": "Here are some of the main factors that may affect Swiss stocks on Monday:",
        "url": "https://www.reuters.com/markets/stocks/swiss-stocks-factors-watch-march-7-2022-03-07/",
        "urlToImage": "https://www.reuters.com/pf/resources/images/reuters/reuters-default.png?d=77",
        "publishedAt": "2022-03-07T05:54:00Z",
        "content": "ZURICH/BERLIN, March 7 (Reuters) - Here are some of the main factors that may affect Swiss stocks"
    },
    {
        "author": "Kaitlyn Cimino",
        "title": "The best luxury smartwatches from Louis Vuitton, Tag Heuer, and more",
        "description": "There is a wearable for nearly every type of user and for every budget. If splurging is on your agenda, check out these luxury smartwatches.",
        "url": "https://www.androidauthority.com/luxury-smartwatches-3137977/",
        "urlToImage": "https://www.androidauthority.com/wp-content/uploads/2021/11/Louis-Vuitton-Tambour-Horizon-Light-Up-scaled.jpg",
        "publishedAt": "0000000000",
        "content": "Wearables come in all shapes, sizes, and price points. If you have money to spare, there are plenty of expensive options up for grabs. Read on to find out more about some of the best luxury smartwatc…"
    },
    {
        "author": "info@hypebeast.com",
        "title": "Sir Michael Caine's Gold Rolex Oysterquartz Breaks World Record At Auction",
        "description": "A collection of personal items, including watches, belonging to legendary actor Sir Michael Caine and his wife have sold at auction in London.The star lot of ‘Sir Michael Caine: The Personal Collection Sale’ at Bonhams London was an 18K yellow gold Rolex Oyst…",
        "url": "https://hypebeast.com/2022/3/sir-michael-caines-rolex-oysterquartz-sells-auction-166600-usd",
        "urlToImage": "https://image-cdn.hypb.st/https%3A%2F%2Fhypebeast.com%2Fimage%2F2022%2F03%2Fsir-michael-caines-rolex-oysterquartz-sells-auction-166600-usd-tw.jpg?w=960&cbr=1&q=90&fit=max",
        "publishedAt": "2022-03-04T18:24:28Z",
        "content": "A collection of personal items, including watches, belonging to legendary actor Sir Michael Caine and his wife have sold at auction in London.\r\nThe star lot of Sir Michael Caine: The Personal Collect… [+1486 chars]"
    }
]

MOCK_IMAGE = (
    b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
    b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
    b'\x02\x4c\x01\x00\x3b'
)

NEWS_API_OPTIONS = {
    "query": 'test',
    "period": 3
}

pytestmark = pytest.mark.django_db


@pytest.fixture(scope='session')
def news_api():
    return NewsApi(settings.NEWS_PORTAL_KEY)


@pytest.fixture(scope="session")
def list_articles_url():
    return reverse('articles-list')


@pytest.fixture(scope="session")
def download_url():
    return reverse('articles-download-articles-from-newsapi')


class TestArticle:
    @pytest.mark.parametrize('article_json', ARTICLES)
    def test_save_from_news_api(self, article_json):
        article, _ = models.Article.objects.get_or_create_from_news_api(**article_json)
        assert article.title == article_json['title']
        assert str(article) == article_json['title']

        article_serialized = serializers.ArticleSerializer(article).data
        assert article_serialized['image_url'] == article_json['urlToImage']

    def test_add_author(self):
        first_name = 'John'
        last_name = 'Appleseed'

        author = models.Author.objects.create(first_name=first_name, last_name=last_name)
        assert str(author) == f'{first_name} {last_name}'

    def test_get_from_news_api(self, news_api):
        news_articles = news_api.get_articles(**NEWS_API_OPTIONS)
        assert len(news_articles) > 0
        assert isinstance(news_articles[0], dict)

    def test_fail_get_from_news_api(self, news_api):
        try:
            news_api.get_articles(query='test', period=10000)
            assert False
        except HTTPError:
            assert True

    def test_get_articles(self):
        cmd = GetArticles()
        cmd.handle(**NEWS_API_OPTIONS)
        assert models.Article.objects.all().exists()


class TestArticleView:
    def test_get_all_articles(self, client, list_articles_url):
        response = client.get(list_articles_url)
        assert response.status_code == 200

    def test_get_by_keywords(self, client, list_articles_url):
        obj, _ = models.Article.objects.get_or_create_from_news_api(**ARTICLES[1])
        keywords = 'price,points'
        response = client.get(
            list_articles_url, {'keywords': keywords}
        )
        assert response.status_code == 200
        data = response.json()['results'][0]
        for k in keywords.split(','):
            assert k in data['title'].lower() or k in data['description'].lower()

    def test_no_keyword(self, client, list_articles_url):
        response = client.get(
            list_articles_url, {'keywords': 'for_sure_no_such_word'}
        )
        assert response.status_code == 200
        assert len(response.json()['results']) == 0

    @pytest.mark.parametrize(
        'param,modifier', [
            ('from_date', -1),
            ('to_date', 1)
        ]
    )
    def test_dates_filter(self, param, modifier, client, list_articles_url):
        article_1, _ = models.Article.objects.get_or_create_from_news_api(**ARTICLES[0])
        article_2, _ = models.Article.objects.get_or_create_from_news_api(**ARTICLES[1])

        timestamp_1 = timezone.now()

        timestamp_2 = timestamp_1 + timezone.timedelta(days=30) * modifier
        timestamp_3 = timestamp_1 + timezone.timedelta(days=10) * modifier

        article_1.timestamp = timestamp_1
        article_2.timestamp = timestamp_2

        article_1.save()
        article_2.save()

        # both must be there
        response = client.get(
            list_articles_url, {param: timestamp_2.strftime(views.ArticleViewSet.date_format)}
        )
        ids = [x['id'] for x in response.json()['results']]
        assert article_1.id in ids
        assert article_2.id in ids

        # only new one must be there
        response = client.get(
            list_articles_url, {param: timestamp_3.strftime(views.ArticleViewSet.date_format)}
        )
        ids = [x['id'] for x in response.json()['results']]
        assert article_1.id in ids
        assert article_2.id not in ids

    def test_image_url(self, client, list_articles_url):
        test_image_name = 'test_image'
        article, _ = models.Article.objects.get_or_create_from_news_api(**ARTICLES[1])
        article.image = SimpleUploadedFile(name=f'{test_image_name}.gif', content=MOCK_IMAGE, content_type='image/gif')
        article.save()
        article_serialized = serializers.ArticleSerializer(article).data
        assert article_serialized['image_url'] != ARTICLES[1]['urlToImage']
        assert test_image_name in article_serialized['image_url']

    def test_wrong_date_format(self, client, list_articles_url):
        response = client.get(
            list_articles_url, {'from_date': '2022-31-31'}
        )
        assert response.status_code == 400

    def test_api_of_articles(self, client, download_url):
        response = client.get(download_url, {'query': 'test', 'period': 2})
        assert response.status_code == 200

    @pytest.mark.parametrize('params', [
        {},
        {'query': 'test'},
        {'query': 'test', 'period': 'abc'},
    ])
    def test_api_of_articles_negative(self, client, download_url, params):
        response = client.get(download_url, params)
        assert response.status_code == 400
