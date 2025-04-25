"""
# Handle existing users and CustomUser relationships

1. Changes
  - Creates CustomUser instances for existing users if they don't exist
  - Ensures unique constraints are respected
"""

from django.db import migrations
from django.contrib.auth.hashers import make_password
import uuid

def handle_existing_users(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    CustomUser = apps.get_model('home', 'CustomUser')
    
    for user in User.objects.all():
        # Check if CustomUser exists with this username
        if CustomUser.objects.filter(username=user.username).exists():
            # Generate a unique username by appending a UUID
            new_username = f"{user.username}_{str(uuid.uuid4())[:8]}"
            CustomUser.objects.create(
                username=new_username,
                email=user.email,
                password=user.password,
                is_active=True,
                is_staff=user.is_staff,
                is_superuser=user.is_superuser,
                date_joined=user.date_joined,
                last_login=user.last_login
            )
        else:
            CustomUser.objects.create(
                username=user.username,
                email=user.email,
                password=user.password,
                is_active=True,
                is_staff=user.is_staff,
                is_superuser=user.is_superuser,
                date_joined=user.date_joined,
                last_login=user.last_login
            )

def reverse_migrate(apps, schema_editor):
    CustomUser = apps.get_model('home', 'CustomUser')
    CustomUser.objects.all().delete()

class Migration(migrations.Migration):

    dependencies = [
        ('home', '0023_remove_gallery_title'),
    ]

    operations = [
        migrations.RunPython(handle_existing_users, reverse_migrate),
    ]
