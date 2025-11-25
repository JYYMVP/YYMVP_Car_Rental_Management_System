"""
URL configuration for customers app.
"""
from django.urls import path
from . import views

app_name = 'customers'

urlpatterns = [
    # 客户管理相关URLs
    path('', views.index, name='index'),
    path('list/', views.customer_list, name='customer_list'),
    path('create/', views.customer_create, name='customer_create'),
    path('<int:pk>/', views.customer_detail, name='customer_detail'),
    path('<int:pk>/edit/', views.customer_update, name='customer_update'),
    path('<int:pk>/delete/', views.customer_delete, name='customer_delete'),
    path('<int:pk>/membership/', views.customer_membership_update, name='customer_membership_update'),
    path('api/statistics/', views.get_customer_statistics, name='get_customer_statistics'),
]