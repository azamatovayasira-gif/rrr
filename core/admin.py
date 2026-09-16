from django.contrib import admin
from .models import ChatMessage, ContactMessage, Friendship, Post, Profile, SharedLocation, Support


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('author', 'created_at', 'image', 'video')
    list_filter = ('created_at',)
    search_fields = ('body', 'tags', 'author__username')


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('pseudonym', 'user', 'location_updated')
    search_fields = ('pseudonym',)


admin.site.register(Friendship)
admin.site.register(SharedLocation)
admin.site.register(Support)
admin.site.register(ContactMessage)
admin.site.register(ChatMessage)
