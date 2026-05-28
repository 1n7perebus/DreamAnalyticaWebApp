from django.contrib import admin
from django.db.models import Count
from .models import *


class DreamsAdmin(admin.ModelAdmin):
    search_fields = ['email', 'pub', 'country_name', 'city', 'symbols__name']
    list_display = ('email', 'active', 'id', 'name', 'age', 'country_code', 'pub')
    list_filter = ('country_code', 'gender', 'mbti_type', 'active', 'symbols')
    filter_horizontal = ('symbols',)
    ordering = ['-pub', 'email']


class DreamSymbolAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = ('name', 'dream_count')
    ordering = ['name']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(dream_count=Count('dreams'))

    @admin.display(ordering='dream_count')
    def dream_count(self, obj):
        return getattr(obj, 'dream_count', obj.dreams.count())

class ReplyAdmin(admin.ModelAdmin):
    list_display = ('dream','id','pub')
    ordering =['-pub']

class ContactAdmin(admin.ModelAdmin):
    list_display = ('name','id', 'email', 'phone', 'pub')
    ordering =['-pub']

admin.site.register(Dreams, DreamsAdmin)
admin.site.register(DreamSymbol, DreamSymbolAdmin)
admin.site.register(Reply, ReplyAdmin)
admin.site.register(Contact, ContactAdmin)
