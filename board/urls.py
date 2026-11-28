from django.urls import path

from . import views

app_name = "board"

urlpatterns = [
    path("", views.post_list, name="list"),
    path("new/", views.create_post, name="create"),
    path("<int:pk>/", views.post_detail, name="detail"),
    path("<int:pk>/delete/", views.delete_post, name="delete_post"),
    path("<int:pk>/comment/", views.add_comment, name="add_comment"),
    path("comment/<int:pk>/delete/", views.delete_comment, name="delete_comment"),
]
