import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Creates an admin user from environment variables'

    def handle(self, *args, **options):
        from accounts.models import Role
        
        username = os.environ.get('ADMIN_USERNAME', 'admin')
        email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
        password = os.environ.get('ADMIN_PASSWORD', 'admin')

        # Create or get System Administrator role
        system_admin_role, created = Role.objects.get_or_create(
            name=Role.SYSTEM_ADMINISTRATOR,
            defaults={
                'description': 'Full system access with all permissions',
                'can_create_users': True,
                'can_manage_projects': True,
                'can_manage_tasks': True,
                'can_move_task_stages': True,
                'can_move_task_categories': True,
                'can_reject_testing': True,
                'can_add_project_notes': True,
                'can_view_assigned_only': False,
                'can_manage_organizations': True,
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS('Created System Administrator role')
            )

        # Create all other roles
        roles_config = [
            {
                'name': Role.ADMINISTRATOR,
                'description': 'Organization administrator',
                'permissions': {
                    'can_create_users': True,
                    'can_manage_projects': True,
                    'can_manage_tasks': True,
                    'can_move_task_stages': True,
                    'can_move_task_categories': True,
                    'can_reject_testing': True,
                    'can_add_project_notes': True,
                    'can_view_assigned_only': False,
                    'can_manage_organizations': False,
                }
            },
            {
                'name': Role.COORDINATOR,
                'description': 'Project coordinator',
                'permissions': {
                    'can_create_users': False,
                    'can_manage_projects': True,
                    'can_manage_tasks': True,
                    'can_move_task_stages': True,
                    'can_move_task_categories': True,
                    'can_reject_testing': True,
                    'can_add_project_notes': True,
                    'can_view_assigned_only': False,
                    'can_manage_organizations': False,
                }
            },
            {
                'name': Role.DEVELOPER,
                'description': 'Developer',
                'permissions': {
                    'can_create_users': False,
                    'can_manage_projects': False,
                    'can_manage_tasks': False,
                    'can_move_task_stages': True,
                    'can_move_task_categories': True,
                    'can_reject_testing': False,
                    'can_add_project_notes': True,
                    'can_view_assigned_only': True,
                    'can_manage_organizations': False,
                }
            },
        ]

        for role_config in roles_config:
            role, created = Role.objects.get_or_create(
                name=role_config['name'],
                defaults={
                    'description': role_config['description'],
                    **role_config['permissions']
                }
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created {role.get_name_display()} role')
                )

        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            if user.role != system_admin_role:
                user.role = system_admin_role
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Updated user "{username}" with System Administrator role')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Admin user "{username}" already exists with System Administrator role')
                )
            return

        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        user.role = system_admin_role
        user.save()
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created admin user "{username}" with System Administrator role')
        )
