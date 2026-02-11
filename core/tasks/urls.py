from django.urls import path

from . import views

app_name = "tasks"

urlpatterns = [
    path("board/<int:project_pk>/", views.task_board, name="task_board"),
    path("create/<int:project_pk>/", views.task_create, name="task_create"),
    path("<int:pk>/", views.task_detail, name="task_detail"),
    path("<int:pk>/edit/", views.task_edit, name="task_edit"),
    path("<int:pk>/move/", views.task_move, name="task_move"),
]
