"""
URL configuration for car_rental_system project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.conf import settings
from django.conf.urls.static import static
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from views import dashboard, home_redirect, page_not_found, server_error, permission_denied
from views import review_list_view, review_edit_view, review_delete_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard, name='dashboard'),
    path('home/', home_redirect, name='home'),
    path('reviews/', review_list_view, name='review_list'),
    path('reviews/<int:pk>/edit/', review_edit_view, name='review_edit'),
    path('reviews/<int:pk>/delete/', review_delete_view, name='review_delete'),
    path('accounts/', include('accounts.urls')),
    path('vehicles/', include('vehicles.urls')),
    path('customers/', include('customers.urls')),
    path('rentals/', include('rentals.urls')),
]

# 开发环境下提供静态文件服务
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0] if settings.STATICFILES_DIRS else None)
