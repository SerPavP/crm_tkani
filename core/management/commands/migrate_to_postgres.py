"""
Django management command to migrate data from SQLite to PostgreSQL.
"""
import os
import sys
import json
import time
import subprocess
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import connections
from django.core.management import call_command
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


class Command(BaseCommand):
    help = 'Migrate data from SQLite to PostgreSQL'

    def add_arguments(self, parser):
        parser.add_argument(
            '--db-name',
            type=str,
            default='crm_tkani',
            help='PostgreSQL database name (default: crm_tkani)'
        )
        parser.add_argument(
            '--db-user',
            type=str,
            default='postgres',
            help='PostgreSQL username (default: postgres)'
        )
        parser.add_argument(
            '--db-password',
            type=str,
            required=True,
            help='PostgreSQL password'
        )
        parser.add_argument(
            '--db-host',
            type=str,
            default='localhost',
            help='PostgreSQL host (default: localhost)'
        )
        parser.add_argument(
            '--db-port',
            type=str,
            default='5432',
            help='PostgreSQL port (default: 5432)'
        )
        parser.add_argument(
            '--skip-export',
            action='store_true',
            help='Skip exporting data from SQLite'
        )
        parser.add_argument(
            '--backup-file',
            type=str,
            help='Use existing backup file instead of creating a new one'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force migration even if PostgreSQL database exists'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Starting migration from SQLite to PostgreSQL...')
        )

        # Get database settings
        db_name = options['db_name']
        db_user = options['db_user']
        db_password = options['db_password']
        db_host = options['db_host']
        db_port = options['db_port']

        try:
            # Step 1: Check PostgreSQL connection
            self.check_postgres_connection(db_name, db_user, db_password, db_host, db_port)

            # Step 2: Create database if it doesn't exist
            self.create_database_if_not_exists(db_name, db_user, db_password, db_host, db_port)

            # Step 3: Update Django settings to use PostgreSQL
            self.update_django_settings(db_name, db_user, db_password, db_host, db_port)

            # Step 4: Export data from SQLite
            backup_file = None
            if not options['skip_export']:
                backup_file = self.export_sqlite_data()
            elif options['backup_file']:
                backup_file = options['backup_file']
                if not os.path.exists(backup_file):
                    raise CommandError(f'Backup file {backup_file} does not exist.')
            else:
                raise CommandError('Either provide a backup file or don\'t skip export.')

            # Step 5: Apply migrations to PostgreSQL
            self.apply_migrations()

            # Step 6: Import data to PostgreSQL
            self.import_data(backup_file)

            # Step 7: Reset sequences
            self.reset_sequences(db_name, db_user, db_password, db_host, db_port)

            # Step 8: Verify migration
            self.verify_migration()

            self.stdout.write(
                self.style.SUCCESS('✅ Migration completed successfully!')
            )
            self.stdout.write(
                self.style.WARNING('📝 Don\'t forget to update your .env file with PostgreSQL settings.')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Migration failed: {str(e)}')
            )
            raise CommandError(f'Migration failed: {str(e)}')

    def check_postgres_connection(self, db_name, db_user, db_password, db_host, db_port):
        """Check if PostgreSQL connection is available."""
        self.stdout.write('🔍 Checking PostgreSQL connection...')
        
        try:
            # Try to connect to PostgreSQL server (without specific database)
            conn = psycopg2.connect(
                host=db_host,
                port=db_port,
                user=db_user,
                password=db_password,
                database='postgres'  # Connect to default postgres database
            )
            conn.close()
            self.stdout.write(self.style.SUCCESS('✅ PostgreSQL connection successful'))
        except psycopg2.Error as e:
            raise CommandError(f'Cannot connect to PostgreSQL: {e}')

    def create_database_if_not_exists(self, db_name, db_user, db_password, db_host, db_port):
        """Create PostgreSQL database if it doesn't exist."""
        self.stdout.write(f'🗄️  Creating database {db_name} if it doesn\'t exist...')
        
        try:
            # Connect to PostgreSQL server
            conn = psycopg2.connect(
                host=db_host,
                port=db_port,
                user=db_user,
                password=db_password,
                database='postgres'
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()

            # Check if database exists
            cursor.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (db_name,)
            )
            
            if cursor.fetchone():
                self.stdout.write(self.style.WARNING(f'⚠️  Database {db_name} already exists'))
            else:
                # Create database
                cursor.execute(f'CREATE DATABASE "{db_name}"')
                self.stdout.write(self.style.SUCCESS(f'✅ Database {db_name} created'))

            cursor.close()
            conn.close()

        except psycopg2.Error as e:
            raise CommandError(f'Error creating database: {e}')

    def update_django_settings(self, db_name, db_user, db_password, db_host, db_port):
        """Update Django settings to use PostgreSQL."""
        self.stdout.write('⚙️  Updating Django settings for PostgreSQL...')
        
        # Create .env file
        env_content = f"""DEBUG=False
SECRET_KEY={getattr(settings, 'SECRET_KEY', 'your-secret-key-here')}
ALLOWED_HOSTS=localhost,127.0.0.1

# PostgreSQL Database
DB_NAME={db_name}
DB_USER={db_user}
DB_PASSWORD={db_password}
DB_HOST={db_host}
DB_PORT={db_port}
"""
        
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        self.stdout.write(self.style.SUCCESS('✅ .env file created with PostgreSQL settings'))

    def export_sqlite_data(self):
        """Export data from SQLite to JSON."""
        self.stdout.write('📤 Exporting data from SQLite...')
        
        # Create backup directory
        backup_dir = Path('db_backup')
        backup_dir.mkdir(exist_ok=True)
        
        # Generate timestamp for backup file
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        backup_file = backup_dir / f'db_dump_{timestamp}.json'
        
        try:
            # Export data excluding permissions and contenttypes
            call_command(
                'dumpdata',
                exclude=['auth.permission', 'contenttypes'],
                output=str(backup_file),
                verbosity=0
            )
            
            self.stdout.write(self.style.SUCCESS(f'✅ Data exported to {backup_file}'))
            return str(backup_file)
            
        except Exception as e:
            raise CommandError(f'Failed to export data: {e}')

    def apply_migrations(self):
        """Apply migrations to PostgreSQL."""
        self.stdout.write('🔄 Applying migrations to PostgreSQL...')
        
        try:
            call_command('migrate', verbosity=0)
            self.stdout.write(self.style.SUCCESS('✅ Migrations applied successfully'))
        except Exception as e:
            raise CommandError(f'Failed to apply migrations: {e}')

    def import_data(self, backup_file):
        """Import data to PostgreSQL."""
        self.stdout.write(f'📥 Importing data from {backup_file}...')
        
        try:
            call_command('loaddata', backup_file, verbosity=0)
            self.stdout.write(self.style.SUCCESS('✅ Data imported successfully'))
        except Exception as e:
            raise CommandError(f'Failed to import data: {e}')

    def reset_sequences(self, db_name, db_user, db_password, db_host, db_port):
        """Reset sequences in PostgreSQL."""
        self.stdout.write('🔄 Resetting sequences in PostgreSQL...')
        
        try:
            # Connect to PostgreSQL
            conn = psycopg2.connect(
                host=db_host,
                port=db_port,
                user=db_user,
                password=db_password,
                database=db_name
            )
            cursor = conn.cursor()

            # Get all tables with auto-increment fields
            cursor.execute("""
                SELECT table_name, column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND column_default LIKE 'nextval%'
            """)
            
            sequences = cursor.fetchall()
            
            for table_name, column_name in sequences:
                cursor.execute(f"""
                    SELECT setval(pg_get_serial_sequence('{table_name}', '{column_name}'), 
                    coalesce(max({column_name}), 1), max({column_name}) IS NOT null) 
                    FROM {table_name}
                """)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            self.stdout.write(self.style.SUCCESS('✅ Sequences reset successfully'))
            
        except psycopg2.Error as e:
            raise CommandError(f'Failed to reset sequences: {e}')

    def verify_migration(self):
        """Verify that migration was successful."""
        self.stdout.write('🔍 Verifying migration...')
        
        try:
            # Check if we can connect to PostgreSQL
            db_config = connections['default']
            with db_config.cursor() as cursor:
                # Count records in main tables
                cursor.execute("SELECT COUNT(*) FROM clients_client")
                clients_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM deals_deal")
                deals_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM fabrics_fabric")
                fabrics_count = cursor.fetchone()[0]
            
            self.stdout.write(self.style.SUCCESS('✅ Migration verification successful'))
            self.stdout.write(f'📊 Migrated data:')
            self.stdout.write(f'   - Clients: {clients_count}')
            self.stdout.write(f'   - Deals: {deals_count}')
            self.stdout.write(f'   - Fabrics: {fabrics_count}')
            
        except Exception as e:
            raise CommandError(f'Migration verification failed: {e}')
