from django.contrib import admin

from .models import Project, ProjectCategory, ProjectNote


@admin.register(ProjectCategory)
class ProjectCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "project", "weight", "total_tasks", "completion_percentage")
    list_filter = ("project", "created_at")
    search_fields = ("name", "project__name")
    fieldsets = (
        ("Category Details", {
            "fields": ("project", "name", "description", "weight"),
        }),
        ("Metadata", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )
    readonly_fields = ("created_at", "updated_at")


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "progress", "created_by", "created_at")
    list_filter = ("organization", "created_at")
    search_fields = ("name", "organization__name")
    fieldsets = (
        ("Project Details", {
            "fields": ("name", "description", "organization", "created_by"),
        }),
        ("Access Control", {
            "fields": ("members", "commenters", "viewers"),
        }),
        ("Metadata", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )
    readonly_fields = ("created_by", "created_at", "updated_at")
    filter_horizontal = ("members", "commenters", "viewers")


@admin.register(ProjectNote)
class ProjectNoteAdmin(admin.ModelAdmin):
    list_display = ("project", "author", "created_at")
    list_filter = ("project", "created_at")
    search_fields = ("project__name", "author__username", "content")
    readonly_fields = ("created_at", "updated_at")
