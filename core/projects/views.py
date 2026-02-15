from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from logs.utils import log_action

from .forms import ProjectForm, ProjectNoteForm, ProjectCategoryForm
from .models import Project, ProjectNote, ProjectCategory

User = get_user_model()


@login_required
def project_list(request):
    user = request.user
    if user.is_system_admin():
        projects = Project.objects.select_related("organization").all()
    else:
        # Get organizations user belongs to
        user_orgs = user.member_organizations.values_list('id', flat=True)
        
        # All users only see projects in their organizations
        # Their role (manage_projects, member, etc) determines what they can do within those projects
        projects = Project.objects.filter(
            organization_id__in=user_orgs
        ).select_related("organization").distinct()
    
    return render(request, "projects/project_list.html", {"projects": projects})


@login_required
def project_create(request):
    if not request.user.has_perm_manage_projects():
        messages.error(request, "Permission denied.")
        return redirect("projects:project_list")

    form = ProjectForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        project = form.save(commit=False)
        project.created_by = request.user
        project.save()
        form.save_m2m()
        log_action(
            actor=request.user,
            action="PROJECT_CREATED",
            target_type="Project",
            target_id=project.pk,
            detail=f"Project '{project.name}' created.",
        )
        messages.success(request, f"Project '{project.name}' created.")
        return redirect("projects:project_detail", pk=project.pk)
    return render(request, "projects/project_form.html", {
        "form": form, 
        "title": "Create Project",
        "existing_members": [],
        "existing_commenters": [],
        "existing_viewers": [],
    })


def _ensure_category_order(project):
    """Initialize order values for all categories without breaking existing order."""
    categories = project.categories.all().order_by("order", "created_at")
    for idx, cat in enumerate(categories):
        if cat.order != idx:
            cat.order = idx
            cat.save()


@login_required
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    user = request.user

    # Permission check: user must have access to organization
    if not project.organization.user_is_member(user):
        messages.error(request, "Permission denied.")
        return redirect("projects:project_list")

    # Ensure categories have proper order values
    _ensure_category_order(project)
    
    # Get tasks without a project category
    from tasks.models import TaskInstance
    uncategorized_tasks = TaskInstance.objects.filter(
        project=project,
        project_category__isnull=True,
        is_closed=False
    ).select_related("created_by").prefetch_related("assignees").order_by("-created_at")
    
    notes = project.notes.select_related("author").all()
    note_form = ProjectNoteForm()
    
    # Get recent audit logs for this project (last 20)
    audit_logs = project.audit_logs.select_related("actor").all()[:20]

    # Members and commenters can add notes to the project
    can_add_notes = project.user_is_commenter(user)

    if request.method == "POST" and can_add_notes:
        note_form = ProjectNoteForm(request.POST)
        if note_form.is_valid():
            note = note_form.save(commit=False)
            note.project = project
            note.author = user
            note.save()
            messages.success(request, "Note added.")
            return redirect("projects:project_detail", pk=pk)

    return render(request, "projects/project_detail.html", {
        "project": project,
        "notes": notes,
        "note_form": note_form,
        "can_add_notes": can_add_notes,
        "audit_logs": audit_logs,
        "uncategorized_tasks": uncategorized_tasks,
    })


@login_required
def project_edit(request, pk):
    if not request.user.has_perm_manage_projects():
        messages.error(request, "Permission denied.")
        return redirect("projects:project_list")

    project = get_object_or_404(Project, pk=pk)
    user = request.user
    
    # Verify user is member of project's organization
    if not (user.is_system_admin() or project.organization.user_is_member(user)):
        messages.error(request, "Permission denied.")
        return redirect("projects:project_list")
    
    form = ProjectForm(request.POST or None, instance=project)
    if request.method == "POST" and form.is_valid():
        form.save()
        log_action(
            actor=request.user,
            action="PROJECT_UPDATED",
            target_type="Project",
            target_id=project.pk,
            detail=f"Project '{project.name}' updated.",
        )
        messages.success(request, f"Project '{project.name}' updated.")
        return redirect("projects:project_detail", pk=pk)
    return render(request, "projects/project_form.html", {
        "form": form,
        "title": f"Edit — {project.name}",
        "existing_members": list(project.members.values_list("username", flat=True)),
        "existing_commenters": list(project.commenters.values_list("username", flat=True)),
        "existing_viewers": list(project.viewers.values_list("username", flat=True)),
    })


@login_required
def note_delete(request, pk):
    note = get_object_or_404(ProjectNote, pk=pk)
    project = note.project
    project_pk = project.pk
    user = request.user
    
    # Check organization membership
    if not (user.is_system_admin() or project.organization.user_is_member(user)):
        messages.error(request, "Permission denied.")
        return redirect("projects:project_list")
    
    # Check if user is note author or system admin
    if user == note.author or user.is_system_admin():
        note.delete()
        messages.success(request, "Note deleted.")
    else:
        messages.error(request, "Permission denied.")
    return redirect("projects:project_detail", pk=project_pk)


