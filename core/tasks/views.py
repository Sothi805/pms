import json

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from logs.utils import log_action

from .forms import TaskInstanceForm
from .models import TaskInstance

User = get_user_model()


@login_required
def task_board(request, project_pk):
    """Kanban board: rows = stages, columns = single category (selectable)."""
    from projects.models import Project

    project = get_object_or_404(Project, pk=project_pk)
    user = request.user

    tasks = TaskInstance.objects.filter(project=project, is_closed=False)

    stages = TaskInstance.STAGE_CHOICES
    categories = TaskInstance.CATEGORY_CHOICES

    # Get selected category from query parameter, default to first category
    selected_category = request.GET.get('category', TaskInstance.DEVELOPMENT)
    
    # Ensure selected category is valid
    valid_categories = [cat[0] for cat in categories]
    if selected_category not in valid_categories:
        selected_category = TaskInstance.DEVELOPMENT

    # Build board data: {stage: [tasks]} for the selected category
    board = {}
    for stg_key, stg_label in stages:
        board[stg_key] = {
            "label": stg_label,
            "tasks": list(tasks.filter(category=selected_category, stage=stg_key))
        }

    can_move = user.is_system_admin() or user.has_perm_move_task_stages()
    can_manage = user.is_system_admin() or user.has_perm_manage_tasks()

    return render(request, "tasks/task_board.html", {
        "project": project,
        "board": board,
        "stages": stages,
        "categories": categories,
        "selected_category": selected_category,
        "can_move": can_move,
        "can_manage": can_manage,
    })


@login_required
def task_create(request, project_pk):
    from projects.models import Project, ProjectCategory

    project = get_object_or_404(Project, pk=project_pk)
    if not (request.user.is_superuser or request.user.has_perm_manage_tasks()):
        messages.error(request, "Permission denied.")
        return redirect("tasks:task_board", project_pk=project_pk)

    form = TaskInstanceForm(request.POST or None, project=project)
    
    # Pre-select project_category if provided in query params
    if request.method == "GET" and "project_category" in request.GET:
        try:
            category_pk = request.GET.get("project_category")
            category = ProjectCategory.objects.get(pk=category_pk, project=project)
            form.fields["project_category"].initial = category
        except (ProjectCategory.DoesNotExist, ValueError):
            pass
    
    if request.method == "POST" and form.is_valid():
        task = form.save(commit=False)
        task.project = project
        task.created_by = request.user
        task.save()
        form.save_m2m()
        log_action(
            actor=request.user,
            action="TASK_CREATED",
            target_type="TaskInstance",
            target_id=task.pk,
            detail=f"Task '{task.title}' created in {task.get_category_display()}.",
            project=project,
        )
        messages.success(request, f"Task '{task.title}' created.")
        return redirect("tasks:task_board", project_pk=project_pk)
    return render(request, "tasks/task_form.html", {
        "form": form,
        "project": project,
        "title": "Create Task",
    })


@login_required
def task_detail(request, pk):
    task = get_object_or_404(
        TaskInstance.objects.select_related("project", "created_by", "parent_task")
        .prefetch_related("assignees", "children"),
        pk=pk,
    )
    user = request.user
    from logs.models import AuditLog
    from .forms import TaskNoteForm

    notes = task.notes.select_related("author").all()
    note_form = TaskNoteForm()

    # Members and commenters can add notes to the task
    can_add_notes = (
        user.has_perm_manage_tasks() 
        or (task.project and task.project.user_is_commenter(user))
    ) if task.project else False

    if request.method == "POST" and can_add_notes:
        note_form = TaskNoteForm(request.POST)
        if note_form.is_valid():
            note = note_form.save(commit=False)
            note.task = task
            note.author = user
            note.save()
            messages.success(request, "Note added.")
            return redirect("tasks:task_detail", pk=pk)

    logs = AuditLog.objects.filter(
        target_type="TaskInstance", target_id=task.pk
    ).order_by("-timestamp")

    return render(request, "tasks/task_detail.html", {
        "task": task,
        "logs": logs,
        "project": task.project,
        "notes": notes,
        "note_form": note_form,
        "can_add_notes": can_add_notes,
    })


@login_required
def task_api_detail(request, pk):
    """API endpoint to get task details as JSON for modal display."""
    task = get_object_or_404(
        TaskInstance.objects.select_related("project", "created_by", "parent_task", "project_category")
        .prefetch_related("assignees", "children"),
        pk=pk,
    )
    
    # Get display labels for choices
    stage_display = dict(TaskInstance.STAGE_CHOICES).get(task.stage, task.stage)
    category_display = dict(TaskInstance.CATEGORY_CHOICES).get(task.category, task.category)
    
    return JsonResponse({
        "id": task.pk,
        "title": task.title,
        "description": task.description,
        "stage": task.stage,
        "stage_display": stage_display,
        "category": task.category,
        "category_display": category_display,
        "story_points": task.story_points,
        "points_earned": task.points_earned,
        "deadline": task.deadline.isoformat() if task.deadline else None,
        "start_date": task.start_date.isoformat() if task.start_date else None,
        "end_date": task.end_date.isoformat() if task.end_date else None,
        "due_status": task.due_status,
        "on_time_status": task.on_time_status,
        "stage_status": task.stage_status,
        "is_closed": task.is_closed,
        "created_by": task.created_by.username if task.created_by else "System",
        "assignees": [a.username for a in task.assignees.all()],
        "project_category": task.project_category.name if task.project_category else None,
    })


