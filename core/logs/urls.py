from django.urls import path

from . import views

app_name = "logs"

urlpatterns = [
    path("", views.audit_log_list, name="audit_log_list"),
]
