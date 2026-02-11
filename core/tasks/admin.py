from django.contrib import admin

from .models import TaskInstance, TaskNote


@admin.register(TaskInstance)
class TaskInstanceAdmin(admin.ModelAdmin):
    list_display = ("title", "project", "project_category", "stage", "category", "is_closed", "created_at")
    list_filter = ("project", "project_category", "stage", "category", "is_closed", "created_at")
    search_fields = ("title", "project__name", "project_category__name")
    fieldsets = (
        ("Task Details", {
            "fields": ("title", "description", "project", "project_category"),
        }),
        ("Classification", {
            "fields": ("category", "stage"),
        }),
        ("Assignment", {
            "fields": ("created_by", "assignees"),
        }),
        ("Metrics", {
            "fields": ("story_points", "points_earned", "deadline"),
        }),
        ("Lineage", {
            "fields": ("parent_task", "original_category", "is_closed"),
            "classes": ("collapse",),
        }),
        ("Metadata", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )
    readonly_fields = ("created_at", "updated_at")
    filter_horizontal = ("assignees",)


@admin.register(TaskNote)
class TaskNoteAdmin(admin.ModelAdmin):
    list_display = ("task", "author", "created_at")
    list_filter = ("created_at", "task__project")
    search_fields = ("task__title", "author__username", "content")
    readonly_fields = ("created_at", "updated_at")
