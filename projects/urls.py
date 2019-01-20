from django.urls import path
from . import views

urlpatterns = [
    path('projects/', views.projects, name='projects'),
    path('projects/new', views.project_new, name='project_new'),
    path('projects/<uuid:uuid>/', views.project_detail, name='project_detail'),
    path('projects/<uuid:uuid>/edit', views.project_edit, name='project_edit'),
    path('projects/<uuid:uuid>/delete', views.project_delete, name='project_delete'),
]
