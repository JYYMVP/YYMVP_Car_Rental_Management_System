from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # 用户认证
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('password-reset/', views.password_reset_request_view, name='password_reset_request'),
    path('password-reset/confirm/', views.password_reset_view, name='password_reset'),
    
    # 个人中心
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('password-change/', views.password_change_view, name='password_change'),
    path('customer-info/', views.customer_info_view, name='customer_info'),
    
    # 车辆浏览
    path('home/', views.home_view, name='home'),
    path('vehicle/<int:pk>/', views.vehicle_detail_view, name='vehicle_detail'),
    path('vehicle/<int:pk>/favorite/', views.favorite_toggle_view, name='favorite_toggle'),
    path('favorites/', views.favorites_view, name='favorites'),
    path('vehicle-compare/', views.vehicle_compare_view, name='vehicle_compare'),
    path('vehicle-compare/result/', views.vehicle_compare_result_view, name='vehicle_compare_result'),
    
    # 订单管理
    path('orders/', views.my_orders_view, name='my_orders'),
    path('order/<int:pk>/', views.order_detail_view, name='order_detail'),
    path('order/create/', views.order_create_view, name='order_create'),
    path('order/<int:pk>/cancel/', views.order_cancel_view, name='order_cancel'),
    path('order/<int:pk>/review/', views.order_review_view, name='order_review'),
    path('order/<int:pk>/return/', views.order_return_view, name='order_return'),
    
    # 支付
    path('payment/<int:pk>/', views.payment_view, name='payment'),
    path('payment/history/', views.payment_history_view, name='payment_history'),
    path('consumption/', views.consumption_report_view, name='consumption_report'),
    
    # 消息通知
    path('notifications/', views.notifications_view, name='notifications'),
    path('notification/<int:pk>/read/', views.notification_mark_read_view, name='notification_mark_read'),
    path('notifications/mark-all-read/', views.notification_mark_all_read_view, name='notification_mark_all_read'),
    
    # 帮助中心
    path('help/', views.help_center_view, name='help_center'),
    path('contact/', views.contact_view, name='contact'),
]