@login_required
def task_edit(request, pk):
    task = get_object_or_404(TaskInstance, pk=pk)
    if not (request.user.is_superuser or request.user.has_perm_manage_tasks()):
        messages.error(request, "Permission denied.")
        return redirect("tasks:task_detail", pk=pk)
    if task.is_closed:
        messages.error(request, "Closed tasks cannot be edited.")
        return redirect("tasks:task_detail", pk=pk)

    form = TaskInstanceForm(request.POST or None, instance=task, project=task.project)
    if request.method == "POST" and form.is_valid():
        form.save()
        log_action(
            actor=request.user,
            action="TASK_UPDATED",
            target_type="TaskInstance",
            target_id=task.pk,
            detail=f"Task '{task.title}' updated.",
            project=task.project,
        )
        messages.success(request, f"Task '{task.title}' updated.")
        return redirect("tasks:task_board", project_pk=task.project.pk)
    return render(request, "tasks/task_form.html", {
        "form": form,
        "project": task.project,
        "title": f"Edit — {task.title}",
    })


@require_POST
@login_required
@login_required
@require_POST
def task_move(request, pk):
    """Drag-and-drop handler: move task to a new stage (and optionally category)."""
    task = get_object_or_404(TaskInstance, pk=pk)
    user = request.user

    # Handle both JSON (from board) and form data (from detail page)
    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
    else:
        # Form data from detail page
        data = request.POST.dict()

    new_stage = data.get("stage")
    new_category = data.get("category")  # optional, for category moves

    if task.is_closed:
        if request.content_type == 'application/json':
            return JsonResponse({"error": "Task is closed."}, status=403)
        else:
            messages.error(request, "Task is closed and cannot be moved.")
            return redirect("tasks:task_detail", pk=pk)

    # ── Permission checks ──
    if new_category and new_category != task.category:
        if not (user.is_system_admin() or user.has_perm_move_task_categories()):
            error_msg = "No permission to move categories."
            if request.content_type == 'application/json':
                return JsonResponse({"error": error_msg}, status=403)
            messages.error(request, error_msg)
            return redirect("tasks:task_detail", pk=pk)

    if new_stage and new_stage != task.stage:
        if not (user.is_system_admin() or user.has_perm_move_task_stages()):
            error_msg = "No permission to move stages."
            if request.content_type == 'application/json':
                return JsonResponse({"error": error_msg}, status=403)
            messages.error(request, error_msg)
            return redirect("tasks:task_detail", pk=pk)

    # ── Validate stage ──
    valid_stages = [s[0] for s in TaskInstance.STAGE_CHOICES]
    if new_stage and new_stage not in valid_stages:
        error_msg = "Invalid stage."
        if request.content_type == 'application/json':
            return JsonResponse({"error": error_msg}, status=400)
        messages.error(request, error_msg)
        return redirect("tasks:task_detail", pk=pk)

    valid_cats = [c[0] for c in TaskInstance.CATEGORY_CHOICES]
    if new_category and new_category not in valid_cats:
        error_msg = "Invalid category."
        if request.content_type == 'application/json':
            return JsonResponse({"error": error_msg}, status=400)
        messages.error(request, error_msg)
        return redirect("tasks:task_detail", pk=pk)

    old_stage = task.stage
    old_category = task.category

    # ── REJECT can only occur in TESTING ──
    if new_stage == TaskInstance.REJECT:
        if task.category != TaskInstance.TESTING:
            error_msg = "REJECT only allowed in TESTING."
            if request.content_type == 'application/json':
                return JsonResponse({"error": error_msg}, status=400)
            messages.error(request, error_msg)
            return redirect("tasks:task_detail", pk=pk)
        if not (user.is_system_admin() or user.has_perm_reject_testing()):
            error_msg = "No permission to reject."
            if request.content_type == 'application/json':
                return JsonResponse({"error": error_msg}, status=403)
            messages.error(request, error_msg)
            return redirect("tasks:task_detail", pk=pk)

    # Apply category change
    if new_category and new_category != task.category:
        task.category = new_category

    # Apply stage change
    if new_stage and new_stage != old_stage:
        task.stage = new_stage

    task.save()

    detail_parts = []
    if new_stage and new_stage != old_stage:
        detail_parts.append(f"Stage: {old_stage} → {new_stage}")
    if new_category and new_category != old_category:
        detail_parts.append(f"Category: {old_category} → {new_category}")

    log_action(
        actor=user,
        action="STAGE_CHANGE",
        target_type="TaskInstance",
        target_id=task.pk,
        detail=f"Task '{task.title}' moved. {'; '.join(detail_parts)}",
        project=task.project,
    )

    # ── Handle stage transitions with cloning ──
    if new_stage == TaskInstance.DONE and old_stage != TaskInstance.DONE:
        if task.category in TaskInstance.BUILD_CATEGORIES:
            _handle_build_done(task, user)
        elif task.category == TaskInstance.TESTING:
            _handle_testing_done(task, user)
        elif task.category == TaskInstance.DEPLOYMENT:
            _handle_deployment_done(task, user)
        elif task.category == TaskInstance.GENERAL:
            _handle_general_done(task, user)

    # ── REJECT in TESTING: close + clone back ──
    if new_stage == TaskInstance.REJECT and task.category == TaskInstance.TESTING:
        _handle_testing_reject(task, user)

    # For form submissions, redirect back to detail page
    if request.content_type != 'application/json':
        messages.success(request, f"Task moved to {dict(TaskInstance.STAGE_CHOICES).get(new_stage, new_stage)}")
        return redirect("tasks:task_detail", pk=pk)

    return JsonResponse({"ok": True, "stage": task.stage, "category": task.category})


