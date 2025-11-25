from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Sum
from datetime import date
from decimal import Decimal
from django.utils import timezone
from rentals.models import Rental
from vehicles.models import Vehicle
from accounts.models import Payment


class Command(BaseCommand):
    help = '自动更新租赁订单状态: 预订中→进行中, 进行中→已完成, 并同步车辆状态'

    def handle(self, *args, **options):
        """执行订单和车辆状态的自动更新"""
        today = date.today()
        
        self.stdout.write(self.style.WARNING(f'\n开始执行订单状态自动更新...'))
        self.stdout.write(f'当前日期: {today}\n')
        
        # ====================
        # 阶段1: 激活预订中订单
        # ====================
        self.stdout.write(self.style.WARNING('[阶段1] 激活预订中订单'))
        activated_rentals, activated_vehicles = self._activate_pending_rentals(today)
        
        # ====================
        # 阶段2: 完成过期订单
        # ====================
        self.stdout.write(self.style.WARNING('\n[阶段2] 完成过期订单'))
        completed_rentals, released_vehicles = self._complete_expired_rentals(today)
        
        # 输出执行摘要
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('执行完成!'))
        self.stdout.write(self.style.SUCCESS(f'激活订单数量: {len(activated_rentals)}'))
        self.stdout.write(self.style.SUCCESS(f'激活车辆数量: {len(activated_vehicles)}'))
        self.stdout.write(self.style.SUCCESS(f'完成订单数量: {len(completed_rentals)}'))
        self.stdout.write(self.style.SUCCESS(f'释放车辆数量: {len(released_vehicles)}'))
        self.stdout.write(self.style.SUCCESS('='*60 + '\n'))
    
    def _activate_pending_rentals(self, today):
        """激活预订中的订单(预订中 → 进行中)"""
        # 查询所有待激活的"预订中"订单
        pending_rentals = Rental.objects.filter(
            status='PENDING',
            start_date__lte=today
        ).select_related('vehicle')
        
        pending_count = pending_rentals.count()
        
        if pending_count == 0:
            self.stdout.write(self.style.SUCCESS('未发现待激活的预订中订单'))
            return [], []
        
        self.stdout.write(f'发现 {pending_count} 个待激活订单')
        
        # 收集更新记录
        activated_rentals = []
        activated_vehicles = []
        
        # 更新订单状态和车辆状态
        with transaction.atomic():
            for rental in pending_rentals:
                # 更新订单状态为"进行中"
                rental.status = 'ONGOING'
                rental.save()
                activated_rentals.append(rental)
                
                self.stdout.write(
                    f'  - 订单 #{rental.id}: {rental.customer.name} - '
                    f'{rental.vehicle.license_plate} '
                    f'({rental.start_date} ~ {rental.end_date})'
                )
                
                # 更新车辆状态为"已租"
                if rental.vehicle.status == 'AVAILABLE':
                    rental.vehicle.status = 'RENTED'
                    rental.vehicle.save()
                    activated_vehicles.append(rental.vehicle)
                    self.stdout.write(
                        f'    → 车辆 {rental.vehicle.license_plate} 状态已更新为"已租"'
                    )
        
        self.stdout.write(self.style.SUCCESS(
            f'\n✓ 已成功激活 {len(activated_rentals)} 个订单, 更新 {len(activated_vehicles)} 个车辆状态'
        ))
        
        return activated_rentals, activated_vehicles
    
    def _complete_expired_rentals(self, today):
        """完成过期订单(进行中 → 已完成)"""
        # 查询所有过期的"进行中"订单
        expired_rentals = Rental.objects.filter(
            status='ONGOING',
            end_date__lt=today
        ).select_related('vehicle')
        
        expired_count = expired_rentals.count()
        
        if expired_count == 0:
            self.stdout.write(self.style.SUCCESS('未发现过期的进行中订单'))
            return [], []
        
        self.stdout.write(f'发现 {expired_count} 个过期订单')
        
        # 收集涉及的车辆ID
        vehicle_ids = set()
        completed_rentals = []
        
        # 更新订单状态
        with transaction.atomic():
            for rental in expired_rentals:
                rental.status = 'COMPLETED'
                if not rental.actual_return_date:
                    rental.actual_return_date = rental.end_date
                rental.save()
                vehicle_ids.add(rental.vehicle.id)
                completed_rentals.append(rental)
                
                self.stdout.write(
                    f'  - 订单 #{rental.id}: {rental.customer.name} - '
                    f'{rental.vehicle.license_plate} '
                    f'({rental.start_date} ~ {rental.end_date})'
                )
                
                self._settle_completed_rental(rental)
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ 已成功完成 {len(completed_rentals)} 个订单'))
        
        # 更新车辆状态
        self.stdout.write(self.style.WARNING(f'\n更新车辆状态...'))
        released_vehicles = []
        
        for vehicle_id in vehicle_ids:
            # 检查该车辆是否还有其他"进行中"的订单
            ongoing_rentals = Rental.objects.filter(
                vehicle_id=vehicle_id,
                status='ONGOING'
            ).count()
            
            if ongoing_rentals == 0:
                # 没有进行中的订单,可以将车辆状态改为"可用"
                vehicle = Vehicle.objects.get(id=vehicle_id)
                if vehicle.status == 'RENTED':
                    vehicle.status = 'AVAILABLE'
                    vehicle.save()
                    released_vehicles.append(vehicle)
                    self.stdout.write(
                        f'  - 车辆 {vehicle.license_plate} '
                        f'({vehicle.brand} {vehicle.model}) 已更新为"可用"'
                    )
            else:
                vehicle = Vehicle.objects.get(id=vehicle_id)
                self.stdout.write(
                    f'  - 车辆 {vehicle.license_plate} 仍有 {ongoing_rentals} '
                    f'个进行中订单,保持"已租"状态'
                )
        
        if released_vehicles:
            self.stdout.write(self.style.SUCCESS(
                f'\n✓ 已成功更新 {len(released_vehicles)} 个车辆状态为"可用"'
            ))
        else:
            self.stdout.write(self.style.WARNING('\n所有车辆仍有进行中订单,未更新车辆状态'))
        
        return completed_rentals, released_vehicles

    def _settle_completed_rental(self, rental):
        """订单完成后自动结算押金/更新财务数据"""
        deposit_amount = rental.deposit or Decimal('0.00')
        charges = rental.payments.filter(
            transaction_type='CHARGE',
            status='PAID'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        refunded = rental.payments.filter(
            transaction_type='REFUND',
            status='REFUNDED'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        refundable = deposit_amount - refunded
        
        # 只有在押金已支付且未退还时才自动退款
        if deposit_amount > Decimal('0.00') and refundable > Decimal('0.00') and charges >= deposit_amount:
            payment_user = rental.payments.filter(
                transaction_type='CHARGE'
            ).order_by('created_at').first()
            refund_user = payment_user.user if payment_user else None
            if not refund_user and rental.customer and rental.customer.user:
                refund_user = rental.customer.user
            
            if refund_user:
                Payment.objects.create(
                    rental=rental,
                    user=refund_user,
                    amount=refundable,
                    payment_method='BANK',
                    transaction_type='REFUND',
                    status='REFUNDED',
                    description='订单完成，押金自动退还',
                    paid_at=timezone.now(),
                    transaction_id=f'REF{int(timezone.now().timestamp())}'
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'    → 自动退还押金 ¥{refundable:.2f} 给 {refund_user.username}'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'    → 订单 #{rental.id} 未找到可用的账号用于生成退款记录，跳过退押金'
                    )
                )
        
        rental.refresh_financials()
