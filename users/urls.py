from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('about', views.about, name='about'),
    path('contact', views.contact, name='contact'),
    path('search', views.search, name='search'),
    path('profile', views.profile, name='profile'),
    path('login', views.login, name='login'),
    path('faq', views.faq, name='faq'),
    path('profile/certificate', views.certificate, name='certificate'),
]
