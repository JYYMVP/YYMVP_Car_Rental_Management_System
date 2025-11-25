from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Count, Sum, Avg
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django.utils import timezone
from django import forms
from django.core.cache import cache
from datetime import date, datetime, timedelta
from decimal import Decimal
from .forms import (
    UserRegisterForm, UserLoginForm, PasswordResetRequestForm,
    PasswordResetForm, UserProfileForm, PasswordChangeFormCustom,
    ReviewForm, PaymentForm, VehicleCompareForm
)
from .models import UserProfile, Favorite, Review, Payment, Notification
from vehicles.models import Vehicle
from rentals.models import Rental
from customers.models import Customer


# ========== 用户认证相关视图 ==========

def register_view(request):
    """用户注册视图"""
    if request.user.is_authenticated:
        return redirect('accounts:profile')
    
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # 创建用户资料
            UserProfile.objects.get_or_create(user=user)
            messages.success(request, f'注册成功！欢迎 {user.username}，请登录。')
            return redirect('accounts:login')
    else:
        form = UserRegisterForm()
    
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """用户登录视图 - 支持管理员和普通用户"""
    login_type = request.GET.get('type', 'user')
    if request.user.is_authenticated:
        # 如果已登录，根据身份跳转
        if request.user.is_staff:
            return redirect('dashboard')
        return redirect('accounts:home')
    
    if request.method == 'POST':
        login_type = request.POST.get('login_type', 'user')
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()

            # 如果选择管理员登录但账号不是管理员，拒绝
            if login_type == 'admin' and not user.is_staff:
                form.add_error(None, '该账号没有管理员权限，请切换到用户登录。')
            else:
                login(request, user)
                
                # 处理"记住我"功能
                if not form.cleaned_data.get('remember_me'):
                    # 如果不记住，关闭浏览器后会话结束
                    request.session.set_expiry(0)
                
                if user.is_staff:
                    messages.success(request, f'欢迎回来，管理员 {user.username}！')
                else:
                    messages.success(request, f'欢迎回来，{user.username}！')
                
                # 检查是否有next参数
                next_url = request.GET.get('next', '')
                if next_url:
                    return redirect(next_url)
                
                # 根据身份跳转
                if user.is_staff:
                    return redirect('dashboard')
                return redirect('accounts:home')
    else:
        form = UserLoginForm()
    
    return render(request, 'accounts/login.html', {'form': form, 'login_type': login_type})


@login_required
def logout_view(request):
    """用户登出视图"""
    username = request.user.username
    logout(request)
    messages.success(request, f'再见，{username}！您已成功退出。')
    return redirect('accounts:login')


@require_http_methods(["GET", "POST"])
def password_reset_request_view(request):
    """密码重置请求视图"""
    if request.user.is_authenticated:
        return redirect('accounts:profile')
    
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            # 这里简化处理，实际应该发送邮件
            email = form.cleaned_data.get('email')
            messages.info(request, f'密码重置链接已发送至 {email}（演示功能，实际需要配置邮件服务器）')
            return redirect('accounts:login')
    else:
        form = PasswordResetRequestForm()
    
    return render(request, 'accounts/password_reset_request.html', {'form': form})


@require_http_methods(["GET", "POST"])
def password_reset_view(request):
    """密码重置视图"""
    if request.user.is_authenticated:
        return redirect('accounts:profile')
    
    # 这里简化处理，实际应该验证token
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            # 实际应该根据token找到用户
            messages.success(request, '密码重置成功，请登录。')
            return redirect('accounts:login')
    else:
        form = PasswordResetForm()
    
    return render(request, 'accounts/password_reset.html', {'form': form})


# ========== 个人中心相关视图 ==========

@login_required
def profile_view(request):
    """用户个人中心视图"""
    user = request.user
    
    # 获取用户的客户信息
    customer = get_customer_for_user(user)
    
    # 获取用户的订单
    user_rentals = []
    if customer:
        user_rentals = Rental.objects.filter(customer=customer).select_related(
            'vehicle'
        ).order_by('-created_at')[:10]
    
    # 获取统计信息
    rental_stats = {
        'total': 0,
        'total_amount': Decimal('0.00'),
    }
    if customer:
        rental_stats = Rental.objects.filter(customer=customer).aggregate(
            total=Count('id'),
            total_amount=Sum('total_amount')
        )
    
    # 获取未读通知数
    unread_notifications = Notification.objects.filter(
        user=user, is_read=False
    ).count()
    
    context = {
        'user': user,
        'customer': customer,
        'rentals': user_rentals,
        'rental_stats': rental_stats,
        'unread_notifications': unread_notifications,
    }
    
    return render(request, 'accounts/profile.html', context)


