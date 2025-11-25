"""
URL configuration for rentals app.
"""
from django.urls import path
from . import views

app_name = 'rentals'

urlpatterns = [
    # 租赁管理相关URLs
    path('', views.index, name='index'),
    path('list/', views.rental_list, name='rental_list'),
    path('create/', views.rental_create, name='rental_create'),
    path('<int:pk>/', views.rental_detail, name='rental_detail'),
    path('<int:pk>/edit/', views.rental_update, name='rental_update'),
    path('<int:pk>/status/', views.rental_status_update, name='rental_status_update'),
    path('<int:pk>/return/', views.rental_return, name='rental_return'),
    path('<int:pk>/cancel/', views.rental_cancel, name='rental_cancel'),
    
    # AJAX接口
    path('vehicle-dates/', views.get_vehicle_available_dates, name='vehicle_available_dates'),
]