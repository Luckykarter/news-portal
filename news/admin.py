from django.contrib import admin
from news import models


class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'description')
    search_fields = ('title', 'description')
    list_filter = ('author',)


class AuthorAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name')
    search_fields = ('email', 'first_name', 'last_name')


admin.site.register(models.Article, ArticleAdmin)
admin.site.register(models.Author, AuthorAdmin)
