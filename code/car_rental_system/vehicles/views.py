from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseBadRequest
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from .models import Vehicle
from .forms import VehicleForm


def index(request):
    """车辆管理首页 - 优化版本"""
    # 使用单个聚合查询优化统计信息
    vehicle_counts = Vehicle.objects.aggregate(
        total=Count('id'),
        available=Count('id', filter=Q(status='AVAILABLE')),
        rented=Count('id', filter=Q(status='RENTED')),
        maintenance=Count('id', filter=Q(status='MAINTENANCE')),
    )
    
    total_vehicles = vehicle_counts['total'] or 0
    available_vehicles = vehicle_counts['available'] or 0
    rented_vehicles = vehicle_counts['rented'] or 0
    maintenance_vehicles = vehicle_counts['maintenance'] or 0
    
    # 获取最近添加的车辆
    recent_vehicles = Vehicle.objects.all()[:5]
    
    context = {
        'total_vehicles': total_vehicles,
        'available_vehicles': available_vehicles,
        'rented_vehicles': rented_vehicles,
        'maintenance_vehicles': maintenance_vehicles,
        'recent_vehicles': recent_vehicles,
    }
    
    return render(request, 'vehicles/index.html', context)


def vehicle_list(request):
    """车辆列表页 - 支持搜索、筛选和分页（优化版本）"""
    # 获取查询参数
    query = request.GET.get('q', '')
    brand_filter = request.GET.get('brand', '')
    type_filter = request.GET.get('type', '')
    status_filter = request.GET.get('status', '')
    page = request.GET.get('page', 1)
    
    # 构建查询 - 只选择需要的字段
    vehicles = Vehicle.objects.only(
        'id', 'license_plate', 'brand', 'model', 'vehicle_type', 
        'color', 'seats', 'daily_rate', 'status', 'created_at'
    )
    
    # 获取座位数筛选参数
    seats_filter = request.GET.get('seats', '')
    
    # 搜索功能
    if query:
        vehicles = vehicles.filter(
            Q(license_plate__icontains=query) |
            Q(brand__icontains=query) |
            Q(model__icontains=query)
        )
    
    # 筛选功能
    if brand_filter:
        vehicles = vehicles.filter(brand=brand_filter)
    
    if type_filter:
        vehicles = vehicles.filter(vehicle_type=type_filter)
    
    if status_filter:
        vehicles = vehicles.filter(status=status_filter)
    
    # 座位数筛选（只有在字段存在时才执行）
    if seats_filter:
        try:
            seats = int(seats_filter)
            # 尝试使用seats字段筛选，如果字段不存在会抛出异常
            vehicles = vehicles.filter(seats=seats)
        except (ValueError, Exception):
            # 如果转换失败或字段不存在，忽略筛选
            pass
    
    # 优化：只在需要时获取筛选选项（延迟加载）
    # 使用缓存或只在首次加载时获取
    from django.core.cache import cache
    cache_key_brands = 'vehicle_brands_list'
    cache_key_types = 'vehicle_types_list'
    
    brands = cache.get(cache_key_brands)
    if brands is None:
        brands = list(Vehicle.objects.values_list('brand', flat=True).distinct().order_by('brand'))
        cache.set(cache_key_brands, brands, 300)  # 缓存5分钟
    
    types = cache.get(cache_key_types)
    if types is None:
        types = list(Vehicle.objects.values_list('vehicle_type', flat=True).distinct().order_by('vehicle_type'))
        cache.set(cache_key_types, types, 300)  # 缓存5分钟
    
    # 分页 - 每页10条，先排序再分页
    vehicles = vehicles.order_by('-created_at')
    paginator = Paginator(vehicles, 10)
    vehicles_page = paginator.get_page(page)
    
    # 获取座位数选项（使用缓存）
    cache_key_seats = 'vehicle_seats_list'
    seats_options = cache.get(cache_key_seats)
    if seats_options is None:
        try:
            # 检查字段是否存在（如果迁移未应用，会抛出异常）
            seats_values = list(Vehicle.objects.values_list('seats', flat=True))
            seats_options = sorted({seat for seat in seats_values if seat})
            cache.set(cache_key_seats, seats_options, 300)  # 缓存5分钟
        except Exception:
            # 如果字段不存在（迁移未应用），使用空列表
            seats_options = []
            cache.set(cache_key_seats, seats_options, 300)
    
    context = {
        'vehicles': vehicles_page,
        'brands': brands,
        'types': types,
        'seats_options': seats_options,
        'query': query,
        'brand_filter': brand_filter,
        'type_filter': type_filter,
        'status_filter': status_filter,
        'seats_filter': seats_filter,
    }
    
    return render(request, 'vehicles/vehicle_list.html', context)


