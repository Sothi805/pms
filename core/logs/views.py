from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import redirect, render

from .models import AuditLog


@login_required
def audit_log_list(request):
    if not request.user.is_system_admin():
        from django.contrib import messages
        messages.error(request, "Permission denied.")
        return redirect("dashboard")

    logs_qs = AuditLog.objects.select_related("actor", "project").all()
    total_count = logs_qs.count()

    try:
        page_size = int(request.GET.get("page_size", 20))
        page_size = max(1, min(page_size, max(total_count, 1)))
    except (ValueError, TypeError):
        page_size = 20

    paginator = Paginator(logs_qs, page_size)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    return render(request, "logs/audit_log_list.html", {
        "page_obj": page_obj,
        "page_size": page_size,
        "total_count": total_count,
    })
