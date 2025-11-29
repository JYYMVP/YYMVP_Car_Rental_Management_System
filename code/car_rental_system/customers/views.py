from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, Prefetch
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.urls import reverse
from decimal import Decimal
import json
from .models import Customer
from .forms import CustomerForm, CustomerSearchForm, MembershipUpdateForm
from rentals.models import Rental


def index(request):
    """客户管理首页"""
    customer_count = Customer.objects.count()
    vip_count = Customer.objects.filter(member_level='VIP').count()
    normal_count = Customer.objects.filter(member_level='NORMAL').count()
    
    # 最近添加的客户
    recent_customers = Customer.objects.all()[:5]
    
    context = {
        'customer_count': customer_count,
        'vip_count': vip_count,
        'normal_count': normal_count,
        'recent_customers': recent_customers,
    }
    return render(request, 'customers/index.html', context)


def customer_list(request):
    """客户列表页 - 优化版本，避免N+1查询"""
    # 获取所有客户
    customers = Customer.objects.all()
    
    # 处理搜索和筛选
    search_form = CustomerSearchForm(request.GET)
    if search_form.is_valid():
        search = search_form.cleaned_data.get('search')
        member_level = search_form.cleaned_data.get('member_level')
        
        if search:
            customers = customers.filter(
                Q(name__icontains=search) | 
                Q(phone__icontains=search)
            )
        
        if member_level:
            customers = customers.filter(member_level=member_level)
    
    # 使用聚合查询一次性获取所有客户的统计信息，避免N+1查询
    from django.db.models import Prefetch
    customers = customers.prefetch_related(
        Prefetch('rentals', queryset=Rental.objects.only('total_amount'))
    ).annotate(
        total_rentals=Count('rentals'),
        total_amount=Sum('rentals__total_amount')
    )
    
    # 分页（每页10条）
    paginator = Paginator(customers, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 优化：避免重复查询总数
    total_customers = customers.count() if not search_form.is_valid() or not (search_form.cleaned_data.get('search') or search_form.cleaned_data.get('member_level')) else page_obj.paginator.count
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'total_customers': total_customers,
    }
    return render(request, 'customers/customer_list.html', context)


def customer_detail(request, pk):
    """客户详情页"""
    customer = get_object_or_404(Customer, pk=pk)
    
    # 获取客户的所有租赁记录
    rentals = customer.rentals.all().select_related('vehicle').order_by('-created_at')
    
    # 计算统计信息
    total_rentals = rentals.count()
    total_amount = rentals.aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    # 按状态统计
    status_stats = rentals.values('status').annotate(
        count=Count('id')
    ).order_by('status')
    
    # 计算VIP节省的金额（假设VIP享受9折优惠）
    vip_discount_amount = 0
    if customer.member_level == 'VIP' and total_amount:
        vip_discount_amount = total_amount * Decimal('0.1')
    
    # 检查是否符合VIP升级条件（如果不是VIP）
    vip_upgrade_info = None
    if customer.member_level != 'VIP':
        is_eligible, consecutive_count = customer.check_vip_upgrade_eligibility()
        vip_upgrade_info = {
            'is_eligible': is_eligible,
            'consecutive_count': consecutive_count,
            'remaining': max(0, 10 - consecutive_count)
        }
    
    context = {
        'customer': customer,
        'rentals': rentals,
        'total_rentals': total_rentals,
        'total_amount': total_amount,
        'status_stats': status_stats,
        'vip_discount_amount': vip_discount_amount,
        'vip_upgrade_info': vip_upgrade_info,
    }
    return render(request, 'customers/customer_detail.html', context)


def customer_create(request):
    """添加客户"""
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            messages.success(request, f'客户 "{customer.name}" 添加成功！')
            return redirect('customers:customer_detail', pk=customer.pk)
    else:
        form = CustomerForm()
    
    context = {
        'form': form,
        'title': '添加客户',
        'action_url': reverse('customers:customer_create'),
    }
    return render(request, 'customers/customer_form.html', context)


def customer_update(request, pk):
    """编辑客户"""
    customer = get_object_or_404(Customer, pk=pk)
    
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            customer = form.save()
            messages.success(request, f'客户 "{customer.name}" 信息更新成功！')
            return redirect('customers:customer_detail', pk=customer.pk)
    else:
        form = CustomerForm(instance=customer)
    
    context = {
        'form': form,
        'customer': customer,
        'title': '编辑客户',
        'action_url': reverse('customers:customer_update', kwargs={'pk': pk}),
    }
    return render(request, 'customers/customer_form.html', context)


def customer_delete(request, pk):
    """删除客户"""
    customer = get_object_or_404(Customer, pk=pk)
    
    # 检查是否有未完成的租赁订单
    active_rentals = customer.rentals.filter(
        status__in=['PENDING', 'ONGOING']
    ).count()
    
    if request.method == 'POST':
        if active_rentals > 0:
            messages.error(
                request, 
                f'无法删除客户 "{customer.name}"，因为该客户还有 {active_rentals} 个未完成的租赁订单。'
            )
            return redirect('customers:customer_detail', pk=customer.pk)
        
        customer_name = customer.name
        customer.delete()
        messages.success(request, f'客户 "{customer_name}" 删除成功！')
        return redirect('customers:customer_list')
    
    context = {
        'customer': customer,
        'active_rentals': active_rentals,
    }
    return render(request, 'customers/customer_confirm_delete.html', context)


@require_http_methods(["POST"])
@csrf_exempt
def customer_membership_update(request, pk):
    """Ajax更新客户会员等级"""
    customer = get_object_or_404(Customer, pk=pk)
    
    try:
        data = json.loads(request.body)
        new_level = data.get('member_level')
        
        if new_level not in dict(Customer.MEMBER_LEVEL_CHOICES):
            return JsonResponse({
                'success': False,
                'error': '无效的会员等级'
            })
        
        old_level = customer.member_level
        customer.member_level = new_level
        customer.save()
        
        return JsonResponse({
            'success': True,
            'message': f'客户 "{customer.name}" 会员等级已从 {dict(Customer.MEMBER_LEVEL_CHOICES)[old_level]} 更新为 {dict(Customer.MEMBER_LEVEL_CHOICES)[new_level]}',
            'new_level': new_level,
            'new_level_name': dict(Customer.MEMBER_LEVEL_CHOICES)[new_level]
        })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': '无效的请求数据'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'更新失败: {str(e)}'
        })


def get_customer_statistics(request):
    """获取客户统计信息的API端点"""
    total_customers = Customer.objects.count()
    vip_count = Customer.objects.filter(member_level='VIP').count()
    normal_count = Customer.objects.filter(member_level='NORMAL').count()
    
    # 租赁统计
    total_rentals = Rental.objects.count()
    total_revenue = Rental.objects.aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    # 活跃客户（最近30天有租赁的客户）
    from django.utils import timezone
    from datetime import timedelta
    recent_date = timezone.now().date() - timedelta(days=30)
    active_customers = Customer.objects.filter(
        rentals__start_date__gte=recent_date
    ).distinct().count()
    
    data = {
        'total_customers': total_customers,
        'vip_count': vip_count,
        'normal_count': normal_count,
        'total_rentals': total_rentals,
        'total_revenue': float(total_revenue),
        'active_customers': active_customers,
    }
    
    return JsonResponse(data)