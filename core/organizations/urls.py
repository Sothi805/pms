from django.urls import path

from . import views

app_name = "organizations"

urlpatterns = [
    path("", views.organization_list, name="org_list"),
    path("create/", views.organization_create, name="org_create"),
    path("<int:pk>/edit/", views.organization_edit, name="org_edit"),
    path("<int:pk>/delete/", views.organization_delete, name="org_delete"),
    path("<int:pk>/members/", views.organization_members, name="org_members"),
    path("<int:pk>/members/remove/<int:user_id>/", views.remove_member, name="remove_member"),
]
