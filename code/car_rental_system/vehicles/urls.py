"""
URL configuration for vehicles app.
"""
from django.urls import path
from . import views

app_name = 'vehicles'

urlpatterns = [
    # 车辆管理相关URLs
    path('', views.index, name='index'),
    path('vehicles/', views.vehicle_list, name='vehicle_list'),
    path('vehicles/create/', views.vehicle_create, name='vehicle_create'),
    path('vehicles/<int:pk>/', views.vehicle_detail, name='vehicle_detail'),
    path('vehicles/<int:pk>/edit/', views.vehicle_update, name='vehicle_update'),
    path('vehicles/<int:pk>/delete/', views.vehicle_delete, name='vehicle_delete'),
    path('vehicles/<int:pk>/status/', views.vehicle_status_update, name='vehicle_status_update'),
]