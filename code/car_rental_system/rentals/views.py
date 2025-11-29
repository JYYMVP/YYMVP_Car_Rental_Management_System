from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import date, datetime, timedelta
from decimal import Decimal

from .models import Rental
from .forms import RentalForm, RentalStatusForm, ReturnForm, CancelForm
from customers.models import Customer
from vehicles.models import Vehicle


def index(request):
    """租赁管理首页"""
    # 自动更新订单状态
    Rental.auto_update_status()
    
    today = date.today()
    this_month_start = today.replace(day=1)
    
    # 使用单个聚合查询优化统计数据
    rental_counts = Rental.objects.aggregate(
        total=Count('id'),
        pending=Count('id', filter=Q(status='PENDING')),
        ongoing=Count('id', filter=Q(status='ONGOING')),
        completed=Count('id', filter=Q(status='COMPLETED')),
        today=Count('id', filter=Q(start_date=today)),
    )
    
    this_month_revenue = Rental.objects.filter(
        status='COMPLETED',
        start_date__gte=this_month_start
    ).aggregate(
        total=Sum('total_amount')
    )['total'] or Decimal('0.00')
    
    stats = {
        'total_rentals': rental_counts['total'] or 0,
        'pending_rentals': rental_counts['pending'] or 0,
        'ongoing_rentals': rental_counts['ongoing'] or 0,
        'completed_rentals': rental_counts['completed'] or 0,
        'today_rentals': rental_counts['today'] or 0,
        'this_month_revenue': this_month_revenue,
    }
    
    # 最近订单
    recent_rentals = Rental.objects.select_related('customer', 'vehicle').all()[:5]
    
    context = {
        'stats': stats,
        'recent_rentals': recent_rentals,
    }
    
    return render(request, 'rentals/rental_index.html', context)


