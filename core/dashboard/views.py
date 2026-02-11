from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from projects.models import Project
from tasks.models import TaskInstance


@login_required
def dashboard(request):
    user = request.user

    if user.is_system_admin() or user.has_perm_manage_projects():
        projects = Project.objects.select_related("organization").all()[:10]
    else:
        # User can see projects where they are member, commenter, or viewer
        projects = (
            Project.objects.filter(members=user)
            | Project.objects.filter(commenters=user)
            | Project.objects.filter(viewers=user)
        ).distinct().select_related("organization")[:10]

    # Project count
    total_projects = projects.count()

    # Recent tasks for this user (active only) - only show assigned tasks
    if user.is_superuser:
        recent_tasks = TaskInstance.objects.filter(is_closed=False).select_related("project").all()[:10]
    else:
        recent_tasks = TaskInstance.objects.filter(
            assignees=user, is_closed=False
        ).select_related("project")[:10]

    # Stats (active tasks only) - only count assigned tasks
    if user.is_superuser:
        all_user_tasks = TaskInstance.objects.filter(is_closed=False)
    else:
        all_user_tasks = TaskInstance.objects.filter(assignees=user, is_closed=False)
    total_tasks = all_user_tasks.count()
    done_tasks = all_user_tasks.filter(stage=TaskInstance.DONE).count()
    in_progress_tasks = all_user_tasks.filter(stage=TaskInstance.IN_PROGRESS).count()

    return render(request, "dashboard/dashboard.html", {
        "projects": projects,
        "recent_tasks": recent_tasks,
        "total_projects": total_projects,
        "total_tasks": total_tasks,
        "done_tasks": done_tasks,
        "in_progress_tasks": in_progress_tasks,
    })