def vehicle_detail(request, pk):
    """车辆详情页（优化版本）"""
    vehicle = get_object_or_404(Vehicle, pk=pk)
    
    # 获取相关租赁订单（如果有的话）- 使用select_related优化
    from rentals.models import Rental
    from django.db.models import Count, Q
    
    rental_orders = Rental.objects.filter(vehicle=vehicle).select_related('customer').order_by('-created_at')[:10]
    
    # 计算租赁统计数据
    rental_stats = Rental.objects.filter(vehicle=vehicle).aggregate(
        total=Count('id'),
        active=Count('id', filter=Q(status='ONGOING')),
        completed=Count('id', filter=Q(status='COMPLETED')),
    )
    
    context = {
        'vehicle': vehicle,
        'rental_orders': rental_orders,
        'rental_stats': {
            'total': rental_stats['total'] or 0,
            'active': rental_stats['active'] or 0,
            'completed': rental_stats['completed'] or 0,
        },
    }
    
    return render(request, 'vehicles/vehicle_detail.html', context)


@require_http_methods(["GET", "POST"])
def vehicle_create(request):
    """车辆信息录入（优化版本）"""
    if request.method == 'POST':
        form = VehicleForm(request.POST)
        if form.is_valid():
            vehicle = form.save()
            # 清除相关缓存
            from django.core.cache import cache
            cache.delete('vehicle_brands_list')
            cache.delete('vehicle_types_list')
            cache.delete('rental_filter_vehicles')
            
            messages.success(request, f'车辆 {vehicle.license_plate} 添加成功！')
            return redirect('vehicles:vehicle_detail', pk=vehicle.pk)
    else:
        form = VehicleForm()
    
    context = {
        'form': form,
        'title': '添加车辆',
        'action': '创建',
    }
    
    return render(request, 'vehicles/vehicle_form.html', context)


@require_http_methods(["GET", "POST"])
def vehicle_update(request, pk):
    """车辆信息修改（优化版本）"""
    vehicle = get_object_or_404(Vehicle, pk=pk)
    
    if request.method == 'POST':
        form = VehicleForm(request.POST, instance=vehicle)
        if form.is_valid():
            vehicle = form.save()
            # 清除相关缓存
            from django.core.cache import cache
            cache.delete('vehicle_brands_list')
            cache.delete('vehicle_types_list')
            cache.delete('rental_filter_vehicles')
            
            messages.success(request, f'车辆 {vehicle.license_plate} 更新成功！')
            return redirect('vehicles:vehicle_detail', pk=vehicle.pk)
    else:
        form = VehicleForm(instance=vehicle)
    
    context = {
        'form': form,
        'vehicle': vehicle,
        'title': f'编辑车辆 - {vehicle.license_plate}',
        'action': '更新',
    }
    
    return render(request, 'vehicles/vehicle_form.html', context)


@require_http_methods(["GET", "POST"])
def vehicle_delete(request, pk):
    """车辆信息删除"""
    vehicle = get_object_or_404(Vehicle, pk=pk)
    
    # 检查是否有活跃的租赁订单 - 使用正确的模型
    from rentals.models import Rental
    active_rentals = Rental.objects.filter(vehicle=vehicle, status__in=['PENDING', 'ONGOING']).only('id')
    
    if request.method == 'POST':
        if active_rentals.exists():
            messages.error(request, f'无法删除车辆 {vehicle.license_plate}，因为有活跃的租赁订单。')
            return redirect('vehicles:vehicle_detail', pk=vehicle.pk)
        
        license_plate = vehicle.license_plate
        vehicle.delete()
        
        # 清除相关缓存
        from django.core.cache import cache
        cache.delete('vehicle_brands_list')
        cache.delete('vehicle_types_list')
        cache.delete('rental_filter_vehicles')
        
        messages.success(request, f'车辆 {license_plate} 删除成功！')
        return redirect('vehicles:vehicle_list')
    
    context = {
        'vehicle': vehicle,
        'active_rentals': active_rentals,
    }
    
    return render(request, 'vehicles/vehicle_confirm_delete.html', context)


@require_http_methods(["POST"])
def vehicle_status_update(request, pk):
    """车辆状态管理"""
    vehicle = get_object_or_404(Vehicle, pk=pk)
    
    new_status = request.POST.get('status')
    
    # 验证状态值
    if new_status not in dict(Vehicle.VEHICLE_STATUS_CHOICES):
        messages.error(request, '无效的车辆状态。')
        return redirect('vehicles:vehicle_detail', pk=vehicle.pk)
    
    # 检查状态变更是否合法
    if vehicle.status == 'RENTED' and new_status == 'AVAILABLE':
        # 只有没有活跃租赁的车辆才能设为可用
        from rentals.models import Rental
        active_rentals = Rental.objects.filter(vehicle=vehicle, status='ONGOING').only('id')
        if active_rentals.exists():
            messages.error(request, '无法将状态设置为可用，因为该车辆正在被租用。')
            return redirect('vehicles:vehicle_detail', pk=vehicle.pk)
    
    old_status = vehicle.get_status_display()
    vehicle.status = new_status
    vehicle.save()
    
    new_status_display = vehicle.get_status_display()
    messages.success(request, f'车辆 {vehicle.license_plate} 状态已从 "{old_status}" 更新为 "{new_status_display}"')
    
    # 如果是Ajax请求，返回JSON响应
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return HttpResponse('{"success": true, "status": "' + new_status_display + '"}', 
                          content_type='application/json')
    
    return redirect('vehicles:vehicle_detail', pk=vehicle.pk)