def get_customer_for_user(user):
    """统一的获取用户客户信息的函数"""
    customer = None
    try:
        # 首先查找已关联用户的客户记录
        customer = Customer.objects.filter(user=user).first()
        
        # 如果没有找到，尝试通过邮箱或手机号查找
        if not customer:
            if user.email:
                customer = Customer.objects.filter(email=user.email).first()
            if not customer and hasattr(user, 'username'):
                try:
                    customer = Customer.objects.filter(phone=user.username).first()
                except:
                    pass
        
        # 如果找到了客户信息但没有关联用户，自动关联
        if customer and not customer.user:
            customer.user = user
            customer.save(update_fields=['user'])
    except Exception as e:
        print(f"查找客户信息时出错: {e}")
    
    return customer


def get_order_amount_breakdown(rental):
    """计算订单的费用构成（基础租金、押金、异地还车费、总额）"""
    base_amount = rental.total_amount or Decimal('0.00')
    deposit_amount = rental.deposit or Decimal('0.00')
    cross_location_fee = rental.cross_location_fee or Decimal('0.00')
    
    if not rental.is_cross_location_return:
        cross_location_fee = Decimal('0.00')
    
    order_total_amount = base_amount + deposit_amount + cross_location_fee
    return {
        'base_amount': base_amount,
        'deposit_amount': deposit_amount,
        'cross_location_fee': cross_location_fee,
        'order_total_amount': order_total_amount,
    }


