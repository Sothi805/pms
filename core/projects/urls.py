from django.urls import path

from . import views

app_name = "projects"

urlpatterns = [
    path("", views.project_list, name="project_list"),
    path("create/", views.project_create, name="project_create"),
    path("<int:pk>/", views.project_detail, name="project_detail"),
    path("<int:pk>/edit/", views.project_edit, name="project_edit"),
    path("notes/<int:pk>/delete/", views.note_delete, name="note_delete"),
    path("<int:project_pk>/categories/create/", views.category_create, name="category_create"),
    path("categories/<int:category_pk>/edit/", views.category_edit, name="category_edit"),
    path("categories/<int:category_pk>/delete/", views.category_delete, name="category_delete"),
    path("categories/<int:category_pk>/move-up/", views.category_move_up, name="category_move_up"),
    path("categories/<int:category_pk>/move-down/", views.category_move_down, name="category_move_down"),
]
