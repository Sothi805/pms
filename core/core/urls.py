from django.contrib import admin
from django.urls import include, path

from dashboard.views import dashboard

urlpatterns = [
    # path("admin/", admin.site.urls),
    path("", dashboard, name="dashboard"),
    path("dashboard/", dashboard, name="dashboard"),
    path("accounts/", include("accounts.urls")),
    path("organizations/", include("organizations.urls")),
    path("projects/", include("projects.urls")),
    path("tasks/", include("tasks.urls")),
    path("general-tasks/", include("general_tasks.urls")),
    path("logs/", include("logs.urls")),
]
