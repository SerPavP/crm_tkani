#!/usr/bin/env python
"""
Script to automate migration from SQLite to PostgreSQL for the CRM Tkani project.
"""
import os
import sys
import subprocess
import json
import time
import argparse
from pathlib import Path

def run_command(command, description=None):
    """Run a shell command and print output."""
    if description:
        print(f"\n{description}...")
    print(f"Running: {command}")
    try:
        result = subprocess.run(command, shell=True, check=True, text=True, 
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(result.stdout)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error output: {e.stderr}")
        return False, e.stderr

def create_env_file(db_name, db_user, db_password, db_host, db_port):
    """Create .env file from template."""
    print("\nCreating .env file...")
    
    try:
        # Read the template
        with open('env_template.txt', 'r', encoding='utf-8') as f:
            env_content = f.read()
        
        # Replace database settings
        env_content = env_content.replace('DB_NAME=crm_tkani', f'DB_NAME={db_name}')
        env_content = env_content.replace('DB_USER=postgres', f'DB_USER={db_user}')
        env_content = env_content.replace('DB_PASSWORD=your_password', f'DB_PASSWORD={db_password}')
        env_content = env_content.replace('DB_HOST=localhost', f'DB_HOST={db_host}')
        env_content = env_content.replace('DB_PORT=5432', f'DB_PORT={db_port}')
        
        # Write the .env file
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print("Created .env file with PostgreSQL settings.")
        return True
    except FileNotFoundError:
        print("Error: env_template.txt not found. Make sure you're running this script from the project root directory.")
        return False
    except Exception as e:
        print(f"Error creating .env file: {e}")
        return False

def export_sqlite_data():
    """Export data from SQLite to JSON."""
    print("\nExporting data from SQLite...")
    
    # Create a backup directory if it doesn't exist
    backup_dir = Path('db_backup')
    backup_dir.mkdir(exist_ok=True)
    
    # Generate a timestamp for the backup file
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    backup_file = backup_dir / f'db_dump_{timestamp}.json'
    
    # Export data excluding permissions and contenttypes
    success, _ = run_command(
        f'python manage.py dumpdata --exclude auth.permission --exclude contenttypes > {backup_file}',
        'Exporting data from SQLite'
    )
    
    if success:
        print(f"Data exported to {backup_file}")
        return str(backup_file)
    else:
        print("Failed to export data.")
        return None

def apply_migrations():
    """Apply migrations to PostgreSQL."""
    return run_command('python manage.py migrate', 'Applying migrations to PostgreSQL')

def import_data(backup_file):
    """Import data to PostgreSQL."""
    return run_command(f'python manage.py loaddata {backup_file}', 'Importing data to PostgreSQL')

def reset_sequences(db_name, db_user, db_password, db_host, db_port):
    """Reset sequences in PostgreSQL."""
    print("\nResetting sequences in PostgreSQL...")
    
    # Get list of all tables
    success, output = run_command(
        "python manage.py shell -c \"from django.apps import apps; "
        "print(','.join([model._meta.db_table for model in apps.get_models() "
        "if not model._meta.abstract and model._meta.managed]))\"",
        "Getting list of tables"
    )
    
    if not success:
        print("Failed to get list of tables.")
        return False
    
    tables = output.strip().split(',')
    
    # Create a SQL script to reset sequences
    sql_script = "reset_sequences.sql"
    with open(sql_script, 'w') as f:
        for table in tables:
            f.write(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
                   f"coalesce(max(id), 1), max(id) IS NOT null) FROM {table};\n")
    
    # Set PGPASSWORD environment variable for psql
    os.environ['PGPASSWORD'] = db_password
    
    # Run the SQL script using psql
    success, _ = run_command(
        f'psql -h {db_host} -p {db_port} -U {db_user} -d {db_name} -f {sql_script}',
        'Resetting sequences'
    )
    
    # Clean up
    os.remove(sql_script)
    # Clear password from environment
    os.environ.pop('PGPASSWORD', None)
    
    return success

def check_psql_installed():
    """Check if psql command is available."""
    try:
        result = subprocess.run(
            'psql --version', 
            shell=True, 
            check=False, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE
        )
        return result.returncode == 0
    except Exception:
        return False

def main():
    """Main function to run the migration process."""
    parser = argparse.ArgumentParser(description='Migrate from SQLite to PostgreSQL')
    parser.add_argument('--db-name', default='crm_tkani', help='PostgreSQL database name')
    parser.add_argument('--db-user', default='postgres', help='PostgreSQL username')
    parser.add_argument('--db-password', required=True, help='PostgreSQL password')
    parser.add_argument('--db-host', default='localhost', help='PostgreSQL host')
    parser.add_argument('--db-port', default='5432', help='PostgreSQL port')
    parser.add_argument('--skip-export', action='store_true', help='Skip exporting data from SQLite')
    parser.add_argument('--backup-file', help='Use existing backup file instead of creating a new one')
    
    args = parser.parse_args()
    
    # Check if psql is installed
    if not check_psql_installed():
        print("Error: psql command not found. Please install PostgreSQL client tools.")
        return 1
    
    # Create .env file
    if not create_env_file(args.db_name, args.db_user, args.db_password, args.db_host, args.db_port):
        print("Failed to create .env file. Aborting migration.")
        return 1
    
    # Export data from SQLite
    backup_file = None
    if not args.skip_export:
        backup_file = export_sqlite_data()
        if not backup_file:
            print("Failed to export data. Aborting migration.")
            return 1
    elif args.backup_file:
        backup_file = args.backup_file
        if not os.path.exists(backup_file):
            print(f"Backup file {backup_file} does not exist. Aborting migration.")
            return 1
    else:
        print("Either provide a backup file or don't skip export. Aborting migration.")
        return 1
    
    # Apply migrations to PostgreSQL
    success, _ = apply_migrations()
    if not success:
        print("Failed to apply migrations. Aborting migration.")
        return 1
    
    # Import data to PostgreSQL
    success, _ = import_data(backup_file)
    if not success:
        print("Failed to import data. Aborting migration.")
        return 1
    
    # Reset sequences
    success = reset_sequences(args.db_name, args.db_user, args.db_password, args.db_host, args.db_port)
    if not success:
        print("Failed to reset sequences. The migration may not be complete.")
        return 1
    
    print("\nMigration completed successfully!")
    return 0

if __name__ == '__main__':
    sys.exit(main())
