"""
# Add packages ManyToManyField to Booking model

1. Changes
  - Replace single package ForeignKey with ManyToManyField in Booking model
"""

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('home', '0024_handle_existing_users'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='booking',
            name='package',
        ),
        migrations.AddField(
            model_name='booking',
            name='packages',
            field=models.ManyToManyField(to='home.package'),
        ),
    ]