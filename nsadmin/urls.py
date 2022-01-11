from django.urls import path

from .views import nsadmin, nsadminmessage_detail

urlpatterns = [
    path('nsadmin', nsadmin, name='nsadmin'),
    path('nsadmin/messages/<uuid:uuid>', nsadminmessage_detail, name='nsadminmessage_detail'),
]
