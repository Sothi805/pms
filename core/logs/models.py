from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """Immutable system log. Cannot be edited or deleted."""

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=50)
    target_type = models.CharField(max_length=50, blank=True)
    target_id = models.PositiveIntegerField(null=True, blank=True)
    detail = models.TextField(blank=True)
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {self.action} by {self.actor}"

    def save(self, *args, **kwargs):
        # Immutable: only allow creation
        if self.pk:
            return  # block updates
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Immutable: block deletion (except superuser hard delete via raw SQL)
        return
