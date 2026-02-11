from django.core.management.base import BaseCommand

from accounts.models import Role


ROLE_DEFAULTS = [
    {
        "name": Role.SUPERUSER,
        "description": "Full system access. Bypasses all rules.",
        "can_create_users": True,
        "can_manage_projects": True,
        "can_manage_tasks": True,
        "can_move_task_stages": True,
        "can_move_task_categories": True,
        "can_reject_testing": True,
        "can_add_project_notes": True,
        "can_view_assigned_only": False,
        "can_manage_organizations": True,
    },
    {
        "name": Role.COORDINATOR,
        "description": "Manages projects, moves tasks across categories, rejects testing.",
        "can_create_users": True,
        "can_manage_projects": True,
        "can_manage_tasks": True,
        "can_move_task_stages": True,
        "can_move_task_categories": True,
        "can_reject_testing": True,
        "can_add_project_notes": True,
        "can_view_assigned_only": False,
        "can_manage_organizations": False,
    },
    {
        "name": Role.DEVELOPER,
        "description": "Manages own tasks, moves stages via drag-and-drop.",
        "can_create_users": False,
        "can_manage_projects": False,
        "can_manage_tasks": True,
        "can_move_task_stages": True,
        "can_move_task_categories": False,
        "can_reject_testing": False,
        "can_add_project_notes": False,
        "can_view_assigned_only": False,
        "can_manage_organizations": False,
    },
    {
        "name": Role.STAKEHOLDER,
        "description": "View only tasks they are responsible for.",
        "can_create_users": False,
        "can_manage_projects": False,
        "can_manage_tasks": False,
        "can_move_task_stages": False,
        "can_move_task_categories": False,
        "can_reject_testing": False,
        "can_add_project_notes": False,
        "can_view_assigned_only": True,
        "can_manage_organizations": False,
    },
    {
        "name": Role.KEY_STAKEHOLDER,
        "description": "View assigned tasks + add project-level notes.",
        "can_create_users": False,
        "can_manage_projects": False,
        "can_manage_tasks": False,
        "can_move_task_stages": False,
        "can_move_task_categories": False,
        "can_reject_testing": False,
        "can_add_project_notes": True,
        "can_view_assigned_only": True,
        "can_manage_organizations": False,
    },
]


class Command(BaseCommand):
    help = "Seed default roles into the database."

    def handle(self, *args, **options):
        for role_data in ROLE_DEFAULTS:
            role, created = Role.objects.update_or_create(
                name=role_data["name"],
                defaults=role_data,
            )
            status = "Created" if created else "Updated"
            self.stdout.write(f"  {status}: {role.get_name_display()}")

        self.stdout.write(self.style.SUCCESS("Default roles seeded."))
