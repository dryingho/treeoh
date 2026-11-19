from django.contrib import admin

from .models import Comment, Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "author_name", "is_notice", "is_scenario_clue", "created_at")
    list_filter = ("is_notice", "is_scenario_clue")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "post", "author_name", "ip_address", "looks_like_script", "created_at")
    list_filter = ("created_at",)
    search_fields = ("body", "author_name", "ip_address")
