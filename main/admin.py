from django.contrib import admin
from .models import *


class DreamsAdmin(admin.ModelAdmin):
    search_fields = ['email', 'pub', 'country_name', 'city']
    list_display = ('active','email', 'id', 'name', 'age', 'country_code', 'pub')
    list_filter = ('country_code', 'gender', 'mbti_type', 'active')
    ordering = ['-pub', 'email']

class ReplyAdmin(admin.ModelAdmin):
    list_display = ('dream','id','pub')
    ordering =['-pub']

class ContactAdmin(admin.ModelAdmin):
    list_display = ('name','id', 'email', 'phone', 'pub')
    ordering =['-pub']

admin.site.register(Dreams, DreamsAdmin)
admin.site.register(Reply, ReplyAdmin)
admin.site.register(Contact, ContactAdmin)
