import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import Role
from organizations.models import Organization
from dotenv import load_dotenv

User = get_user_model()

load_dotenv()

class Command(BaseCommand):
    help = 'Create test accounts with different roles from .env variables'

    def handle(self, *args, **options):
        self.stdout.write('Creating test accounts and organization...')
        
        # Create default organization
        default_org, org_created = Organization.objects.get_or_create(
            name='Default Organization',
            defaults={'description': 'Default organization for testing'}
        )
        if org_created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created organization: Default Organization'))
        else:
            self.stdout.write(f'→ Organization "Default Organization" already exists')
        
        # Get System Administrator role
        sys_admin_role, _ = Role.objects.get_or_create(
            name=Role.SYSTEM_ADMINISTRATOR,
            defaults={'description': 'System administrator with full access'}
        )
        
        # Get Administrator role (for organization)
        org_admin_role, _ = Role.objects.get_or_create(
            name=Role.ADMINISTRATOR,
            defaults={'description': 'Organization administrator'}
        )
        
        # Get Coordinator role
        coordinator_role, _ = Role.objects.get_or_create(
            name=Role.COORDINATOR,
            defaults={'description': 'Project coordinator'}
        )
        
        # Get Developer role
        developer_role, _ = Role.objects.get_or_create(
            name=Role.DEVELOPER,
            defaults={'description': 'Regular developer'}
        )
        
        # Create System Admin
        admin_username = os.getenv('ADMIN_USERNAME', 'admin')
        admin_email = os.getenv('ADMIN_EMAIL', 'admin@example.com')
        admin_password = os.getenv('ADMIN_PASSWORD', 'Admin@123456')
        
        admin_user, created = User.objects.get_or_create(
            username=admin_username,
            defaults={
                'email': admin_email,
                'role': sys_admin_role,
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            }
        )
        if created:
            admin_user.set_password(admin_password)
            admin_user.save()
            default_org.members.add(admin_user)
            self.stdout.write(
                self.style.SUCCESS(f'✓ Created System Admin: {admin_username}')
            )
        else:
            self.stdout.write(f'→ System Admin {admin_username} already exists')
        
        # Create Organization Admin
        org_admin_username = os.getenv('ORG_ADMIN_USERNAME', 'orgadmin')
        org_admin_email = os.getenv('ORG_ADMIN_EMAIL', 'orgadmin@example.com')
        org_admin_password = os.getenv('ORG_ADMIN_PASSWORD', 'OrgAdmin@123456')
        
        org_admin_user, created = User.objects.get_or_create(
            username=org_admin_username,
            defaults={
                'email': org_admin_email,
                'role': org_admin_role,
                'admin_organization': default_org,
                'is_active': True,
            }
        )
        if created:
            org_admin_user.set_password(org_admin_password)
            org_admin_user.save()
            default_org.members.add(org_admin_user)
            self.stdout.write(
                self.style.SUCCESS(f'✓ Created Organization Admin: {org_admin_username} (manages: Default Organization)')
            )
        else:
            self.stdout.write(f'→ Organization Admin {org_admin_username} already exists')
        
        # Create Coordinator
        coordinator_username = os.getenv('COORDINATOR_USERNAME', 'coordinator')
        coordinator_email = os.getenv('COORDINATOR_EMAIL', 'coordinator@example.com')
        coordinator_password = os.getenv('COORDINATOR_PASSWORD', 'Coordinator@123456')
        
        coordinator_user, created = User.objects.get_or_create(
            username=coordinator_username,
            defaults={
                'email': coordinator_email,
                'role': coordinator_role,
                'is_active': True,
            }
        )
        if created:
            coordinator_user.set_password(coordinator_password)
            coordinator_user.save()
            default_org.members.add(coordinator_user)
            self.stdout.write(
                self.style.SUCCESS(f'✓ Created Coordinator: {coordinator_username}')
            )
        else:
            self.stdout.write(f'→ Coordinator {coordinator_username} already exists')
        
        # Create Regular User (Developer)
        user_username = os.getenv('USER_USERNAME', 'user')
        user_email = os.getenv('USER_EMAIL', 'user@example.com')
        user_password = os.getenv('USER_PASSWORD', 'User@123456')
        
        regular_user, created = User.objects.get_or_create(
            username=user_username,
            defaults={
                'email': user_email,
                'role': developer_role,
                'is_active': True,
            }
        )
        if created:
            regular_user.set_password(user_password)
            regular_user.save()
            default_org.members.add(regular_user)
            self.stdout.write(
                self.style.SUCCESS(f'✓ Created Developer: {user_username}')
            )
        else:
            self.stdout.write(f'→ Developer {user_username} already exists')
        
        self.stdout.write(self.style.SUCCESS('\n✓ Test accounts setup complete!'))
        self.stdout.write(
            '\nTest credentials:\n'
            f'  System Admin: {admin_username} / {admin_password}\n'
            f'  Org Admin: {org_admin_username} / {org_admin_password} (manages "Default Organization")\n'
            f'  Coordinator: {coordinator_username} / {coordinator_password}\n'
            f'  Developer: {user_username} / {user_password}\n'
        )
