from django.urls import path

from . import views

urlpatterns = [
    path('workflows/', views.workflows, name='workflows'),
]
