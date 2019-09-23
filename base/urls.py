"""base URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('oidc/', include('mozilla_django_oidc.urls')),
    path('users/', include('django.contrib.auth.urls')),
    path('whoami', views.whoami, name='whoami'),
    path('', include('users.urls')),
    path('', include('comanage.urls')),
    path('', include('projects.urls')),
    path('', include('debug.urls')),
    path('', include('datasets.urls')),
    path('', include('workflows.urls')),
    path('', include('apache_kafka.urls')),
    path('', include('infrastructure.urls')),
]

# Configure custom error pages
handler400 = 'base.views.handler400'
handler404 = 'base.views.handler404'
handler500 = 'base.views.handler500'
