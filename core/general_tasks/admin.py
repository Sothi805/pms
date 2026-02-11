from django.contrib import admin

from .models import GeneralTask


@admin.register(GeneralTask)
class GeneralTaskAdmin(admin.ModelAdmin):
    list_display = ["title", "status", "priority", "assigned_to", "created_by", "created_at"]
    list_filter = ["status", "priority", "created_at"]
    search_fields = ["title", "description"]
    readonly_fields = ["created_at", "updated_at"]
