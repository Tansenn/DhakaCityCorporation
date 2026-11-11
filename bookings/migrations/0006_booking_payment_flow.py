from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('bookings', '0005_booking_national_id_booking_office_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='payment_flow',
            field=models.CharField(
                choices=[('approval_first', 'Approval first'), ('direct', 'Direct payment')],
                default='approval_first',
                max_length=20,
            ),
        ),
    ]
