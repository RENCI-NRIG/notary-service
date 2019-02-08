from django.urls import path
from . import views

urlpatterns = [
    path('datasets/', views.datasets, name='datasets'),
    path('datasets/new', views.dataset_new, name='dataset_new'),
    path('datasets/<uuid:uuid>/', views.dataset_detail, name='dataset_detail'),
    path('datasets/<uuid:uuid>/edit', views.dataset_edit, name='dataset_edit'),
    path('datasets/<uuid:uuid>/delete', views.dataset_delete, name='dataset_delete'),
    path('templates/', views.templates, name='templates'),
    path('templates/new', views.template_new, name='template_new'),
    path('templates/<uuid:uuid>/', views.template_detail, name='template_detail'),
    path('templates/<uuid:uuid>/edit', views.template_edit, name='template_edit'),
    path('templates/<uuid:uuid>/delete', views.template_delete, name='template_delete'),
]