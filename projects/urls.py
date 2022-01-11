from django.urls import path

from .views import projects, project_new, project_detail, project_edit, project_delete, project_update_staff, \
    project_update_pi, project_update_admin, project_update_infra, project_update_dataset

urlpatterns = [
    path('projects', projects, name='projects'),
    path('projects/new', project_new, name='project_new'),
    path('projects/<uuid:uuid>', project_detail, name='project_detail'),
    path('projects/<uuid:uuid>/edit', project_edit, name='project_edit'),
    path('projects/<uuid:uuid>/delete', project_delete, name='project_delete'),
    path('projects/<uuid:uuid>/update_staff', project_update_staff, name='project_update_staff'),
    path('projects/<uuid:uuid>/update_pi', project_update_pi, name='project_update_pi'),
    path('projects/<uuid:uuid>/update_admin', project_update_admin, name='project_update_admin'),
    path('projects/<uuid:uuid>/update_infrastructure', project_update_infra, name='project_update_infra'),
    path('projects/<uuid:uuid>/update_dataset', project_update_dataset, name='project_update_dataset'),
]
