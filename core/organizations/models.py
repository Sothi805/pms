from django.conf import settings
from django.db import models


class Organization(models.Model):
    """Governance boundary. Created/managed only by superuser."""

    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="member_organizations",
        help_text="Users who belong to this organization.",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_organizations",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def user_is_member(self, user):
        """Check if user is a member of this organization.
        
        System Administrators and organization Administrators are automatically members.
        """
        if user.is_system_admin():
            return True
        if user.is_org_admin(self):
            return True
        return self.members.filter(pk=user.pk).exists()
