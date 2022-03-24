from rest_framework import serializers
from news import models


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Author
        fields = ('first_name', 'last_name', 'email')


class ArticleSerializer(serializers.ModelSerializer):
    author = AuthorSerializer()
    image_url = serializers.SerializerMethodField()

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return obj.external_image

    class Meta:
        model = models.Article
        exclude = ('keywords',)