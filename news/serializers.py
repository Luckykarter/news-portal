from rest_framework import serializers
from news import models


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Author
        fields = ('first_name', 'last_name',)


class ArticleSerializer(serializers.ModelSerializer):
    author = AuthorSerializer()
    image_url = serializers.SerializerMethodField()

    def get_image_url(self, obj):
        """
        If image attached locally - use it,
        otherwise - use external image
        """
        if obj.image:
            return obj.image.url
        return obj.external_image

    class Meta:
        model = models.Article
        exclude = ('keywords', 'external_image', 'image',)