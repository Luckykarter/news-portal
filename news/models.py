import datetime

import pytz
from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from news.utils import NewsApi
from django.utils import timezone


class Author(models.Model):
    UNKNOWN = 'Unknown Author'

    # in case Author is registered in the application - Django User model can be used instead
    # user = models.ForeignKey(User, on_delete=models.CASCADE)

    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(blank=True)
    username = models.CharField(max_length=150)

    objects = models.Manager()

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class ArticleManager(models.Manager):
    def get_or_create_from_news_api(self, author=None, title='', description='',
                                    urlToImage='', publishedAt=None, content='', url=None, **kwargs):
        """
        Takes one article from newsapi.org and saves it to DB
        All parameters per response of newsapi.org

        Repeats the behaviour of standard objects.get_or_create()

        :return tuple:  object created or fetched, True/False if object was created
        """
        # if url is None:
        #     return None, False

        try:
            return self.get_queryset().get(external_url=url), False
        except ObjectDoesNotExist:
            pass

        if author is None:
            first_name, last_name = Author.UNKNOWN.split()
            obj_author, _ = Author.objects.get_or_create(
                username=Author.UNKNOWN, first_name=first_name, last_name=last_name
            )
        else:
            tokens = author.split()
            username = first_name = tokens[0]
            if len(tokens) > 1:
                last_name = tokens[1]
            else:
                last_name = ''
            obj_author, _ = Author.objects.get_or_create(
                username=username, first_name=first_name, last_name=last_name
            )

        try:
            timestamp = datetime.datetime.strptime(publishedAt, NewsApi.DATETIME_FORMAT)
            timestamp = pytz.utc.localize(timestamp)
        except ValueError:
            timestamp = timezone.now()

        # remove truncation e.g. [+1234 chars] from content
        try:
            idx = content.index('[+')
            content = content[:idx]
        except ValueError:
            pass

        article = self.create(
            title=title,
            description=content,
            author=obj_author,
            timestamp=timestamp,
            external_url=url,
            external_image=urlToImage,
        )

        return article, True


class Keyword(models.Model):
    """
    Helper table for faster lookup of articles by keywords
    """
    name = models.CharField(max_length=255, unique=True)
    objects = models.Manager()


class Article(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=timezone.now)
    image = models.ImageField(upload_to='news_images', blank=True)
    external_image = models.URLField(blank=True, default=None, null=True, max_length=2048)
    external_url = models.URLField(help_text="URL of the article if it's from external source", max_length=2048,
                                   blank=True)
    keywords = models.ManyToManyField(Keyword, blank=True)

    objects = ArticleManager()

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super().save(force_insert, force_update, using, update_fields)

        for fld in [self.title, self.description]:
            words = {"".join([y for y in x.lower() if y.isalnum()]) for x in str(fld).split() if 3 < len(x) < 255}
            for name in words:
                keyword, _ = Keyword.objects.get_or_create(name=name)
                self.keywords.add(keyword)

    def __str__(self):
        return self.title
