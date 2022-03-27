import requests
import datetime


class NewsApi:
    DATE_FORMAT = '%Y-%m-%d'
    DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'

    def __init__(self, api_key):
        self.api_key = api_key
        self.url = 'https://newsapi.org/v2/everything'

    def get_articles(self, query, period=0):
        from_date = datetime.datetime.now() - datetime.timedelta(days=period)
        if isinstance(from_date, datetime.datetime):
            from_date = from_date.strftime(self.DATE_FORMAT)

        res = requests.get(self.url, params={
            'q': query,
            'from': from_date,
            'apiKey': self.api_key
        })
        if not res.ok:
            raise requests.HTTPError(res.content.decode())
        res = res.json()
        if 'articles' not in res:   # pragma: no cover
            raise RuntimeError(f'Response from {self.url} does not contain "articles"')
        return res['articles']