def get_payment_summary(rental, payments=None):
    """计算支付/退款及剩余金额汇总"""
    if payments is None:
        payments = Payment.objects.filter(rental=rental)
    paid_amount = payments.filter(
        transaction_type='CHARGE',
        status='PAID'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    refunded_amount = payments.filter(
        transaction_type='REFUND',
        status='REFUNDED'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    amount_breakdown = get_order_amount_breakdown(rental)
    order_total_amount = amount_breakdown['order_total_amount']
    remaining_amount = order_total_amount - paid_amount
    if remaining_amount < Decimal('0.00'):
        remaining_amount = Decimal('0.00')
    net_paid = paid_amount - refunded_amount
    return {
        'paid_amount': paid_amount,
        'refunded_amount': refunded_amount,
        'net_paid': net_paid,
        'remaining_amount': remaining_amount,
        'order_total_amount': order_total_amount,
        **amount_breakdown
    }


def get_recommended_vehicles(user, limit=6):
    """
    获取推荐车辆
    推荐策略：
    1. 基于用户历史订单推荐相似车型（相同品牌、类型、座位数等）
    2. 基于热门车型推荐（租赁次数最多的车型）
    3. 综合推荐结果
    """
    recommended_vehicles = []
    
    # 只推荐可用车辆
    available_vehicles = Vehicle.objects.filter(status='AVAILABLE')
    
    # 策略1：基于用户历史订单的个性化推荐
    customer = get_customer_for_user(user)
    if customer:
        # 获取用户的历史订单
        user_rentals = Rental.objects.filter(
            customer=customer,
            status__in=['COMPLETED', 'ONGOING']
        ).select_related('vehicle').order_by('-created_at')[:10]
        
        if user_rentals.exists():
            # 分析用户偏好：品牌、类型、座位数
            preferred_brands = []
            preferred_types = []
            preferred_seats = []
            
            for rental in user_rentals:
                vehicle = rental.vehicle
                if vehicle.brand:
                    preferred_brands.append(vehicle.brand)
                if vehicle.vehicle_type:
                    preferred_types.append(vehicle.vehicle_type)
                if vehicle.seats:
                    preferred_seats.append(vehicle.seats)
            
            # 根据偏好推荐相似车辆
            if preferred_brands or preferred_types or preferred_seats:
                # 构建推荐查询
                recommendation_query = Q()
                
                # 优先匹配品牌
                if preferred_brands:
                    # 获取最常见的品牌
                    from collections import Counter
                    brand_counter = Counter(preferred_brands)
                    top_brands = [brand for brand, _ in brand_counter.most_common(2)]
                    recommendation_query |= Q(brand__in=top_brands)
                
                # 匹配类型
                if preferred_types:
                    type_counter = Counter(preferred_types)
                    top_types = [vtype for vtype, _ in type_counter.most_common(2)]
                    recommendation_query |= Q(vehicle_type__in=top_types)
                
                # 匹配座位数（允许±1的误差）
                if preferred_seats:
                    seats_counter = Counter(preferred_seats)
                    top_seats = [seats for seats, _ in seats_counter.most_common(2)]
                    seats_query = Q()
                    for seat in top_seats:
                        seats_query |= Q(seats__gte=seat-1, seats__lte=seat+1)
                    recommendation_query |= seats_query
                
                # 获取推荐车辆（排除用户已租过的车辆）
                rented_vehicle_ids = user_rentals.values_list('vehicle_id', flat=True)
                personalized_vehicles = available_vehicles.filter(
                    recommendation_query
                ).exclude(id__in=rented_vehicle_ids).distinct()[:limit]
                
                recommended_vehicles.extend(list(personalized_vehicles))
    
    # 策略2：基于热门车型推荐（如果个性化推荐不足）
    if len(recommended_vehicles) < limit:
        # 获取租赁次数最多的车辆（热门车型）
        cache_key = 'popular_vehicles'
        popular_vehicle_ids = cache.get(cache_key)
        
        if popular_vehicle_ids is None:
            # 统计每个车辆的租赁次数
            popular_vehicles = Rental.objects.filter(
                status__in=['COMPLETED', 'ONGOING']
            ).values('vehicle_id').annotate(
                rental_count=Count('id')
            ).order_by('-rental_count')[:limit*2]
            
            popular_vehicle_ids = [item['vehicle_id'] for item in popular_vehicles]
            cache.set(cache_key, popular_vehicle_ids, 3600)  # 缓存1小时
        
        # 获取热门车辆
        if popular_vehicle_ids:
            popular_vehicles = available_vehicles.filter(
                id__in=popular_vehicle_ids
            ).exclude(id__in=[v.id for v in recommended_vehicles])[:limit - len(recommended_vehicles)]
            
            recommended_vehicles.extend(list(popular_vehicles))
    
    # 策略3：如果还是不足，推荐最新添加的车辆
    if len(recommended_vehicles) < limit:
        new_vehicles = available_vehicles.exclude(
            id__in=[v.id for v in recommended_vehicles]
        ).order_by('-created_at')[:limit - len(recommended_vehicles)]
        
        recommended_vehicles.extend(list(new_vehicles))
    
    # 去重并限制数量
    seen_ids = set()
    unique_vehicles = []
    for vehicle in recommended_vehicles:
        if vehicle.id not in seen_ids:
            seen_ids.add(vehicle.id)
            unique_vehicles.append(vehicle)
        if len(unique_vehicles) >= limit:
            break
    
    return unique_vehicles[:limit]


@login_required
@require_http_methods(["GET", "POST"])
def customer_info_view(request):
    """用户填写/编辑客户信息视图"""
    user = request.user
    
    # 获取或创建客户信息
    customer = get_customer_for_user(user)
    
    if request.method == 'POST':
        from customers.forms import CustomerForm
        form = CustomerForm(request.POST, instance=customer)
        
        # 隐藏会员等级字段，用户不能直接修改
        if 'member_level' in form.fields:
            form.fields['member_level'].widget = forms.HiddenInput()
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    customer = form.save(commit=False)
                    # 确保关联到当前用户
                    customer.user = user
                    # 如果用户有邮箱，自动填充
                    if not customer.email and user.email:
                        customer.email = user.email
                    # 新客户默认为普通会员
                    if not customer.member_level:
                        customer.member_level = 'NORMAL'
                    customer.save()
                    
                    # 刷新对象以确保获取最新数据
                    customer.refresh_from_db()
                    
                    # 验证保存是否成功
                    saved_customer = Customer.objects.filter(user=user).first()
                    if saved_customer and saved_customer.user == user:
                        messages.success(request, '客户信息保存成功！现在可以开始租车了。')
                        return redirect('accounts:profile')
                    else:
                        # 如果保存失败，显示详细信息
                        debug_info = f"用户ID: {user.id}, 客户ID: {customer.id if customer else 'None'}, 客户用户: {customer.user.id if customer and customer.user else 'None'}"
                        messages.error(request, f'客户信息保存失败。调试信息: {debug_info}')
            except Exception as e:
                import traceback
                error_detail = traceback.format_exc()
                print(f"保存客户信息错误详情: {error_detail}")
                messages.error(request, f'保存客户信息时出错：{str(e)}')
    else:
        from customers.forms import CustomerForm
        form = CustomerForm(instance=customer)
        
        # 隐藏会员等级字段，用户不能直接修改
        if 'member_level' in form.fields:
            form.fields['member_level'].widget = forms.HiddenInput()
            form.fields['member_level'].initial = 'NORMAL'
        
        # 如果用户有邮箱，预填充
        if not customer and user.email:
            form.fields['email'].initial = user.email
    
    # 添加调试信息
    debug_info = {
        'user_id': user.id,
        'user_email': user.email,
        'user_username': user.username,
        'customer_exists': customer is not None,
        'customer_id': customer.id if customer else None,
        'customer_user': customer.user.id if customer and customer.user else None,
        'customer_email': customer.email if customer else None,
        'customer_phone': customer.phone if customer else None,
    }
    
    context = {
        'form': form,
        'customer': customer,
        'title': '完善客户信息' if not customer else '编辑客户信息',
        'debug_info': debug_info,  # 调试信息
    }
    
    return render(request, 'accounts/customer_info.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def profile_edit_view(request):
    """编辑个人资料视图"""
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile, user=user)
        if form.is_valid():
            form.save()
            messages.success(request, '个人资料更新成功！')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=profile, user=user)
    
    context = {
        'form': form,
        'user': user,
        'profile': profile,
    }
    
    return render(request, 'accounts/profile_edit.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def password_change_view(request):
    """修改密码视图"""
    if request.method == 'POST':
        form = PasswordChangeFormCustom(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, '密码修改成功！')
            return redirect('accounts:profile')
    else:
        form = PasswordChangeFormCustom(request.user)
    
    context = {
        'form': form,
    }
    
    return render(request, 'accounts/password_change.html', context)


# ========== 车辆浏览相关视图 ==========

def home_view(request):
    """用户首页视图 - 浏览可租车辆"""
    # 只显示可用的车辆
    vehicles = Vehicle.objects.filter(status='AVAILABLE').only(
        'id', 'license_plate', 'brand', 'model', 'vehicle_type',
        'color', 'seats', 'daily_rate', 'created_at'
    )
    
    # 搜索功能
    search_query = request.GET.get('q', '')
    if search_query:
        vehicles = vehicles.filter(
            Q(license_plate__icontains=search_query) |
            Q(brand__icontains=search_query) |
            Q(model__icontains=search_query) |
            Q(vehicle_type__icontains=search_query)
        )
    
    # 筛选功能
    brand_filter = request.GET.get('brand', '')
    type_filter = request.GET.get('type', '')
    seats_filter = request.GET.get('seats', '')
    price_min = request.GET.get('price_min', '')
    price_max = request.GET.get('price_max', '')
    
    if brand_filter:
        vehicles = vehicles.filter(brand=brand_filter)
    
    if type_filter:
        vehicles = vehicles.filter(vehicle_type=type_filter)
    
    # 座位数筛选（只有在字段存在时才执行）
    if seats_filter:
        try:
            seats = int(seats_filter)
            # 尝试使用seats字段筛选，如果字段不存在会抛出异常
            vehicles = vehicles.filter(seats=seats)
        except (ValueError, Exception):
            # 如果转换失败或字段不存在，忽略筛选
            pass
    
    if price_min:
        try:
            vehicles = vehicles.filter(daily_rate__gte=Decimal(price_min))
        except:
            pass
    
    if price_max:
        try:
            vehicles = vehicles.filter(daily_rate__lte=Decimal(price_max))
        except:
            pass
    
    # 获取筛选选项（使用缓存）
    from django.core.cache import cache
    cache_key_brands = 'user_vehicle_brands_list'
    cache_key_types = 'user_vehicle_types_list'
    
    brands = cache.get(cache_key_brands)
    if brands is None:
        brands = list(Vehicle.objects.values_list('brand', flat=True).distinct().order_by('brand'))
        cache.set(cache_key_brands, brands, 300)
    
    types = cache.get(cache_key_types)
    if types is None:
        types = list(Vehicle.objects.values_list('vehicle_type', flat=True).distinct().order_by('vehicle_type'))
        cache.set(cache_key_types, types, 300)
    
    # 获取座位数选项（使用缓存）
    cache_key_seats = 'user_vehicle_seats_list'
    seats_options = cache.get(cache_key_seats)
    if seats_options is None:
        try:
            # 检查字段是否存在（如果迁移未应用，会抛出异常）
            seats_values = list(Vehicle.objects.filter(status='AVAILABLE').values_list('seats', flat=True))
            seats_options = sorted({seat for seat in seats_values if seat})
            cache.set(cache_key_seats, seats_options, 300)
        except Exception:
            # 如果字段不存在（迁移未应用），使用空列表
            seats_options = []
            cache.set(cache_key_seats, seats_options, 300)
    
    # 商务风格统计信息
    vehicle_stats_raw = Vehicle.objects.filter(status='AVAILABLE').aggregate(
        total=Count('id'),
        avg_rate=Avg('daily_rate')
    )
    vehicle_stats = {
        'total': vehicle_stats_raw['total'] or 0,
        'avg_rate': (vehicle_stats_raw['avg_rate'] or Decimal('0.00')),
        'seat_options': len(seats_options)
    }
    popular_types = list(
        Vehicle.objects.filter(status='AVAILABLE')
        .values_list('vehicle_type', flat=True)
        .distinct()
        .order_by('vehicle_type')[:6]
    )
    
    # 检查用户收藏的车辆ID
    favorite_vehicle_ids = []
    if request.user.is_authenticated:
        favorite_vehicle_ids = list(
            Favorite.objects.filter(user=request.user).values_list('vehicle_id', flat=True)
        )
    
    # 分页
    paginator = Paginator(vehicles.order_by('-created_at'), 12)
    page_number = request.GET.get('page', 1)
    vehicles_page = paginator.get_page(page_number)
    
    # 获取推荐车辆（仅对已登录用户显示）
    recommended_vehicles = []
    if request.user.is_authenticated:
        recommended_vehicles = get_recommended_vehicles(request.user, limit=6)
    
    context = {
        'vehicles': vehicles_page,
        'brands': brands,
        'types': types,
        'seats_options': seats_options,
        'search_query': search_query,
        'brand_filter': brand_filter,
        'type_filter': type_filter,
        'seats_filter': seats_filter,
        'price_min': price_min,
        'price_max': price_max,
        'favorite_vehicle_ids': favorite_vehicle_ids,
        'recommended_vehicles': recommended_vehicles,
        'vehicle_stats': vehicle_stats,
        'popular_types': popular_types,
    }
    
    return render(request, 'accounts/home.html', context)


def vehicle_detail_view(request, pk):
    """用户查看车辆详情"""
    vehicle = get_object_or_404(Vehicle, pk=pk)
    
    # 检查是否已收藏
    is_favorited = False
    if request.user.is_authenticated:
        is_favorited = Favorite.objects.filter(user=request.user, vehicle=vehicle).exists()
    
    # 获取车辆评价统计
    review_stats = Review.objects.filter(vehicle=vehicle).aggregate(
        total=Count('id'),
        average_rating=Avg('rating')
    )
    
    # 获取最近评价
    recent_reviews = Review.objects.filter(vehicle=vehicle).select_related(
        'user'
    ).order_by('-created_at')[:5]
    
    # 检查用户是否可以租车
    can_rent = False
    customer = None
    if request.user.is_authenticated:
        customer = get_customer_for_user(request.user)
        if customer:
            can_rent = True
    
    context = {
        'vehicle': vehicle,
        'can_rent': can_rent,
        'customer': customer,
        'is_favorited': is_favorited,
        'review_stats': review_stats,
        'recent_reviews': recent_reviews,
    }
    
    return render(request, 'accounts/vehicle_detail.html', context)


@login_required
@require_http_methods(["POST"])
def favorite_toggle_view(request, pk):
    """收藏/取消收藏车辆"""
    vehicle = get_object_or_404(Vehicle, pk=pk)
    
    favorite, created = Favorite.objects.get_or_create(
        user=request.user,
        vehicle=vehicle
    )
    
    if created:
        messages.success(request, f'已收藏 {vehicle.brand} {vehicle.model}')
        action = 'added'
    else:
        favorite.delete()
        messages.info(request, f'已取消收藏 {vehicle.brand} {vehicle.model}')
        action = 'removed'
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'action': action})
    
    return redirect('accounts:vehicle_detail', pk=pk)


