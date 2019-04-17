from django.urls import path

from . import views

urlpatterns = [
    path('workflows', views.workflows, name='workflows'),
    path('workflows/<uuid:uuid>', views.workflow_detail, name='workflow_detail'),
    path('workflows/<uuid:uuid>/reset', views.workflow_reset, name='workflow_reset'),
    path('workflows/<uuid:uuid>/delete', views.workflow_delete, name='workflow_delete'),
]
