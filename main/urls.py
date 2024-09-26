from django.urls import path, re_path
from django.views.static import serve
from django.conf import settings
from . import views

app_name = "main"

urlpatterns = [
    path("", views.index, name="index"),
    path('dreams/', views.dreams, name='dreams'),
    path('consult/', views.consult, name='consult'),
    path('contact/', views.contact, name='contact'),
    path('app/', views.app, name='app'),
    path("about/", views.about, name="about"),
    path("error/", views.error, name="error"),
    path('dreams/<uuid:dream_id>/', views.dreams, name='specific_dream'),
    re_path(r'^static/(?P<path>.*)$', serve,{'document_root': settings.STATIC_ROOT}),
]

    #path('login/', views.login_view, name='login'),
    #path('register/', views.register_view, name='register'),
    #path('logout/', views.logout_view, name='logout'),