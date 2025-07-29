from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from core.models import UserProfile, SystemSettings

class Command(BaseCommand):
    help = 'Создаёт тестовых пользователей и системные группы'

    def handle(self, *args, **kwargs):
        if not SystemSettings.objects.exists():
            SystemSettings.objects.create()
        admin_group, _ = Group.objects.get_or_create(name='Admin')
        accountant_group, _ = Group.objects.get_or_create(name='Accountant')
        warehouse_group, _ = Group.objects.get_or_create(name='Warehouse')

        admin_user, created = User.objects.get_or_create(username='admin', email='admin@example.com')
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
        admin_user.groups.add(admin_group)
        UserProfile.objects.get_or_create(user=admin_user, role='admin')

        accountant_user, created = User.objects.get_or_create(username='accountant', email='accountant@example.com')
        if created:
            accountant_user.set_password('accountant123')
            accountant_user.save()
        accountant_user.groups.add(accountant_group)
        UserProfile.objects.get_or_create(user=accountant_user, role='accountant')

        warehouse_user, created = User.objects.get_or_create(username='warehouse', email='warehouse123')
        if created:
            warehouse_user.set_password('warehouse123')
            warehouse_user.save()
        warehouse_user.groups.add(warehouse_group)
        UserProfile.objects.get_or_create(user=warehouse_user, role='warehouse')

        self.stdout.write(self.style.SUCCESS('Users and profiles created successfully.'))