@login_required
def favorites_view(request):
    """我的收藏视图"""
    favorites = Favorite.objects.filter(user=request.user).select_related(
        'vehicle'
    ).order_by('-created_at')
    
    # 分页
    paginator = Paginator(favorites, 12)
    page_number = request.GET.get('page', 1)
    favorites_page = paginator.get_page(page_number)
    
    context = {
        'favorites': favorites_page,
    }
    
    return render(request, 'accounts/favorites.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def vehicle_compare_view(request):
    """车辆对比视图"""
    if request.method == 'POST':
        form = VehicleCompareForm(request.POST)
        if form.is_valid():
            vehicles = form.cleaned_data.get('vehicles')
            # 将车辆ID存储到session中用于对比
            request.session['compare_vehicles'] = [v.id for v in vehicles]
            return redirect('accounts:vehicle_compare_result')
    else:
        # 从session获取要对比的车辆
        vehicle_ids = request.session.get('compare_vehicles', [])
        form = VehicleCompareForm(initial={'vehicles': vehicle_ids})
    
    # 获取可租车辆
    available_vehicles = Vehicle.objects.filter(status='AVAILABLE').order_by('brand', 'model')
    form.fields['vehicles'].queryset = available_vehicles
    
    context = {
        'form': form,
    }
    
    return render(request, 'accounts/vehicle_compare.html', context)


@login_required
def vehicle_compare_result_view(request):
    """车辆对比结果视图"""
    vehicle_ids = request.session.get('compare_vehicles', [])
    
    if not vehicle_ids or len(vehicle_ids) < 2:
        messages.warning(request, '请至少选择2辆车进行对比。')
        return redirect('accounts:vehicle_compare')
    
    vehicles = Vehicle.objects.filter(id__in=vehicle_ids).order_by('brand', 'model')
    
    if vehicles.count() < 2:
        messages.warning(request, '请至少选择2辆车进行对比。')
        return redirect('accounts:vehicle_compare')
    
    context = {
        'vehicles': vehicles,
    }
    
    return render(request, 'accounts/vehicle_compare_result.html', context)


# ========== 订单管理相关视图 ==========

@login_required
def my_orders_view(request):
    """我的订单视图"""
    # 获取用户的客户信息
    customer = get_customer_for_user(request.user)
    
    if not customer:
        messages.info(request, '您还没有客户信息，请先完善客户信息才能租车。')
        return redirect('accounts:customer_info')
    
    # 获取订单
    rentals = Rental.objects.filter(customer=customer).select_related(
        'vehicle'
    ).order_by('-created_at')
    
    # 筛选
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('q', '')
    
    if status_filter:
        rentals = rentals.filter(status=status_filter)
    
    if search_query:
        rentals = rentals.filter(
            Q(vehicle__license_plate__icontains=search_query) |
            Q(vehicle__brand__icontains=search_query) |
            Q(vehicle__model__icontains=search_query)
        )
    
    # 分页
    paginator = Paginator(rentals, 15)
    page_number = request.GET.get('page', 1)
    rentals_page = paginator.get_page(page_number)
    
    context = {
        'rentals': rentals_page,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    
    return render(request, 'accounts/my_orders.html', context)


@login_required
def order_detail_view(request, pk):
    """订单详情视图"""
    rental = get_object_or_404(Rental, pk=pk)
    
    # 验证订单属于当前用户
    customer = get_customer_for_user(request.user)
    
    if rental.customer != customer:
        messages.error(request, '您没有权限查看此订单。')
        return redirect('accounts:my_orders')
    
    # 获取订单的评价
    review = None
    try:
        review = Review.objects.get(rental=rental)
    except Review.DoesNotExist:
        pass
    
    # 获取支付记录
    payments = Payment.objects.filter(rental=rental).order_by('-created_at')
    payment_summary = get_payment_summary(rental, payments)
    can_pay = rental.status in ['PENDING', 'ONGOING'] and payment_summary['remaining_amount'] > Decimal('0.00')
    
    context = {
        'rental': rental,
        'review': review,
        'payments': payments,
        'can_review': rental.status == 'COMPLETED' and not review,
        'can_cancel': rental.status in ['PENDING'],
        'amount_paid': payment_summary['paid_amount'],
        'refunded_amount': payment_summary['refunded_amount'],
        'net_paid': payment_summary['net_paid'],
        'remaining_amount': payment_summary['remaining_amount'],
        'can_pay': can_pay,
        'base_amount': payment_summary['base_amount'],
        'deposit_amount': payment_summary['deposit_amount'],
        'cross_location_fee': payment_summary['cross_location_fee'],
        'order_total_amount': payment_summary['order_total_amount'],
        'has_cross_location_fee': payment_summary['cross_location_fee'] > Decimal('0.00'),
    }
    
    return render(request, 'accounts/order_detail.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def order_create_view(request):
    """创建订单视图"""
    # 检查是否有客户信息
    customer = get_customer_for_user(request.user)
    
    if not customer:
        # 显示详细的调试信息
        debug_msg = f"用户ID: {request.user.id}, 邮箱: {request.user.email or '无'}, 用户名: {request.user.username}"
        messages.warning(request, f'请先完善客户信息才能租车。{debug_msg}')
        return redirect('accounts:customer_info')
    
    # 从URL参数获取车辆ID
    vehicle_id = request.GET.get('vehicle')
    
    if request.method == 'POST':
        from rentals.forms import RentalForm
        form = RentalForm(request.POST)
        
        # 设置客户字段（只显示当前用户的客户信息）
        form.fields['customer'].queryset = Customer.objects.filter(pk=customer.pk)
        form.fields['customer'].initial = customer
        
        # 设置状态字段（默认为PENDING）
        form.fields['status'].initial = 'PENDING'
        
        # 只显示可用车辆
        form.fields['vehicle'].queryset = Vehicle.objects.filter(status='AVAILABLE').order_by('license_plate')
        
        if form.is_valid():
            with transaction.atomic():
                rental = form.save(commit=False)
                
                # 计算总费用
                from rentals.views import calculate_rental_amount
                total_amount = calculate_rental_amount(
                    rental.customer,
                    rental.vehicle,
                    rental.start_date,
                    rental.end_date
                )
                rental.total_amount = total_amount
                rental.save()
                
                # 更新车辆状态
                if rental.status == 'PENDING':
                    rental.vehicle.status = 'RENTED'
                    rental.vehicle.save()
                
                # 创建通知
                Notification.objects.create(
                    user=request.user,
                    notification_type='ORDER_CREATED',
                    title='订单创建成功',
                    content=f'您的订单 #{rental.id} 已创建成功。',
                    related_rental=rental
                )
                
                messages.success(request, f'订单创建成功！订单号：{rental.id}')
                return redirect('accounts:order_detail', pk=rental.pk)
    else:
        from rentals.forms import RentalForm
        form = RentalForm()
        
        # 设置客户字段（只显示当前用户的客户信息）
        form.fields['customer'].queryset = Customer.objects.filter(pk=customer.pk)
        form.fields['customer'].initial = customer
        form.fields['customer'].widget = forms.HiddenInput()  # 隐藏客户字段
        
        # 设置状态字段（默认为PENDING，用户不能修改）
        form.fields['status'].initial = 'PENDING'
        form.fields['status'].widget = forms.HiddenInput()  # 隐藏状态字段
        
        # 只显示可用车辆
        form.fields['vehicle'].queryset = Vehicle.objects.filter(status='AVAILABLE').order_by('license_plate')
        
        if vehicle_id:
            try:
                vehicle = Vehicle.objects.get(pk=vehicle_id, status='AVAILABLE')
                form.fields['vehicle'].initial = vehicle
            except Vehicle.DoesNotExist:
                messages.error(request, '选择的车辆不存在或不可用。')
    
    context = {
        'form': form,
        'customer': customer,
    }
    
    return render(request, 'accounts/order_create.html', context)


@login_required
@require_http_methods(["POST"])
def order_cancel_view(request, pk):
    """取消订单视图"""
    rental = get_object_or_404(Rental, pk=pk)
    
    # 验证订单属于当前用户
    customer = get_customer_for_user(request.user)
    
    if rental.customer != customer:
        messages.error(request, '您没有权限取消此订单。')
        return redirect('accounts:my_orders')
    
    if rental.status not in ['PENDING']:
        messages.error(request, '只能取消待确认的订单。')
        return redirect('accounts:order_detail', pk=pk)
    
    cancel_reason = request.POST.get('cancel_reason', '用户取消')
    
    with transaction.atomic():
        rental.status = 'CANCELLED'
        rental.notes = f"{rental.notes or ''}\n取消原因：{cancel_reason}".strip()
        rental.save()
        
        # 更新车辆状态
        if rental.vehicle.status == 'RENTED':
            rental.vehicle.status = 'AVAILABLE'
            rental.vehicle.save()
        
        # 创建通知
        Notification.objects.create(
            user=request.user,
            notification_type='ORDER_CANCELLED',
            title='订单已取消',
            content=f'您的订单 #{rental.id} 已取消。',
            related_rental=rental
        )
        
        messages.success(request, '订单已成功取消。')
    
    return redirect('accounts:order_detail', pk=pk)


@login_required
@require_http_methods(["GET", "POST"])
def order_review_view(request, pk):
    """订单评价视图"""
    rental = get_object_or_404(Rental, pk=pk)
    
    # 验证订单属于当前用户
    customer = None
    try:
        customer = Customer.objects.filter(user=request.user).first()
        if not customer:
            customer = Customer.objects.filter(
                Q(email=request.user.email) | Q(phone=request.user.username)
            ).first()
    except Exception:
        pass
    
    if rental.customer != customer:
        messages.error(request, '您没有权限评价此订单。')
        return redirect('accounts:my_orders')
    
    if rental.status != 'COMPLETED':
        messages.error(request, '只能评价已完成的订单。')
        return redirect('accounts:order_detail', pk=pk)
    
    # 检查是否已评价
    try:
        review = Review.objects.get(rental=rental)
        messages.info(request, '您已经评价过此订单。')
        return redirect('accounts:order_detail', pk=pk)
    except Review.DoesNotExist:
        pass
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.rental = rental
            review.user = request.user
            review.vehicle = rental.vehicle
            review.save()
            
            messages.success(request, '评价提交成功！')
            return redirect('accounts:order_detail', pk=pk)
    else:
        form = ReviewForm()
    
    context = {
        'form': form,
        'rental': rental,
    }
    
    return render(request, 'accounts/order_review.html', context)


# ========== 支付相关视图 ==========

@login_required
@require_http_methods(["GET", "POST"])
def payment_view(request, pk):
    """支付页面视图"""
    rental = get_object_or_404(Rental, pk=pk)
    
    # 验证订单属于当前用户
    customer = get_customer_for_user(request.user)
    
    if rental.customer != customer:
        messages.error(request, '您没有权限支付此订单。')
        return redirect('accounts:my_orders')
    
    if rental.status not in ['PENDING', 'ONGOING']:
        messages.error(request, '只能支付待确认或进行中的订单。')
        return redirect('accounts:order_detail', pk=pk)
    
    # 检查是否已支付
    payments = Payment.objects.filter(rental=rental)
    recent_payments = payments.order_by('-created_at')[:5]
    payment_summary = get_payment_summary(rental, payments)
    remaining_amount = payment_summary['remaining_amount']
    
    if remaining_amount <= 0:
        messages.info(request, '此订单已支付完成。')
        return redirect('accounts:order_detail', pk=pk)
    
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                payment = form.save(commit=False)
                payment.rental = rental
                payment.user = request.user
                payment.amount = remaining_amount
                payment.transaction_type = 'CHARGE'
                payment.status = 'PAID'  # 模拟支付成功
                payment.transaction_id = f'TXN{int(timezone.now().timestamp())}'
                payment.paid_at = timezone.now()
                payment.description = payment.description or '线上支付'
                payment.save()
                
                rental.refresh_financials()
                
                # 创建通知
                Notification.objects.create(
                    user=request.user,
                    notification_type='PAYMENT_SUCCESS',
                    title='支付成功',
                    content=f'您的订单 #{rental.id} 支付成功，金额：¥{remaining_amount:.2f}',
                    related_rental=rental
                )
                
                messages.success(request, f'支付成功！金额：¥{remaining_amount:.2f}')
                return redirect('accounts:order_detail', pk=pk)
    else:
        form = PaymentForm()
    
    context = {
        'form': form,
        'rental': rental,
        'remaining_amount': remaining_amount,
        'amount_paid': payment_summary['paid_amount'],
        'net_paid': payment_summary['net_paid'],
        'refunded_amount': payment_summary['refunded_amount'],
        'base_amount': payment_summary['base_amount'],
        'deposit_amount': payment_summary['deposit_amount'],
        'cross_location_fee': payment_summary['cross_location_fee'],
        'order_total_amount': payment_summary['order_total_amount'],
        'has_cross_location_fee': payment_summary['cross_location_fee'] > Decimal('0.00'),
        'recent_payments': recent_payments,
    }
    
    return render(request, 'accounts/payment.html', context)


@login_required
def payment_history_view(request):
    """支付记录视图"""
    payments = Payment.objects.filter(user=request.user).select_related(
        'rental', 'rental__vehicle'
    ).order_by('-created_at')
    
    # 筛选
    status_filter = request.GET.get('status', '')
    if status_filter:
        payments = payments.filter(status=status_filter)
    
    # 分页
    paginator = Paginator(payments, 15)
    page_number = request.GET.get('page', 1)
    payments_page = paginator.get_page(page_number)
    
    context = {
        'payments': payments_page,
        'status_filter': status_filter,
    }
    
    return render(request, 'accounts/payment_history.html', context)


@login_required
def consumption_report_view(request):
    """消费明细视图"""
    customer = get_customer_for_user(request.user)
    
    if not customer:
        messages.warning(request, '请先完善客户信息以查看消费明细。')
        return redirect('accounts:customer_info')
    
    rentals = Rental.objects.filter(customer=customer).select_related(
        'vehicle'
    ).prefetch_related('payments').order_by('-start_date')
    
    consumption_items = []
    for rental in rentals:
        rental_payments = rental.payments.all().order_by('-created_at')
        payment_summary = get_payment_summary(rental, rental_payments)
        consumption_items.append({
            'rental': rental,
            'summary': payment_summary,
            'transactions': rental_payments,
        })
    
    context = {
        'customer': customer,
        'consumption_items': consumption_items,
    }
    
    return render(request, 'accounts/consumption_report.html', context)


# ========== 消息通知相关视图 ==========

@login_required
def notifications_view(request):
    """消息通知视图"""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # 筛选
    is_read_filter = request.GET.get('is_read', '')
    if is_read_filter == 'true':
        notifications = notifications.filter(is_read=True)
    elif is_read_filter == 'false':
        notifications = notifications.filter(is_read=False)
    
    # 分页
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page', 1)
    notifications_page = paginator.get_page(page_number)
    
    # 获取未读数量
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    
    context = {
        'notifications': notifications_page,
        'unread_count': unread_count,
        'is_read_filter': is_read_filter,
    }
    
    return render(request, 'accounts/notifications.html', context)


@login_required
def notification_mark_read_view(request, pk):
    """标记通知为已读"""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect('accounts:notifications')


@login_required
def notification_mark_all_read_view(request):
    """标记所有通知为已读"""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    
    messages.success(request, '已标记所有通知为已读。')
    return redirect('accounts:notifications')


# ========== 帮助中心相关视图 ==========

def help_center_view(request):
    """帮助中心视图"""
    return render(request, 'accounts/help_center.html')


def contact_view(request):
    """联系客服视图"""
    if request.method == 'POST':
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        message = request.POST.get('message', '')
        
        # 这里简化处理，实际应该发送邮件或保存到数据库
        messages.success(request, '您的消息已提交，我们会尽快回复您。')
        return redirect('accounts:contact')
    
    return render(request, 'accounts/contact.html')
