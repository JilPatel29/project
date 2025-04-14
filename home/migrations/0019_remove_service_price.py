"""
# Remove price field from Service model

1. Changes
  - Remove price field from Service model
"""

from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('home', '0018_alter_booking_options_rename_date_payment_created_at_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='service',
            name='price',
        ),
    ]