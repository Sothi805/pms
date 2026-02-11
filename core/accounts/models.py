import secrets
import string

from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.Model):
    """Default permission bundle. Permissions override roles."""

    SYSTEM_ADMINISTRATOR = "system_administrator"
    ADMINISTRATOR = "administrator"
    COORDINATOR = "coordinator"
    DEVELOPER = "developer"

    ROLE_CHOICES = [
        (SYSTEM_ADMINISTRATOR, "System Administrator"),
        (ADMINISTRATOR, "Administrator"),
        (COORDINATOR, "Coordinator"),
        (DEVELOPER, "Developer"),
    ]

    name = models.CharField(max_length=30, choices=ROLE_CHOICES, unique=True)
    description = models.TextField(blank=True)

    can_create_users = models.BooleanField(default=False)
    can_manage_projects = models.BooleanField(default=False)
    can_manage_tasks = models.BooleanField(default=False)
    can_move_task_stages = models.BooleanField(default=False)
    can_move_task_categories = models.BooleanField(default=False)
    can_reject_testing = models.BooleanField(default=False)
    can_add_project_notes = models.BooleanField(default=False)
    can_view_assigned_only = models.BooleanField(default=False)
    can_manage_organizations = models.BooleanField(default=False)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.get_name_display()


class User(AbstractUser):
    """Custom user model for PMS."""

    role = models.ForeignKey(
        Role, on_delete=models.SET_NULL, null=True, blank=True, related_name="users"
    )
    admin_organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="administrators",
        help_text="Organization this user administrates (only for Administrator role).",
    )
    is_auto_generated = models.BooleanField(
        default=False,
        help_text="Auto-generated accounts are inactive until password reset.",
    )

    # Per-user permission overrides (override role defaults)
    perm_create_users = models.BooleanField(null=True, blank=True)
    perm_manage_projects = models.BooleanField(null=True, blank=True)
    perm_manage_tasks = models.BooleanField(null=True, blank=True)
    perm_move_task_stages = models.BooleanField(null=True, blank=True)
    perm_move_task_categories = models.BooleanField(null=True, blank=True)
    perm_reject_testing = models.BooleanField(null=True, blank=True)
    perm_add_project_notes = models.BooleanField(null=True, blank=True)
    perm_view_assigned_only = models.BooleanField(null=True, blank=True)
    perm_manage_organizations = models.BooleanField(null=True, blank=True)

    class Meta:
        ordering = ["username"]

    def _resolve(self, perm_field: str, role_field: str) -> bool:
        user_val = getattr(self, perm_field)
        if user_val is not None:
            return user_val
        if self.role:
            return getattr(self.role, role_field, False)
        return False

    def is_system_admin(self):
        """Check if user is a System Administrator (bypasses everything)."""
        return self.role and self.role.name == Role.SYSTEM_ADMINISTRATOR

    def is_org_admin(self, organization=None):
        """Check if user is Administrator for a specific organization.
        
        If no organization specified, returns True if user is admin of any org.
        """
        if not (self.role and self.role.name == Role.ADMINISTRATOR):
            return False
        if organization is None:
            return self.admin_organization is not None
        return self.admin_organization_id == organization.id

    def has_perm_create_users(self):
        return self.is_system_admin() or self._resolve("perm_create_users", "can_create_users")

    def has_perm_manage_projects(self):
        return self.is_system_admin() or self._resolve("perm_manage_projects", "can_manage_projects")

    def has_perm_manage_tasks(self):
        return self.is_system_admin() or self._resolve("perm_manage_tasks", "can_manage_tasks")

    def has_perm_move_task_stages(self):
        return self.is_system_admin() or self._resolve("perm_move_task_stages", "can_move_task_stages")

    def has_perm_move_task_categories(self):
        return self.is_system_admin() or self._resolve(
            "perm_move_task_categories", "can_move_task_categories"
        )

    def has_perm_reject_testing(self):
        return self.is_system_admin() or self._resolve("perm_reject_testing", "can_reject_testing")

    def has_perm_add_project_notes(self):
        return self.is_system_admin() or self._resolve(
            "perm_add_project_notes", "can_add_project_notes"
        )

    def has_perm_view_assigned_only(self):
        if self.is_system_admin():
            return False
        return self._resolve("perm_view_assigned_only", "can_view_assigned_only")

    def has_perm_manage_organizations(self):
        return self.is_system_admin() or self._resolve(
            "perm_manage_organizations", "can_manage_organizations"
        )

    @staticmethod
    def generate_strong_password(length=16):
        chars = string.ascii_letters + string.digits + string.punctuation
        return "".join(secrets.choice(chars) for _ in range(length))
