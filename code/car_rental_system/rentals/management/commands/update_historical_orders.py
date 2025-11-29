from django.core.management.base import BaseCommand
from django.db import transaction
from datetime import date
from decimal import Decimal
from django.utils import timezone
from rentals.models import Rental
from vehicles.models import Vehicle


class Command(BaseCommand):
    help = '批量更新历史订单记录：更新订单状态、退还押金、刷新财务信息'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅预览将要执行的操作，不实际更新数据',
        )
        parser.add_argument(
            '--skip-status',
            action='store_true',
            help='跳过订单状态更新',
        )
        parser.add_argument(
            '--skip-deposit',
            action='store_true',
            help='跳过押金退还',
        )
        parser.add_argument(
            '--skip-financials',
            action='store_true',
            help='跳过财务信息刷新',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        skip_status = options['skip_status']
        skip_deposit = options['skip_deposit']
        skip_financials = options['skip_financials']
        
        today = date.today()
        
        self.stdout.write(self.style.WARNING('\n' + '='*70))
        self.stdout.write(self.style.WARNING('开始批量更新历史订单记录'))
        self.stdout.write(self.style.WARNING('='*70))
        self.stdout.write(f'当前日期: {today}')
        if dry_run:
            self.stdout.write(self.style.WARNING('【预览模式】不会实际修改数据'))
        self.stdout.write('')
        
        total_updates = {
            'status_updates': 0,
            'deposit_refunds': 0,
            'financial_updates': 0,
        }
        
        # ====================
        # 1. 更新订单状态
        # ====================
        if not skip_status:
            self.stdout.write(self.style.WARNING('[1] 更新订单状态'))
            status_updates = self._update_order_status(today, dry_run)
            total_updates['status_updates'] = status_updates
            self.stdout.write('')
        
        # ====================
        # 2. 退还已完成订单的押金
        # ====================
        if not skip_deposit:
            self.stdout.write(self.style.WARNING('[2] 退还已完成订单的押金和已取消订单的已支付金额'))
            deposit_refunds = self._refund_completed_orders_deposits(dry_run)
            cancelled_refunds = self._refund_cancelled_orders_payments(dry_run)
            total_updates['deposit_refunds'] = deposit_refunds + cancelled_refunds
            self.stdout.write('')
        
        # ====================
        # 3. 刷新所有订单的财务信息
        # ====================
        if not skip_financials:
            self.stdout.write(self.style.WARNING('[3] 刷新订单财务信息'))
            financial_updates = self._refresh_all_financials(dry_run)
            total_updates['financial_updates'] = financial_updates
            self.stdout.write('')
        
        # 输出执行摘要
        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write(self.style.SUCCESS('批量更新完成!'))
        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write(self.style.SUCCESS(f'订单状态更新: {total_updates["status_updates"]} 个'))
        self.stdout.write(self.style.SUCCESS(f'退款处理: {total_updates["deposit_refunds"]} 个（包括已完成订单押金和已取消订单已支付金额）'))
        self.stdout.write(self.style.SUCCESS(f'财务信息刷新: {total_updates["financial_updates"]} 个'))
        if dry_run:
            self.stdout.write(self.style.WARNING('\n【预览模式】未实际修改数据，请移除 --dry-run 参数执行实际更新'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
    
    def _update_order_status(self, today, dry_run):
        """更新订单状态：PENDING->ONGOING, ONGOING->OVERDUE"""
        updates_count = 0
        
        # 1. 激活预订中订单（PENDING -> ONGOING）
        pending_rentals = Rental.objects.filter(
            status='PENDING',
            start_date__lte=today
        ).select_related('vehicle')
        
        pending_count = pending_rentals.count()
        if pending_count > 0:
            self.stdout.write(f'  发现 {pending_count} 个需要激活的预订中订单...')
            
            if not dry_run:
                with transaction.atomic():
                    for rental in pending_rentals:
                        rental.status = 'ONGOING'
                        rental.save(update_fields=['status', 'updated_at'])
                        
                        # 更新车辆状态为已租
                        if rental.vehicle.status == 'AVAILABLE':
                            rental.vehicle.status = 'RENTED'
                            rental.vehicle.save(update_fields=['status'])
                        
                        updates_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  ✓ 订单 #{rental.id} ({rental.customer.name}) - 状态更新为"进行中"'
                            )
                        )
            else:
                for rental in pending_rentals:
                    updates_count += 1
                    self.stdout.write(
                        f'  [预览] 订单 #{rental.id} ({rental.customer.name}) - 将更新为"进行中"'
                    )
        
        # 2. 更新过期订单（ONGOING -> OVERDUE）
        overdue_rentals = Rental.objects.filter(
            status='ONGOING',
            end_date__lt=today
        )
        
        overdue_count = overdue_rentals.count()
        if overdue_count > 0:
            self.stdout.write(f'  发现 {overdue_count} 个已过期的进行中订单...')
            
            if not dry_run:
                with transaction.atomic():
                    for rental in overdue_rentals:
                        rental.status = 'OVERDUE'
                        rental.save(update_fields=['status', 'updated_at'])
                        updates_count += 1
                        self.stdout.write(
                            self.style.WARNING(
                                f'  ✓ 订单 #{rental.id} ({rental.customer.name}) - 状态更新为"已超时未归还"'
                            )
                        )
            else:
                for rental in overdue_rentals:
                    updates_count += 1
                    self.stdout.write(
                        f'  [预览] 订单 #{rental.id} ({rental.customer.name}) - 将更新为"已超时未归还"'
                    )
        
        if updates_count == 0:
            self.stdout.write('  没有需要更新的订单状态')
        
        return updates_count
    
    def _refund_completed_orders_deposits(self, dry_run):
        """退还已完成订单的押金"""
        completed_rentals = Rental.objects.filter(
            status='COMPLETED'
        ).select_related('customer')
        
        refunds_count = 0
        
        for rental in completed_rentals:
            deposit_amount = rental.deposit or Decimal('0.00')
            if deposit_amount <= Decimal('0.00'):
                continue
            
            # 尝试退还押金
            if not dry_run:
                refunded, refund_amount = rental.refund_deposit()
                if refunded:
                    refunds_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✓ 订单 #{rental.id} ({rental.customer.name}) - 退还押金 ¥{refund_amount:.2f}'
                        )
                    )
            else:
                # 预览模式：检查是否需要退还
                from accounts.models import Payment
                from django.db.models import Sum
                
                refunded_amount = Payment.objects.filter(
                    rental=rental,
                    transaction_type='REFUND',
                    status='REFUNDED'
                ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
                
                refundable = deposit_amount - refunded_amount
                if refundable > Decimal('0.00'):
                    refunds_count += 1
                    self.stdout.write(
                        f'  [预览] 订单 #{rental.id} ({rental.customer.name}) - 将退还押金 ¥{refundable:.2f}'
                    )
        
        if refunds_count == 0:
            self.stdout.write('  没有需要退还押金的已完成订单')
        
        return refunds_count
    
    def _refund_cancelled_orders_payments(self, dry_run):
        """退还已取消订单的已支付金额"""
        from accounts.models import Payment
        from accounts.views import get_payment_summary
        
        cancelled_rentals = Rental.objects.filter(
            status='CANCELLED'
        ).select_related('customer')
        
        refunds_count = 0
        
        for rental in cancelled_rentals:
            # 获取已支付金额（扣除已退款金额）
            payment_summary = get_payment_summary(rental)
            paid_amount = payment_summary['paid_amount']
            refunded_amount = payment_summary['refunded_amount']
            net_paid = paid_amount - refunded_amount
            
            # 如果有已支付金额且未退还，创建退款记录
            if net_paid <= Decimal('0.00'):
                continue
            
            if not dry_run:
                # 获取退款用户
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
                        payment_method='BANK',
                        transaction_type='REFUND',
                        status='REFUNDED',
                        description=f'订单取消，退还已支付金额 ¥{net_paid:.2f}',
                        paid_at=timezone.now(),
                        transaction_id=f'REF{int(timezone.now().timestamp())}'
                    )
                    
                    # 更新订单财务信息
                    rental.refresh_financials()
                    
                    refunds_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✓ 已取消订单 #{rental.id} ({rental.customer.name}) - 退还已支付金额 ¥{net_paid:.2f}'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  ⚠ 已取消订单 #{rental.id} ({rental.customer.name}) - 未找到退款用户，退款金额：¥{net_paid:.2f}'
                        )
                    )
            else:
                # 预览模式
                refunds_count += 1
                self.stdout.write(
                    f'  [预览] 已取消订单 #{rental.id} ({rental.customer.name}) - 将退还已支付金额 ¥{net_paid:.2f}'
                )
        
        if refunds_count == 0:
            self.stdout.write('  没有需要退款的已取消订单')
        
        return refunds_count
    
    def _refresh_all_financials(self, dry_run):
        """刷新所有订单的财务信息"""
        all_rentals = Rental.objects.all()
        total_count = all_rentals.count()
        
        self.stdout.write(f'  刷新 {total_count} 个订单的财务信息...')
        
        updates_count = 0
        
        for rental in all_rentals:
            if not dry_run:
                rental.refresh_financials()
                updates_count += 1
            else:
                updates_count += 1
        
        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(f'  ✓ 已刷新 {updates_count} 个订单的财务信息')
            )
        else:
            self.stdout.write(f'  [预览] 将刷新 {updates_count} 个订单的财务信息')
        
        return updates_count

