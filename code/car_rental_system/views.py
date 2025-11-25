"""
租车管理系统主页面视图
处理仪表板数据统计和展示
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta
from django.http import HttpResponseNotFound, HttpResponseServerError, HttpResponseForbidden
from vehicles.models import Vehicle
from customers.models import Customer
from rentals.models import Rental
from accounts.models import Review
from accounts.forms import ReviewAdminForm
from django.contrib import messages
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods


@login_required(login_url='/accounts/login/')
def dashboard(request):
    """
    主页面仪表板视图
    显示系统关键统计数据和最近活动
    """
    try:
        # 使用单个聚合查询优化车辆统计（减少数据库查询次数）
        vehicle_counts = Vehicle.objects.aggregate(
            total=Count('id'),
            available=Count('id', filter=Q(status='AVAILABLE')),
            rented=Count('id', filter=Q(status='RENTED')),
            maintenance=Count('id', filter=Q(status='MAINTENANCE')),
        )
        vehicle_stats = {
            'total': vehicle_counts['total'] or 0,
            'available': vehicle_counts['available'] or 0,
            'rented': vehicle_counts['rented'] or 0,
            'maintenance': vehicle_counts['maintenance'] or 0,
        }
        
        # 使用单个聚合查询优化客户统计
        customer_counts = Customer.objects.aggregate(
            total=Count('id'),
            regular=Count('id', filter=Q(member_level='NORMAL')),
            vip=Count('id', filter=Q(member_level='VIP')),
        )
        customer_stats = {
            'total': customer_counts['total'] or 0,
            'regular': customer_counts['regular'] or 0,
            'vip': customer_counts['vip'] or 0,
        }
        
        # 使用单个聚合查询优化订单统计
        rental_counts = Rental.objects.aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(status__in=['PENDING', 'ONGOING'])),
            completed=Count('id', filter=Q(status='COMPLETED')),
            cancelled=Count('id', filter=Q(status='CANCELLED')),
        )
        rental_stats = {
            'total': rental_counts['total'] or 0,
            'active': rental_counts['active'] or 0,
            'completed': rental_counts['completed'] or 0,
            'cancelled': rental_counts['cancelled'] or 0,
        }
        
        # 收入统计 - 使用单个查询
        today = timezone.now().date()
        month_start = today.replace(day=1)
        completed_rentals = Rental.objects.filter(status='COMPLETED')
        
        revenue_aggregate = completed_rentals.aggregate(
            total=Sum('total_amount'),
            monthly=Sum('total_amount', filter=Q(end_date__gte=month_start)),
            today=Sum('total_amount', filter=Q(end_date=today)),
        )
        revenue_stats = {
            'total': revenue_aggregate['total'] or 0,
            'monthly': revenue_aggregate['monthly'] or 0,
            'today': revenue_aggregate['today'] or 0,
        }
        
        # 最近订单 - 使用select_related避免N+1查询
        recent_rentals = Rental.objects.select_related(
            'customer', 'vehicle'
        ).order_by('-created_at')[:10]
        
        # 车辆状态概览 - 使用select_related并限制查询
        vehicle_status = Vehicle.objects.select_related().order_by('status', 'license_plate')[:20]
        
        context = {
            'vehicle_stats': vehicle_stats,
            'customer_stats': customer_stats,
            'rental_stats': rental_stats,
            'revenue_stats': revenue_stats,
            'recent_rentals': recent_rentals,
            'vehicle_status': vehicle_status,
        }
        
        return render(request, 'dashboard.html', context)
        
    except Exception as e:
        # 错误处理 - 提供默认的空数据
        print(f"Dashboard error: {e}")
        context = {
            'vehicle_stats': {'total': 0, 'available': 0, 'rented': 0, 'maintenance': 0},
            'customer_stats': {'total': 0, 'regular': 0, 'vip': 0},
            'rental_stats': {'total': 0, 'active': 0, 'completed': 0, 'cancelled': 0},
            'revenue_stats': {'total': 0, 'monthly': 0, 'today': 0},
            'recent_rentals': [],
            'vehicle_status': [],
            'error': str(e),
        }
        return render(request, 'dashboard.html', context)


def _require_staff(user):
    return user.is_authenticated and user.is_staff


@login_required(login_url='/accounts/login/')
def review_list_view(request):
    """管理员查看评价列表"""
    if not request.user.is_staff:
        messages.error(request, '无权限访问评价管理。')
        return redirect('dashboard')

    query = request.GET.get('q', '').strip()
    rating = request.GET.get('rating', '')

    reviews = Review.objects.select_related('user', 'vehicle', 'rental').order_by('-created_at')

    if query:
        reviews = reviews.filter(
            Q(user__username__icontains=query) |
            Q(vehicle__brand__icontains=query) |
            Q(vehicle__model__icontains=query) |
            Q(rental__id__icontains=query)
        )

    if rating:
        try:
            rating_value = int(rating)
            reviews = reviews.filter(rating=rating_value)
        except ValueError:
            pass

    paginator = Paginator(reviews, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'rating': rating,
        'rating_choices': Review.RATING_CHOICES,
    }
    return render(request, 'reviews/review_list.html', context)


@login_required(login_url='/accounts/login/')
@require_http_methods(["GET", "POST"])
def review_edit_view(request, pk):
    """管理员编辑评价"""
    if not request.user.is_staff:
        messages.error(request, '无权限执行此操作。')
        return redirect('dashboard')

    review = Review.objects.select_related('user', 'vehicle', 'rental').get(pk=pk)

    if request.method == 'POST':
        form = ReviewAdminForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, '评价已更新。')
            return redirect('review_list')
    else:
        form = ReviewAdminForm(instance=review)

    context = {
        'form': form,
        'review': review,
    }
    return render(request, 'reviews/review_edit.html', context)


@login_required(login_url='/accounts/login/')
@require_http_methods(["POST"])
def review_delete_view(request, pk):
    """管理员删除评价"""
    if not request.user.is_staff:
        messages.error(request, '无权限执行此操作。')
        return redirect('dashboard')

    review = Review.objects.get(pk=pk)
    review.delete()
    messages.success(request, '评价已删除。')
    return redirect('review_list')


def home_redirect(request):
    """
    主页重定向到仪表板
    """
    return dashboard(request)


def page_not_found(request, exception):
    """
    404错误页面处理
    """
    return HttpResponseNotFound(render(request, 'page_not_found.html'))


def server_error(request):
    """
    500错误页面处理
    """
    return HttpResponseServerError(render(request, 'server_error.html'))


def permission_denied(request, exception):
    """
    403错误页面处理
    """
    return HttpResponseForbidden(render(request, 'permission_denied.html'))