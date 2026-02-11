from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from logs.utils import log_action

from .forms import OrganizationForm, OrganizationMembersForm
from .models import Organization

User = get_user_model()

@login_required
def organization_list(request):
    user = request.user
    if user.is_system_admin():
        # System Administrators see all organizations
        orgs = Organization.objects.all()
    else:
        # Non-system admins see only organizations they belong to
        orgs = Organization.objects.filter(members=user)
    
    return render(request, "organizations/org_list.html", {"organizations": orgs})


@login_required
def organization_create(request):
    if not request.user.is_system_admin():
        messages.error(request, "Only system administrators can create organizations.")
        return redirect("dashboard")

    form = OrganizationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        org = form.save(commit=False)
        org.created_by = request.user
        org.save()
        log_action(
            actor=request.user,
            action="ORG_CREATED",
            target_type="Organization",
            target_id=org.pk,
            detail=f"Organization '{org.name}' created.",
        )
        messages.success(request, f"Organization '{org.name}' created.")
        return redirect("organizations:org_list")
    return render(request, "organizations/org_form.html", {"form": form, "title": "Create Organization"})


@login_required
def organization_edit(request, pk):
    if not request.user.is_system_admin():
        messages.error(request, "Only system administrators can edit organizations.")
        return redirect("dashboard")

    org = get_object_or_404(Organization, pk=pk)
    form = OrganizationForm(request.POST or None, instance=org)
    if request.method == "POST" and form.is_valid():
        form.save()
        log_action(
            actor=request.user,
            action="ORG_UPDATED",
            target_type="Organization",
            target_id=org.pk,
            detail=f"Organization '{org.name}' updated.",
        )
        messages.success(request, f"Organization '{org.name}' updated.")
        return redirect("organizations:org_list")
    return render(request, "organizations/org_form.html", {"form": form, "title": f"Edit — {org.name}"})


@login_required
def organization_delete(request, pk):
    if not request.user.is_system_admin():
        messages.error(request, "Only system administrators can delete organizations.")
        return redirect("dashboard")

    org = get_object_or_404(Organization, pk=pk)
    if request.method == "POST":
        name = org.name
        org.delete()
        log_action(
            actor=request.user,
            action="ORG_DELETED",
            target_type="Organization",
            target_id=pk,
            detail=f"Organization '{name}' deleted.",
        )
        messages.success(request, f"Organization '{name}' deleted.")
        return redirect("organizations:org_list")
    return render(request, "organizations/org_confirm_delete.html", {"org": org})


@login_required
def organization_members(request, pk):
    if not request.user.is_system_admin():
        messages.error(request, "Only system administrators can manage organization members.")
        return redirect("dashboard")

    org = get_object_or_404(Organization, pk=pk)
    form = OrganizationMembersForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        # Get new members from form and ADD them (don't replace)
        new_members = form.cleaned_data.get("members", [])
        if new_members:
            for member in new_members:
                org.members.add(member)
            log_action(
                actor=request.user,
                action="ORG_MEMBERS_ADDED",
                target_type="Organization",
                target_id=org.pk,
                detail=f"Added {len(new_members)} member(s) to '{org.name}'.",
            )
            messages.success(request, f"Added {len(new_members)} member(s) to '{org.name}'.")
        return redirect("organizations:org_members", pk=org.pk)
    return render(request, "organizations/org_members.html", {"form": form, "org": org})


@login_required
def remove_member(request, pk, user_id):
    if not request.user.is_system_admin():
        messages.error(request, "Only system administrators can manage organization members.")
        return redirect("dashboard")

    org = get_object_or_404(Organization, pk=pk)
    user = get_object_or_404(User, pk=user_id)
    
    if request.method == "POST":
        if user in org.members.all():
            org.members.remove(user)
            log_action(
                actor=request.user,
                action="ORG_MEMBER_REMOVED",
                target_type="Organization",
                target_id=org.pk,
                detail=f"Removed user '{user.username}' from '{org.name}'.",
            )
            messages.success(request, f"Removed '{user.username}' from '{org.name}'.")
        else:
            messages.error(request, f"'{user.username}' is not a member of '{org.name}'.")
    
    return redirect("organizations:org_members", pk=org.pk)
