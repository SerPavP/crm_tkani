from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import UserProfile
from clients.models import Client
from fabrics.models import Fabric, FabricColor, FabricRoll
from deals.models import Deal, DealItem
import random
from faker import Faker

class Command(BaseCommand):
    help = 'Generates sample data for the CRM system.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting data seeding...'))
        fake = Faker("ru_RU")

        # 1. Create Users and UserProfiles
        self.stdout.write('Creating users and user profiles...')
        users_data = [
            {'username': 'admin', 'password': 'admin123', 'email': 'admin@example.com', 'role': 'admin'},
            {'username': 'manager', 'password': 'manager123', 'email': 'manager@example.com', 'role': 'manager'},
            {'username': 'accountant', 'password': 'accountant123', 'email': 'accountant@example.com', 'role': 'accountant'},
            {'username': 'warehouse', 'password': 'warehouse123', 'email': 'warehouse@example.com', 'role': 'warehouse'},
        ]

        for user_data in users_data:
            user, created = User.objects.get_or_create(username=user_data['username'], defaults={'email': user_data['email']})
            if created:
                user.set_password(user_data['password'])
                user.save()
                UserProfile.objects.create(user=user, role=user_data['role'])
                self.stdout.write(f'  Created user: {user.username} ({user_data["role"]})')
            else:
                self.stdout.write(f'  User already exists: {user.username}')

        # 2. Create Clients
        self.stdout.write('Creating clients...')
        clients = []
        for _ in range(20):
            client = Client.objects.create(
                nickname=fake.company(),
                full_name=fake.name(),
                phone=fake.phone_number(),
                email=fake.email(),
                address=fake.address(),
                notes=fake.text(max_nb_chars=100)
            )
            clients.append(client)
            self.stdout.write(f'  Created client: {client.nickname}')

        # 3. Create Fabrics and FabricColors
        self.stdout.write('Creating fabrics and fabric colors...')
        fabrics = []
        fabric_names = ['Шелк', 'Хлопок', 'Лен', 'Вискоза', 'Полиэстер', 'Шерсть', 'Атлас', 'Бархат']
        for name in fabric_names:
            fabric = Fabric.objects.create(
                name=name,
                description=fake.text(max_nb_chars=100),
                cost_price=round(random.uniform(100, 1000), 2)
            )
            fabrics.append(fabric)
            # Create 3-5 colors for each fabric
            for _ in range(random.randint(3, 5)):
                FabricColor.objects.create(
                    fabric=fabric,
                    color_name=fake.color_name(),
                    color_hex=fake.hex_color(),
                    price_per_meter=round(random.uniform(500, 5000), 2),
                    color_number=fake.unique.random_int(min=100, max=999)
                )
            self.stdout.write(f'  Created fabric: {fabric.name} with colors')
        fabric_colors = list(FabricColor.objects.all())

        # 4. Create FabricRolls
        self.stdout.write('Creating fabric rolls...')
        for _ in range(50):
            fabric_color = random.choice(fabric_colors)
            FabricRoll.objects.create(
                fabric_color=fabric_color,
                width_meters=round(random.uniform(10, 100), 2),
                barcode=fake.unique.ean13()
            )
        self.stdout.write('  Created 50 fabric rolls.')

        # 5. Create Deals and DealItems
        self.stdout.write('Creating deals and deal items...')
        for _ in range(15):
            client = random.choice(clients)
            deal = Deal.objects.create(
                client=client,
                deal_number=fake.unique.bothify(text='DEAL-####'),
                status=random.choice([choice[0] for choice in Deal.STATUS_CHOICES])
            )
            
            num_items = random.randint(1, 5)
            total_amount = 0
            for _ in range(num_items):
                fabric_color = random.choice(fabric_colors)
                meters = round(random.uniform(5, 30), 2)
                price_per_meter = fabric_color.price_per_meter
                item_total = Decimal(str(meters)) * price_per_meter
                DealItem.objects.create(
                    deal=deal,
                    fabric_color=fabric_color,
                    width_meters=meters,
                    price_per_meter=price_per_meter,
                    total_price=item_total
                )
                total_amount += item_total
            
            deal.total_amount = total_amount
            deal.total_with_vat = total_amount * Decimal('1.12')  # Assuming 12% VAT
            deal.save()
            self.stdout.write(f'  Created deal: {deal.deal_number} with {num_items} items')

        self.stdout.write(self.style.SUCCESS('Data seeding completed successfully!'))


