from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import models
from django.shortcuts import get_object_or_404, redirect, render

from logs.utils import log_action

from .forms import GeneralTaskForm
from .models import GeneralTask

User = get_user_model()


@login_required
def task_list(request):
    """List all general tasks (user's created and assigned tasks)."""
    user = request.user
    
    # System admin sees all tasks
    if user.is_system_admin():
        tasks = GeneralTask.objects.all()
    else:
        # Regular users see only their created and assigned tasks
        tasks = GeneralTask.objects.filter(
            models.Q(created_by=user) | models.Q(assigned_to=user)
        )
    
    # Get status filter from query params
    status_filter = request.GET.get('status', 'all')
    if status_filter != 'all':
        tasks = tasks.filter(status=status_filter)
    
    return render(request, "general_tasks/task_list.html", {
        "tasks": tasks,
        "status_filter": status_filter,
        "status_choices": GeneralTask.STATUS_CHOICES,
    })


@login_required
def task_create(request):
    """Create a new general task."""
    form = GeneralTaskForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        task = form.save(commit=False)
        task.created_by = request.user
        task.save()
        log_action(
            actor=request.user,
            action="GENERAL_TASK_CREATED",
            target_type="GeneralTask",
            target_id=task.pk,
            detail=f"General task '{task.title}' created.",
        )
        messages.success(request, f"Task '{task.title}' created.")
        return redirect("general_tasks:task_list")
    
    return render(request, "general_tasks/task_form.html", {
        "form": form,
        "title": "Create Task",
    })


@login_required
def task_detail(request, pk):
    """View general task details."""
    task = get_object_or_404(GeneralTask, pk=pk)
    user = request.user
    
    # Permission check
    if not user.is_system_admin() and task.created_by != user and task.assigned_to != user:
        messages.error(request, "Permission denied.")
        return redirect("general_tasks:task_list")
    
    return render(request, "general_tasks/task_detail.html", {
        "task": task,
    })


@login_required
def task_edit(request, pk):
    """Edit a general task."""
    task = get_object_or_404(GeneralTask, pk=pk)
    user = request.user
    
    # Permission check: creator or system admin
    if not user.is_system_admin() and task.created_by != user:
        messages.error(request, "Only task creator can edit this task.")
        return redirect("general_tasks:task_list")
    
    form = GeneralTaskForm(request.POST or None, instance=task)
    if request.method == "POST" and form.is_valid():
        form.save()
        log_action(
            actor=request.user,
            action="GENERAL_TASK_UPDATED",
            target_type="GeneralTask",
            target_id=task.pk,
            detail=f"General task '{task.title}' updated.",
        )
        messages.success(request, f"Task '{task.title}' updated.")
        return redirect("general_tasks:task_detail", pk=pk)
    
    return render(request, "general_tasks/task_form.html", {
        "form": form,
        "title": f"Edit — {task.title}",
        "task": task,
    })


@login_required
def task_delete(request, pk):
    """Delete a general task."""
    task = get_object_or_404(GeneralTask, pk=pk)
    user = request.user
    
    # Permission check: creator or system admin
    if not user.is_system_admin() and task.created_by != user:
        messages.error(request, "Only task creator can delete this task.")
        return redirect("general_tasks:task_list")
    
    if request.method == "POST":
        task_title = task.title
        task.delete()
        log_action(
            actor=request.user,
            action="GENERAL_TASK_DELETED",
            target_type="GeneralTask",
            target_id=pk,
            detail=f"General task '{task_title}' deleted.",
        )
        messages.success(request, f"Task '{task_title}' deleted.")
        return redirect("general_tasks:task_list")
    
    return render(request, "general_tasks/task_confirm_delete.html", {
        "task": task,
    })


@login_required
def task_update_status(request, pk, status):
    """Update task status (quick action)."""
    task = get_object_or_404(GeneralTask, pk=pk)
    user = request.user
    
    # Permission check: creator, assignee, or system admin
    if not user.is_system_admin() and task.created_by != user and task.assigned_to != user:
        messages.error(request, "Permission denied.")
        return redirect("general_tasks:task_list")
    
    # Validate status
    valid_statuses = [s[0] for s in GeneralTask.STATUS_CHOICES]
    if status not in valid_statuses:
        messages.error(request, "Invalid status.")
        return redirect("general_tasks:task_detail", pk=pk)
    
    task.status = status
    task.save()
    log_action(
        actor=request.user,
        action="GENERAL_TASK_STATUS_CHANGED",
        target_type="GeneralTask",
        target_id=task.pk,
        detail=f"General task '{task.title}' status changed to {status}.",
    )
    messages.success(request, f"Task status updated to {task.get_status_display()}.")
    return redirect("general_tasks:task_detail", pk=pk)
