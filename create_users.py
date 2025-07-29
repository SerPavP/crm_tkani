import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_fabrics.settings')
django.setup()

from django.contrib.auth.models import User, Group
from core.models import UserProfile, SystemSettings

# Create SystemSettings if not exists
if not SystemSettings.objects.exists():
    SystemSettings.objects.create()

# Create groups
admin_group, created = Group.objects.get_or_create(name='Admin')
accountant_group, created = Group.objects.get_or_create(name='Accountant')
warehouse_group, created = Group.objects.get_or_create(name='Warehouse')

# Create users and profiles

# Admin
admin_user, created = User.objects.get_or_create(username='admin', email='admin@example.com')
if created:
    admin_user.set_password('admin123')
    admin_user.save()
admin_user.groups.add(admin_group)
UserProfile.objects.get_or_create(user=admin_user, role='admin')

# Accountant
accountant_user, created = User.objects.get_or_create(username='accountant', email='accountant@example.com')
if created:
    accountant_user.set_password('accountant123')
    accountant_user.save()
accountant_user.groups.add(accountant_group)
UserProfile.objects.get_or_create(user=accountant_user, role='accountant')

# Warehouse
warehouse_user, created = User.objects.get_or_create(username='warehouse', email='warehouse123')
if created:
    warehouse_user.set_password('warehouse123')
    warehouse_user.save()
warehouse_user.groups.add(warehouse_group)
UserProfile.objects.get_or_create(user=warehouse_user, role='warehouse')

print('Users and profiles created successfully.')