def rental_list(request):
    """租赁订单列表页"""
    # 自动更新订单状态
    Rental.auto_update_status()
    
    # 获取筛选参数
    status_filter = request.GET.get('status', '')
    customer_filter = request.GET.get('customer', '')
    vehicle_filter = request.GET.get('vehicle', '')
    search_query = request.GET.get('search', '')
    
    # 构建查询
    queryset = Rental.objects.select_related('customer', 'vehicle').all()
    
    # 状态筛选
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    
    # 客户筛选
    if customer_filter:
        queryset = queryset.filter(customer_id=customer_filter)
    
    # 车辆筛选
    if vehicle_filter:
        queryset = queryset.filter(vehicle_id=vehicle_filter)
    
    # 搜索
    if search_query:
        queryset = queryset.filter(
            Q(customer__name__icontains=search_query) |
            Q(vehicle__license_plate__icontains=search_query) |
            Q(pk__icontains=search_query)
        )
    
    # 分页
    paginator = Paginator(queryset.order_by('-created_at'), 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 获取筛选选项 - 使用缓存提高性能
    from django.core.cache import cache
    
    cache_key_customers = 'rental_filter_customers'
    cache_key_vehicles = 'rental_filter_vehicles'
    
    customers = cache.get(cache_key_customers)
    if customers is None:
        customers = list(Customer.objects.only('id', 'name').order_by('name')[:100])
        cache.set(cache_key_customers, customers, 300)  # 缓存5分钟
    
    vehicles = cache.get(cache_key_vehicles)
    if vehicles is None:
        vehicles = list(Vehicle.objects.only('id', 'license_plate', 'brand', 'model').order_by('license_plate')[:100])
        cache.set(cache_key_vehicles, vehicles, 300)  # 缓存5分钟
    
    context = {
        'page_obj': page_obj,
        'customers': customers,
        'vehicles': vehicles,
        'status_filter': status_filter,
        'customer_filter': customer_filter,
        'vehicle_filter': vehicle_filter,
        'search_query': search_query,
    }
    
    return render(request, 'rentals/rental_list.html', context)


def rental_detail(request, pk):
    """租赁订单详情页"""
    # 自动更新订单状态
    Rental.auto_update_status()
    
    rental = get_object_or_404(
        Rental.objects.select_related('customer', 'vehicle'), 
        pk=pk
    )
    
    # 计算费用详情
    cost_details = calculate_rental_cost(rental)
    
    # 状态转换选项
    status_form = RentalStatusForm(instance=rental)
    
    context = {
        'rental': rental,
        'cost_details': cost_details,
        'status_form': status_form,
    }
    
    return render(request, 'rentals/rental_detail.html', context)


def rental_create(request):
    """创建租赁订单"""
    if request.method == 'POST':
        form = RentalForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                rental = form.save(commit=False)
                
                # 计算并设置总费用
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
                
                messages.success(request, f'租赁订单创建成功！订单号：{rental.id}')
                return redirect('rentals:rental_detail', pk=rental.pk)
    else:
        form = RentalForm()
    
    context = {
        'form': form,
        'title': '创建租赁订单',
    }
    
    return render(request, 'rentals/rental_form.html', context)


def rental_update(request, pk):
    """修改租赁订单"""
    rental = get_object_or_404(Rental, pk=pk)
    
    if request.method == 'POST':
        form = RentalForm(request.POST, instance=rental)
        if form.is_valid():
            with transaction.atomic():
                rental = form.save(commit=False)
                
                # 重新计算费用
                total_amount = calculate_rental_amount(
                    rental.customer,
                    rental.vehicle,
                    rental.start_date,
                    rental.end_date
                )
                rental.total_amount = total_amount
                rental.save()
                
                # 如果状态从非预订变为预订中，更新车辆状态
                if rental.status == 'PENDING' and rental.vehicle.status == 'AVAILABLE':
                    rental.vehicle.status = 'RENTED'
                    rental.vehicle.save()
                
                messages.success(request, '租赁订单修改成功！')
                return redirect('rentals:rental_detail', pk=rental.pk)
    else:
        form = RentalForm(instance=rental)
        
        # 如果订单已进行中或已完成，不允许修改客户和车辆
        if rental.status in ['ONGOING', 'COMPLETED', 'CANCELLED']:
            form.fields['customer'].widget.attrs['disabled'] = True
            form.fields['vehicle'].widget.attrs['disabled'] = True
    
    context = {
        'form': form,
        'rental': rental,
        'title': '编辑租赁订单',
    }
    
    return render(request, 'rentals/rental_form.html', context)


def rental_status_update(request, pk):
    """更新订单状态"""
    rental = get_object_or_404(Rental, pk=pk)
    
    if request.method == 'POST':
        form = RentalStatusForm(request.POST, instance=rental)
        if form.is_valid():
            old_status = rental.status
            rental = form.save()
            
            # 根据状态变化更新车辆状态
            with transaction.atomic():
                if old_status == 'PENDING' and rental.status == 'ONGOING':
                    # 预订中 → 进行中
                    rental.vehicle.status = 'RENTED'
                    rental.vehicle.save()
                    messages.success(request, '订单状态已更新为进行中')
                
                elif old_status in ['PENDING', 'ONGOING'] and rental.status == 'COMPLETED':
                    # 预订中/进行中 → 已完成
                    rental.vehicle.status = 'AVAILABLE'
                    rental.vehicle.save()
                    messages.success(request, '订单已完成，车辆已归还')
                
                elif rental.status == 'CANCELLED':
                    # 任何状态 → 已取消
                    if rental.vehicle.status == 'RENTED':
                        rental.vehicle.status = 'AVAILABLE'
                        rental.vehicle.save()
                    messages.success(request, '订单已取消')
                else:
                    messages.success(request, '状态更新成功')
            
            return redirect('rentals:rental_detail', pk=rental.pk)
    else:
        form = RentalStatusForm(instance=rental)
    
    context = {
        'form': form,
        'rental': rental,
    }
    
    return render(request, 'rentals/rental_status_form.html', context)


def rental_return(request, pk):
    """车辆归还处理"""
    # 自动更新订单状态（确保状态是最新的）
    Rental.auto_update_status()
    
    rental = get_object_or_404(Rental, pk=pk)
    
    # 检查订单状态，只有进行中或已超时未归还的订单才能还车
    if rental.status not in ['ONGOING', 'OVERDUE']:
        messages.error(request, f'只有进行中或已超时未归还的订单才能办理还车，当前订单状态：{rental.get_status_display()}')
        return redirect('rentals:rental_detail', pk=rental.pk)
    
    if request.method == 'POST':
        form = ReturnForm(request.POST)
        if form.is_valid():
            actual_return_date = form.cleaned_data['actual_return_date']
            actual_return_location = form.cleaned_data.get('actual_return_location', '').strip() or None
            
            # 如果未填写还车门店，使用取车门店
            if not actual_return_location:
                actual_return_location = rental.pickup_location
            
            with transaction.atomic():
                # 更新还车信息
                rental.actual_return_date = actual_return_date
                rental.actual_return_location = actual_return_location
                
                # 判断是否实际异地还车（实际还车门店与取车门店不同）
                actual_is_cross_location = (
                    actual_return_location and 
                    actual_return_location.strip() != rental.pickup_location.strip()
                )
                
                # 计算异地还车费用
                cross_location_fee_to_add = Decimal('0.00')
                if actual_is_cross_location:
                    # 如果租车时未勾选异地还车，但实际异地还车了，需要增加费用
                    if not rental.is_cross_location_return:
                        # 默认异地还车费用为日租金的50%（可根据实际业务调整）
                        cross_location_fee_to_add = rental.vehicle.daily_rate * Decimal('0.5')
                        rental.cross_location_fee = cross_location_fee_to_add
                        rental.is_cross_location_return = True
                        rental.return_location = actual_return_location
                
                # 计算超时还车费用
                overdue_fee = Decimal('0.00')
                if actual_return_date > rental.end_date:
                    # 超期租赁，计算超时费用
                    extra_days = (actual_return_date - rental.end_date).days
                    # 超时费用按日租金计算（可根据实际业务调整，如1.5倍日租金）
                    overdue_fee = rental.vehicle.daily_rate * Decimal(str(extra_days))
                    rental.overdue_fee = overdue_fee
                
                # 更新订单状态为已完成
                rental.status = 'COMPLETED'
                rental.save()
                
                # 检查该车辆是否还有其他进行中的订单
                other_ongoing_rentals = Rental.objects.filter(
                    vehicle=rental.vehicle,
                    status='ONGOING'
                ).exclude(pk=rental.pk).count()
                
                # 如果没有其他进行中的订单，更新车辆状态为可用
                if other_ongoing_rentals == 0:
                    rental.vehicle.status = 'AVAILABLE'
                    rental.vehicle.save()
                
                # 退还押金
                # 获取退款用户（优先使用客户关联的用户）
                refund_user = None
                if rental.customer and rental.customer.user:
                    refund_user = rental.customer.user
                deposit_refunded, deposit_refund_amount = rental.refund_deposit(user=refund_user)
                
                # 刷新财务信息
                rental.refresh_financials()
                
                # 检查是否符合VIP升级条件，如果符合则自动升级
                vip_upgraded = False
                if rental.customer and rental.customer.member_level != 'VIP':
                    is_eligible, consecutive_count = rental.customer.check_vip_upgrade_eligibility()
                    if is_eligible:
                        vip_upgraded = rental.customer.upgrade_to_vip()
                
                # 构建成功消息
                fee_details = []
                if cross_location_fee_to_add > 0:
                    fee_details.append(f'异地还车费用：¥{cross_location_fee_to_add:.2f}')
                if overdue_fee > 0:
                    fee_details.append(f'超时还车费用：¥{overdue_fee:.2f}')
                if deposit_refunded:
                    fee_details.append(f'押金退还：¥{deposit_refund_amount:.2f}')
                
                total_fee_message = f'车辆归还成功！订单总额：¥{rental.calculate_order_total():.2f}'
                if fee_details:
                    total_fee_message += f'（含：{", ".join(fee_details)}）'
                if vip_upgraded:
                    total_fee_message += f' 客户 {rental.customer.name} 由于连续10个订单表现优异，已自动升级为VIP会员！'
                
                messages.success(request, total_fee_message)
                return redirect('rentals:rental_detail', pk=rental.pk)
    else:
        # 设置默认还车门店为取车门店
        form = ReturnForm(initial={
            'actual_return_location': rental.pickup_location
        })
    
    context = {
        'form': form,
        'rental': rental,
    }
    
    return render(request, 'rentals/rental_confirm_return.html', context)


def rental_cancel(request, pk):
    """取消租赁订单"""
    from accounts.models import Payment  # 避免循环导入
    from accounts.views import get_payment_summary  # 导入支付汇总函数
    
    rental = get_object_or_404(Rental, pk=pk)
    
    if request.method == 'POST':
        form = CancelForm(request.POST)
        if form.is_valid():
            cancel_reason = form.cleaned_data['cancel_reason']
            
            with transaction.atomic():
                # 获取已支付金额（扣除已退款金额）
                payment_summary = get_payment_summary(rental)
                paid_amount = payment_summary['paid_amount']
                refunded_amount = payment_summary['refunded_amount']
                net_paid = paid_amount - refunded_amount
                
                rental.status = 'CANCELLED'
                rental.notes = f"{rental.notes or ''}\n取消原因：{cancel_reason}".strip()
                rental.save()
                
                # 如果有已支付金额，创建退款记录
                if net_paid > Decimal('0.00'):
                    # 获取用户（优先使用支付记录中的用户，否则使用客户关联的用户）
                    payment_user = Payment.objects.filter(
                        rental=rental,
                        transaction_type='CHARGE',
                        status='PAID'
                    ).order_by('created_at').first()
                    refund_user = payment_user.user if payment_user else None
                    if not refund_user and rental.customer and rental.customer.user:
                        refund_user = rental.customer.user
                    
                    if refund_user:
                        Payment.objects.create(
                            rental=rental,
                            user=refund_user,
                            amount=net_paid,
                            payment_method='BANK',  # 退款方式默认银行卡
                            transaction_type='REFUND',
                            status='REFUNDED',
                            description=f'订单取消，退还已支付金额 ¥{net_paid:.2f}',
                            paid_at=timezone.now(),
                            transaction_id=f'REF{int(timezone.now().timestamp())}'
                        )
                        
                        # 更新订单财务信息
                        rental.refresh_financials()
                        
                        messages.success(request, f'订单已成功取消，已退还 ¥{net_paid:.2f} 给 {refund_user.username}。')
                    else:
                        messages.warning(request, f'订单已成功取消，但未找到退款用户，退款金额：¥{net_paid:.2f}，请手动处理。')
                else:
                    messages.success(request, '订单已成功取消。')
                
                # 如果车辆是已租状态，恢复为可用
                if rental.vehicle.status == 'RENTED':
                    rental.vehicle.status = 'AVAILABLE'
                    rental.vehicle.save()
                
                return redirect('rentals:rental_detail', pk=rental.pk)
    else:
        form = CancelForm()
    
    context = {
        'form': form,
        'rental': rental,
    }
    
    return render(request, 'Rentals/rental_confirm_cancel.html', context)


def calculate_rental_amount(customer, vehicle, start_date, end_date):
    """计算租赁费用"""
    # 计算租赁天数
    rental_days = (end_date - start_date).days + 1
    
    # 基础费用
    base_amount = vehicle.daily_rate * rental_days
    
    # VIP折扣
    if customer.member_level == 'VIP':
        discount = base_amount * Decimal('0.10')  # 10%折扣
        total_amount = base_amount - discount
    else:
        total_amount = base_amount
    
    return total_amount


def calculate_rental_cost(rental):
    """计算租赁费用详情"""
    cost_details = {
        'base_amount': Decimal('0.00'),
        'discount': Decimal('0.00'),
        'extra_amount': Decimal('0.00'),
        'overdue_fee': Decimal('0.00'),
        'cross_location_fee': Decimal('0.00'),
        'deposit': Decimal('0.00'),
        'total_amount': Decimal('0.00'),
        'rental_days': 0,
        'extra_days': 0,
    }
    
    if rental.start_date and rental.end_date:
        # 基础信息
        cost_details['rental_days'] = (rental.end_date - rental.start_date).days + 1
        cost_details['base_amount'] = rental.vehicle.daily_rate * cost_details['rental_days']
        
        # VIP折扣
        if rental.customer.member_level == 'VIP':
            cost_details['discount'] = cost_details['base_amount'] * Decimal('0.10')
        
        cost_details['total_amount'] = cost_details['base_amount'] - cost_details['discount']
        
        # 押金
        cost_details['deposit'] = rental.deposit or Decimal('0.00')
        
        # 超时费用（使用overdue_fee字段，如果已设置）
        if rental.overdue_fee:
            cost_details['overdue_fee'] = rental.overdue_fee
            cost_details['extra_days'] = (rental.actual_return_date - rental.end_date).days if rental.actual_return_date and rental.actual_return_date > rental.end_date else 0
            cost_details['extra_amount'] = cost_details['overdue_fee']
        elif rental.actual_return_date and rental.actual_return_date > rental.end_date:
            # 如果没有设置overdue_fee，但实际还车日期超过结束日期，计算超时费用
            cost_details['extra_days'] = (rental.actual_return_date - rental.end_date).days
            cost_details['extra_amount'] = rental.vehicle.daily_rate * Decimal(str(cost_details['extra_days']))
            cost_details['overdue_fee'] = cost_details['extra_amount']
        
        cost_details['total_amount'] += cost_details['overdue_fee']
        
        # 异地还车费用
        if rental.is_cross_location_return:
            cost_details['cross_location_fee'] = rental.cross_location_fee or Decimal('0.00')
            cost_details['total_amount'] += cost_details['cross_location_fee']
    
    return cost_details


def get_vehicle_available_dates(request):
    """获取车辆可用日期（用于前端验证）"""
    vehicle_id = request.GET.get('vehicle_id')
    if not vehicle_id:
        return JsonResponse({'error': '车辆ID是必需的'}, status=400)
    
    try:
        vehicle = Vehicle.objects.get(id=vehicle_id)
        # 检查车辆是否有预订中、进行中或已超时未归还的订单
        rentals = vehicle.rentals.filter(
            status__in=['PENDING', 'ONGOING', 'OVERDUE']
        ).order_by('start_date')
        
        busy_dates = []
        for rental in rentals:
            current_date = rental.start_date
            end_date = rental.end_date
            while current_date <= end_date:
                busy_dates.append(current_date.isoformat())
                current_date += timedelta(days=1)
        
        return JsonResponse({
            'vehicle_id': vehicle_id,
            'busy_dates': busy_dates,
            'is_available': vehicle.status == 'AVAILABLE'
        })
    except Vehicle.DoesNotExist:
        return JsonResponse({'error': '车辆不存在'}, status=404)