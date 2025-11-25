from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='description',
            field=models.CharField(
                verbose_name='备注',
                max_length=255,
                blank=True,
                null=True,
                help_text='支付或退款说明'
            ),
        ),
        migrations.AddField(
            model_name='payment',
            name='transaction_type',
            field=models.CharField(
                verbose_name='交易类型',
                max_length=20,
                choices=[
                    ('CHARGE', '支付'),
                    ('REFUND', '退款'),
                ],
                default='CHARGE',
                help_text='区分支付或退款'
            ),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['transaction_type'], name='accounts_pa_transac_8c3869_idx'),
        ),
    ]

