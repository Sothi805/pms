from .models import AuditLog


def log_action(*, actor, action, target_type="", target_id=None, detail="", project=None):
    """Create an immutable audit log entry."""
    AuditLog.objects.create(
        actor=actor,
        action=action,
        target_type=target_type,
        target_id=target_id,
        detail=detail,
        project=project,
    )
