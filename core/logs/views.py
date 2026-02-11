from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import AuditLog


@login_required
def audit_log_list(request):
    if not request.user.is_system_admin():
        from django.contrib import messages
        messages.error(request, "Permission denied.")
        from django.shortcuts import redirect
        return redirect("dashboard")

    logs = AuditLog.objects.select_related("actor", "project").all()[:200]
    return render(request, "logs/audit_log_list.html", {"logs": logs})
