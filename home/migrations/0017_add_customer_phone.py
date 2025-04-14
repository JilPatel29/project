"""
# Add customer phone field to Booking model

1. Changes
  - Add customer_phone field to Booking model
"""

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('home', '0016_alter_customuser_email'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='customer_phone',
            field=models.CharField(max_length=15, default=''),
            preserve_default=False,
        ),
    ]