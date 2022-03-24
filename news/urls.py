from rest_framework import routers

from django.conf.urls import url
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from django.urls import path, include
from news import views

api_router = routers.DefaultRouter()

api_router.register('articles', views.ArticleViewSet, basename='articles')

schema_view_garage = get_schema_view(
    openapi.Info(
        title="News Portal API",
        default_version='v1',
        description="The set of APIs for serving News Portal<br>"
                    "<small>Home task of Egor Wexler for Breitling SA</small>",
        contact=openapi.Contact(email="egor.wexler@icloud.com"),
    ),
    public=True,
)


urlpatterns = [
    path('api/', include(api_router.urls)),
    path('swagger/', schema_view_garage.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui-news'),
]
