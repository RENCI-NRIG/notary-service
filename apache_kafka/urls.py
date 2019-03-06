from django.urls import path

from . import views

urlpatterns = [
    path('messages/', views.messages, name='messages'),
    # path('messages/new', views.message_new, name='message_new'),
    path('messages/<uuid:uuid>/', views.message_detail, name='message_detail'),
    # path('messages/<uuid:uuid>/edit', views.message_edit, name='message_edit'),
    # path('messages/<uuid:uuid>/delete', views.message_delete, name='message_delete'),
]