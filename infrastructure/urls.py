from django.urls import path

from . import views

urlpatterns = [
    path('infrastructure', views.infrastructure, name='infrastructure'),
    path('infrastructure/new', views.infrastructure_new, name='infrastructure_new'),
    path('infrastructure/<uuid:uuid>', views.infrastructure_detail, name='infrastructure_detail'),
    path('infrastructure/<uuid:uuid>/edit', views.infrastructure_edit, name='infrastructure_edit'),
    path('infrastructure/<uuid:uuid>/delete', views.infrastructure_delete, name='infrastructure_delete'),
]
