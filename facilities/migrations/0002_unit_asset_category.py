from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('facilities', '0001_initial')]
    operations = [
        migrations.AddField(
            model_name='unit', name='asset_category',
            field=models.CharField(default='dakbungalow', max_length=20, choices=[
                ('land', 'Lands'), ('ponds', 'Ponds'), ('markets', 'Markets'),
                ('kheyaghat', 'Kheyaghat'), ('auditorium', 'Auditorium'),
                ('dakbungalow', 'Dakbungalows'),
            ]),
        ),
        migrations.AlterField(
            model_name='unit', name='kind',
            field=models.CharField(default='room', max_length=10, choices=[
                ('room', 'Room'), ('suite', 'VIP suite'), ('hall', 'Conference hall'),
                ('asset', 'Daily reservation'),
            ]),
        ),
    ]
