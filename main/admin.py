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

class DreamCommentAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'dream', 'pub')
    list_filter = ('pub',)
    search_fields = ('name', 'body', 'user__username', 'user__email')
    ordering = ['-pub']

class ContactAdmin(admin.ModelAdmin):
    list_display = ('name','id', 'email', 'phone', 'pub')
    ordering =['-pub']


class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'user_email', 'birth_year', 'birth_year_updates_count',
        'mbti_type', 'mbti_updates_count', 'country_name', 'country_locked',
    )
    readonly_fields = ('user_email',)
    fields = (
        'user',
        'user_email',
        'birth_year',
        'birth_year_updates_count',
        'mbti_type',
        'mbti_updates_count',
        'country_code',
        'country_name',
        'country_locked',
    )
    search_fields = ('user__username', 'user__email', 'user__first_name')
    list_filter = ('country_locked',)

    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj is not None:
            readonly.insert(0, 'user')
        return readonly

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

    @admin.display(description='Email', ordering='user__email')
    def user_email(self, obj):
        if not obj or not obj.user_id:
            return '—'
        return obj.user.email or '—'


class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'dream', 'read', 'created_at')
    list_filter = ('read', 'created_at')
    search_fields = ('recipient__username', 'recipient__email', 'dream__title')
    ordering = ['-created_at']


admin.site.register(Dreams, DreamsAdmin)
admin.site.register(DreamSymbol, DreamSymbolAdmin)
admin.site.register(DreamComment, DreamCommentAdmin)
admin.site.register(Contact, ContactAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Notification, NotificationAdmin)