@login_required
def category_create(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk)
    user = request.user
    
    # Verify user is member of project's organization
    if not (user.is_system_admin() or project.organization.user_is_member(user)):
        messages.error(request, "Permission denied.")
        return redirect("projects:project_list")
    
    # Only system admins or members can manage categories
    can_manage = user.is_system_admin() or project.user_is_member(user)
    
    if not can_manage:
        messages.error(request, "Permission denied.")
        return redirect("projects:project_detail", pk=project_pk)
    
    form = ProjectCategoryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        category = form.save(commit=False)
        category.project = project
        category.save()
        messages.success(request, f"Category '{category.name}' created.")
        return redirect("projects:project_detail", pk=project_pk)
    
    return render(request, "projects/category_form.html", {
        "form": form,
        "project": project,
        "title": "Create Category",
    })


@login_required
def category_edit(request, category_pk):
    category = get_object_or_404(ProjectCategory, pk=category_pk)
    project = category.project
    user = request.user
    
    # Verify user is member of project's organization
    if not (user.is_system_admin() or project.organization.user_is_member(user)):
        messages.error(request, "Permission denied.")
        return redirect("projects:project_list")
    
    # Only system admins or members can manage categories
    can_manage = user.is_system_admin() or project.user_is_member(user)
    
    if not can_manage:
        messages.error(request, "Permission denied.")
        return redirect("projects:project_detail", pk=project.pk)
    
    form = ProjectCategoryForm(request.POST or None, instance=category)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"Category '{category.name}' updated.")
        return redirect("projects:project_detail", pk=project.pk)
    
    return render(request, "projects/category_form.html", {
        "form": form,
        "project": project,
        "title": f"Edit — {category.name}",
    })


@login_required
def category_delete(request, category_pk):
    category = get_object_or_404(ProjectCategory, pk=category_pk)
    project = category.project
    user = request.user
    
    # Verify user is member of project's organization
    if not (user.is_system_admin() or project.organization.user_is_member(user)):
        messages.error(request, "Permission denied.")
        return redirect("projects:project_list")
    
    # Only system admins or members can manage categories
    can_manage = user.is_system_admin() or project.user_is_member(user)
    
    if not can_manage:
        messages.error(request, "Permission denied.")
        return redirect("projects:project_detail", pk=project.pk)
    
    if request.method == "POST":
        category_name = category.name
        category.delete()
        messages.success(request, f"Category '{category_name}' deleted.")
        return redirect("projects:project_detail", pk=project.pk)
    
    return render(request, "projects/category_confirm_delete.html", {
        "category": category,
        "project": project,
    })


@login_required
def category_move_up(request, category_pk):
    """Move category up in display order."""
    category = get_object_or_404(ProjectCategory, pk=category_pk)
    project = category.project
    user = request.user
    
    # Verify user is member of project's organization
    if not (user.is_system_admin() or project.organization.user_is_member(user)):
        messages.error(request, "Permission denied.")
        return redirect("projects:project_list")
    
    # Only system admins or members can manage categories
    can_manage = user.is_system_admin() or project.user_is_member(user)
    
    if not can_manage:
        messages.error(request, "Permission denied.")
        return redirect("projects:project_detail", pk=project.pk)
    
    # Ensure all categories have sequential order
    _ensure_category_order(project)
    
    # Find previous category (lower order value)
    previous = ProjectCategory.objects.filter(
        project=project,
        order__lt=category.order
    ).order_by("-order").first()
    
    if previous:
        # Swap order values
        category.order, previous.order = previous.order, category.order
        category.save()
        previous.save()
        messages.success(request, f"Category '{category.name}' moved up.")
    else:
        messages.info(request, "This category is already at the top.")
    
    return redirect("projects:project_detail", pk=project.pk)


@login_required
def category_move_down(request, category_pk):
    """Move category down in display order."""
    category = get_object_or_404(ProjectCategory, pk=category_pk)
    project = category.project
    user = request.user
    
    # Verify user is member of project's organization
    if not (user.is_system_admin() or project.organization.user_is_member(user)):
        messages.error(request, "Permission denied.")
        return redirect("projects:project_list")
    
    # Only system admins or members can manage categories
    can_manage = user.is_system_admin() or project.user_is_member(user)
    
    if not can_manage:
        messages.error(request, "Permission denied.")
        return redirect("projects:project_detail", pk=project.pk)
    
    # Ensure all categories have sequential order
    _ensure_category_order(project)
    
    # Find next category (higher order value)
    next_cat = ProjectCategory.objects.filter(
        project=project,
        order__gt=category.order
    ).order_by("order").first()
    
    if next_cat:
        # Swap order values
        category.order, next_cat.order = next_cat.order, category.order
        category.save()
        next_cat.save()
        messages.success(request, f"Category '{category.name}' moved down.")
    else:
        messages.info(request, "This category is already at the bottom.")
    
    return redirect("projects:project_detail", pk=project.pk)

