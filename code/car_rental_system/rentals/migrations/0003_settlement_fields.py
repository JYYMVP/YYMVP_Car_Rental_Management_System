from django.db import migrations, models
from decimal import Decimal
from django.db.models import Sum


def populate_financial_fields(apps, schema_editor):
    Rental = apps.get_model('rentals', 'Rental')
    Payment = apps.get_model('accounts', 'Payment')
    
    for rental in Rental.objects.all():
        paid_total = Payment.objects.filter(
            rental_id=rental.id,
            status='PAID',
            transaction_type='CHARGE'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        refunded_total = Payment.objects.filter(
            rental_id=rental.id,
            status='REFUNDED',
            transaction_type='REFUND'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        settlement_status = 'UNSETTLED'
        if paid_total > Decimal('0.00'):
            settlement_status = 'PARTIAL'
        order_total = (rental.total_amount or Decimal('0.00')) + (rental.deposit or Decimal('0.00'))
        if rental.is_cross_location_return:
            order_total += rental.cross_location_fee or Decimal('0.00')
        if rental.status == 'COMPLETED' and order_total <= paid_total:
            settlement_status = 'SETTLED'
        
        Rental.objects.filter(pk=rental.pk).update(
            amount_paid=paid_total,
            amount_refunded=refunded_total,
            settlement_status=settlement_status
        )


class Migration(migrations.Migration):

    dependencies = [
        ('rentals', '0002_add_deposit_and_location_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='rental',
            name='amount_paid',
            field=models.DecimalField(
                verbose_name='累计支付金额',
                default=Decimal('0.00'),
                max_digits=10,
                decimal_places=2,
                help_text='用户累计支付金额（不含退款）'
            ),
        ),
        migrations.AddField(
            model_name='rental',
            name='amount_refunded',
            field=models.DecimalField(
                verbose_name='累计退款金额',
                default=Decimal('0.00'),
                max_digits=10,
                decimal_places=2,
                help_text='系统累计退款金额'
            ),
        ),
        migrations.AddField(
            model_name='rental',
            name='settled_at',
            field=models.DateTimeField(
                verbose_name='结算时间',
                blank=True,
                null=True,
                help_text='订单完成并结算的时间'
            ),
        ),
        migrations.AddField(
            model_name='rental',
            name='settlement_status',
            field=models.CharField(
                verbose_name='结算状态',
                default='UNSETTLED',
                max_length=20,
                choices=[
                    ('UNSETTLED', '未结算'),
                    ('PARTIAL', '部分结算'),
                    ('SETTLED', '已结算'),
                ],
                help_text='订单费用结算状态'
            ),
        ),
        migrations.RunPython(populate_financial_fields, migrations.RunPython.noop),
    ]

