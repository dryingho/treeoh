from django.urls import path

from . import views

app_name = "operator"

urlpatterns = [
    path("login/", views.operator_login, name="login"),
    path("logout/", views.operator_logout, name="logout"),
    path("", views.dashboard, name="dashboard"),
    path("profile/", views.edit_profile, name="edit_profile"),
    path("links/", views.edit_links, name="edit_links"),
    path("projects/", views.edit_projects, name="edit_projects"),
    path("audit/", views.audit_log, name="audit"),
]
