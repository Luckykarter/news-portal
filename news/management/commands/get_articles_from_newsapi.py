import django.core.management.base as base
from django.conf import settings
import datetime
from news import models
from news.utils import NewsApi
import logging

logger = logging.getLogger(__name__)


def download_articles(query, period):
    news_api = NewsApi(settings.NEWS_PORTAL_KEY)
    articles = news_api.get_articles(query=query, period=period)
    logger.info(f'Found {len(articles)} articles')

    new_articles = []
    for article in articles:
        article_obj, created = models.Article.objects.get_or_create_from_news_api(**article)
        if created:
            new_articles.append(article_obj)
    logger.info(f"Added {len(new_articles)} new articles")
    return new_articles


class Command(base.BaseCommand):
    def add_arguments(self, parser):  # pragma: no cover
        parser.add_argument('--query', required=True,
                            help="query to search news")
        parser.add_argument('--period', type=int, required=True,
                            help="Period of news in days in the past from today")

    def handle(self, *args, **options):
        queries = options.get('query').split(',')
        for q in queries:
            download_articles(q.strip(), options.get('period'))
