import datetime
import pytz

from rest_framework import viewsets, mixins, status, filters
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action
from django.core.exceptions import ObjectDoesNotExist
from news import serializers, models
from news.management.commands.get_articles_from_newsapi import download_articles
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from django.conf import settings


def getter(func):
    """
    Decorator of function that needs additional logic to get value from request
    In case parameter is not in request - returns None
    :param func:
    :return:
    """

    def wrap(*args, **kwargs):
        obj, parameter = args
        res = obj.request.GET.get(parameter)
        if not res:
            return None
        return func(obj, res)

    return wrap


class ArticleViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.ArticleSerializer
    model = models.Article
    date_format = '%Y-%m-%d'
    date_verbose_format = 'YYYY-MM-DD'
    filter_fields = ('title', 'description', 'timestamp')

    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['timestamp', 'author', 'title']

    queryset = model.objects.all()
    _filter = {}

    @getter
    def _get_timestamp(self, value):
        try:
            timestamp = datetime.datetime.strptime(value, self.date_format)
            return pytz.utc.localize(timestamp)
        except ValueError:
            raise ValidationError(f"{value} has wrong date format. Expected: {self.date_verbose_format}")

    @getter
    def _get_list(self, value):
        return [x.strip() for x in value.split(',')]


    def _add_to_filter(self, parameter, value):
        if value:
            self._filter[parameter] = value

    def get_queryset(self):
        self._filter = {}
        queryset = self.model.objects.all()

        self._add_to_filter('timestamp__gte', self._get_timestamp('from_date'))
        to_date = self._get_timestamp('to_date')
        if to_date:
            to_date += datetime.timedelta(days=1)   # adding one day to make it inclusive
        self._add_to_filter('timestamp__lte', to_date)

        queryset = queryset.filter(**self._filter)

        keywords = self._get_list('keywords')
        if keywords:
            for keyword in keywords:
                try:
                    k = models.Keyword.objects.get(name=keyword)
                    queryset = queryset.filter(keywords=k)
                except ObjectDoesNotExist:
                    return self.model.objects.none()
        return queryset

    query = openapi.Parameter(
        'query', openapi.IN_QUERY,
        description="Search query for the news to get",
        type=openapi.TYPE_STRING,
        required=True
    )
    period = openapi.Parameter(
        'period', openapi.IN_QUERY,
        description="Period (from today) in the past to get the news",
        type=openapi.TYPE_INTEGER,
        required=True
    )

    @swagger_auto_schema(method='get', manual_parameters=[query, period])
    @action(detail=False, methods=['get'])
    def download_articles_from_newsapi(self, request, **kwargs):
        """
        Call to this endpoint downloads articles from newsapi.org
        """
        query = request.GET.get('query')
        if not query:
            raise ValidationError('query parameter is mandatory')
        period = request.GET.get('period')
        if not period:
            raise ValidationError('period parameter is mandatory')
        try:
            period = int(period)
        except ValueError:
            raise ValidationError('period parameter must be numeric')

        try:
            new_articles = download_articles(query, period)
            return Response(data=serializers.ArticleSerializer(new_articles, many=True).data)
        except Exception as e:  # pragma: no cover
            raise ValidationError(str(e))
