from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from logs.utils import log_action

from .forms import LoginForm, PermissionOverrideForm, UserCreateForm, UserEditForm, ChangePasswordForm, SetPasswordForm

User = get_user_model()


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = authenticate(
            request,
            username=form.cleaned_data["username"],
            password=form.cleaned_data["password"],
        )
        if user is not None:
            login(request, user)
            return redirect(request.GET.get("next", "dashboard"))
        form.add_error(None, "Invalid credentials.")
    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("accounts:login")


@login_required
def user_list(request):
    if not request.user.is_system_admin():
        messages.error(request, "Permission denied.")
        return redirect("dashboard")
    users = User.objects.select_related("role").all()
    return render(request, "accounts/user_list.html", {"users": users})


@login_required
def user_create(request):
    if not request.user.is_system_admin():
        messages.error(request, "Permission denied.")
        return redirect("dashboard")

    form = UserCreateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save(commit=False)
        raw_pw = User.generate_strong_password()
        user.set_password(raw_pw)
        user.is_auto_generated = True
        user.is_active = False
        user.save()
        log_action(
            actor=request.user,
            action="USER_CREATED",
            target_type="User",
            target_id=user.pk,
            detail=f"User '{user.username}' created (auto-generated, inactive).",
        )
        messages.success(
            request,
            f"User '{user.username}' created. Temporary password: {raw_pw}",
        )
        return redirect("accounts:user_list")
    return render(request, "accounts/user_form.html", {"form": form, "title": "Create User"})


@login_required
def user_edit(request, pk):
    if not request.user.is_system_admin():
        messages.error(request, "Permission denied.")
        return redirect("dashboard")

    user = get_object_or_404(User, pk=pk)
    form = UserEditForm(request.POST or None, instance=user)
    perm_form = PermissionOverrideForm(request.POST or None, instance=user, prefix="perms")

    if request.method == "POST" and form.is_valid() and perm_form.is_valid():
        old_role = user.role
        user = form.save()
        perm_form.save()
        log_action(
            actor=request.user,
            action="USER_UPDATED",
            target_type="User",
            target_id=user.pk,
            detail=f"User '{user.username}' updated. Role: {old_role} → {user.role}",
        )
        messages.success(request, f"User '{user.username}' updated.")
        return redirect("accounts:user_list")
    return render(
        request,
        "accounts/user_form.html",
        {"form": form, "perm_form": perm_form, "title": f"Edit User — {user.username}"},
    )


@login_required
def reset_password(request, pk):
    if not request.user.is_system_admin():
        messages.error(request, "Only system administrator can reset passwords.")
        return redirect("dashboard")

    user = get_object_or_404(User, pk=pk)
    raw_pw = User.generate_strong_password()
    user.set_password(raw_pw)
    user.is_active = True
    user.is_auto_generated = False
    user.save()
    log_action(
        actor=request.user,
        action="PASSWORD_RESET",
        target_type="User",
        target_id=user.pk,
        detail=f"Password reset for '{user.username}'.",
    )
    messages.success(request, f"New password for '{user.username}': {raw_pw}")
    return redirect("accounts:user_list")


@login_required
def set_user_password(request, pk):
    """Superuser manually sets a password for any user."""
    if not request.user.is_system_admin():
        messages.error(request, "Only system administrator can set user passwords.")
        return redirect("dashboard")

    user = get_object_or_404(User, pk=pk)
    form = SetPasswordForm(request.POST or None)
    
    if request.method == "POST" and form.is_valid():
        password = form.cleaned_data["password"]
        user.set_password(password)
        user.is_active = True
        user.save()
        log_action(
            actor=request.user,
            action="PASSWORD_SET_BY_ADMIN",
            target_type="User",
            target_id=user.pk,
            detail=f"Password manually set for '{user.username}' by admin.",
        )
        messages.success(request, f"Password set for '{user.username}'.")
        return redirect("accounts:user_list")
    
    return render(
        request,
        "accounts/set_password_form.html",
        {"form": form, "target_user": user},
    )


@login_required
def settings_view(request):
    """User settings page with change password."""
    form = ChangePasswordForm(request.POST or None)
    
    if request.method == "POST" and form.is_valid():
        user = request.user
        current_password = form.cleaned_data["current_password"]
        new_password = form.cleaned_data["new_password"]
        
        # Verify current password
        if not user.check_password(current_password):
            form.add_error("current_password", "Current password is incorrect.")
        else:
            user.set_password(new_password)
            user.save()
            log_action(
                actor=request.user,
                action="PASSWORD_CHANGED",
                target_type="User",
                target_id=user.pk,
                detail="User changed their password.",
            )
            messages.success(request, "Password changed successfully.")
            # Re-authenticate user to keep them logged in
            login(request, user)
            return redirect("accounts:settings")
    
    organizations = request.user.member_organizations.all()
    return render(request, "accounts/settings.html", {
        "form": form,
        "organizations": organizations
    })


@login_required
@require_http_methods(["GET"])
def search_users(request):
    """API endpoint to search for active users by username or email."""
    # Allow system admins and users who can manage tasks (for assignee autocomplete)
    if not (request.user.is_system_admin() or request.user.has_perm_manage_tasks()):
        return JsonResponse({"error": "Permission denied."}, status=403)
    
    query = request.GET.get("q", "").strip()
    
    if not query or len(query) < 1:
        return JsonResponse({"users": []})
    
    # Search by username or email (case-insensitive)
    users = User.objects.filter(
        is_active=True
    ).filter(
        Q(username__icontains=query) | Q(email__icontains=query)
    ).values("id", "username", "email").order_by("username")[:20]
    
    return JsonResponse({
        "users": list(users)
    })