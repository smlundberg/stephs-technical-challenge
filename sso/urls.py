from django.urls import path
from . import views


urlpatterns = [
    path("", views.login, name="login"),
    path("auth", views.auth, name="auth"),
    path("auth/callback", views.auth_callback, name="auth_callback"),
    path("logout", views.logout, name="logout"),

    # new endpoint for explicit organization‑ID login
    path("auth/org", views.auth_org, name="auth_org"),

    # Directory Sync drill-down pages
    path("directory", views.get_directory, name="directory"),
    path("users", views.get_directory_users, name="dir_users"),
    path("groups", views.get_directory_groups, name="dir_groups"),
]