def _handle_build_done(task, user):
    """Build phase DONE: earn points once, clone to TESTING. Task stays visible."""
    if not task.points_earned:
        task.points_earned = True
        task.save()

    # Clone to TESTING
    testing_task = TaskInstance.objects.create(
        title=task.title,
        description=task.description,
        project=task.project,
        category=TaskInstance.TESTING,
        stage=TaskInstance.TODO,
        created_by=user,
        story_points=task.story_points,
        deadline=task.deadline,
        parent_task=task,
        original_category=task.category,
    )
    testing_task.assignees.set(task.assignees.all())

    log_action(
        actor=user,
        action="TASK_CLONED_TO_TESTING",
        target_type="TaskInstance",
        target_id=testing_task.pk,
        detail=f"Testing task cloned from '{task.title}' ({task.get_category_display()}).",
        project=task.project,
    )


def _handle_testing_done(task, user):
    """Testing DONE: earn points, clone to DEPLOYMENT. Task stays visible."""
    if not task.points_earned:
        task.points_earned = True
        task.save()

    # Clone to DEPLOYMENT
    deployment_task = TaskInstance.objects.create(
        title=task.title,
        description=task.description,
        project=task.project,
        category=TaskInstance.DEPLOYMENT,
        stage=TaskInstance.TODO,
        created_by=user,
        story_points=task.story_points,
        deadline=task.deadline,
        parent_task=task,
        original_category=task.original_category or TaskInstance.TESTING,
    )
    deployment_task.assignees.set(task.assignees.all())

    log_action(
        actor=user,
        action="TASK_CLONED_TO_DEPLOYMENT",
        target_type="TaskInstance",
        target_id=deployment_task.pk,
        detail=f"Deployment task cloned from '{task.title}' (Testing).",
        project=task.project,
    )


def _handle_deployment_done(task, user):
    """Deployment DONE is FINAL: earn points. Task stays visible."""
    if not task.points_earned:
        task.points_earned = True
        task.save()

    log_action(
        actor=user,
        action="DEPLOYMENT_DONE",
        target_type="TaskInstance",
        target_id=task.pk,
        detail=f"Deployment DONE for '{task.title}'. Task complete.",
        project=task.project,
    )


def _handle_general_done(task, user):
    """General task DONE: earn contribution points. Task stays visible as completed."""
    if not task.points_earned:
        task.points_earned = True
        task.save()

    log_action(
        actor=user,
        action="GENERAL_DONE",
        target_type="TaskInstance",
        target_id=task.pk,
        detail=f"General task '{task.title}' DONE. Contribution points earned.",
        project=task.project,
    )


def _handle_testing_reject(task, user):
    """REJECT in TESTING: close testing, clone back to original category."""
    task.is_closed = True
    task.save()

    rework_cat = task.original_category or TaskInstance.DEVELOPMENT
    rework_task = TaskInstance.objects.create(
        title=task.title,
        description=task.description,
        project=task.project,
        category=rework_cat,
        stage=TaskInstance.TODO,
        created_by=user,
        story_points=0,  # rework: no new story points
        deadline=task.deadline,
        parent_task=task,
        original_category=rework_cat,
    )
    rework_task.assignees.set(task.assignees.all())

    log_action(
        actor=user,
        action="TESTING_REJECTED",
        target_type="TaskInstance",
        target_id=rework_task.pk,
        detail=f"Testing rejected for '{task.title}'. Rework cloned back to {rework_cat}.",
        project=task.project,
    )
