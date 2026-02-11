from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("settings/", views.settings_view, name="settings"),
    path("users/", views.user_list, name="user_list"),
    path("users/create/", views.user_create, name="user_create"),
    path("users/<int:pk>/edit/", views.user_edit, name="user_edit"),
    path("users/<int:pk>/reset-password/", views.reset_password, name="reset_password"),
    path("users/<int:pk>/set-password/", views.set_user_password, name="set_user_password"),
    path("api/search-users/", views.search_users, name="search_users"),
]
