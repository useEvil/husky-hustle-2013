from husky.models import Parent, Children, Blog, Message, Donation

from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User


class ChildrenAdmin(admin.ModelAdmin):
    fields = ['parent', 'first_name', 'last_name', 'teacher', 'room_number', 'identifier', 'laps', 'date_added']
    list_display = ['parent', 'first_name', 'last_name', 'teacher', 'room_number', 'identifier', 'laps']
    search_fields = ['teacher', 'first_name', 'last_name', 'room_number', 'parent__first_name', 'parent__last_name']
    list_editable = ['laps']

class ChildrenInline(admin.StackedInline):
    model = Children
    extra = 2

class ParentInline(admin.StackedInline):
    model = Parent
    can_delete = False
    verbose_name_plural = 'parent'

class ParentAdmin(admin.ModelAdmin):
    fields = ['first_name', 'last_name', 'email_address', 'phone_number', 'activation_key', 'date_added']
    list_display = ['id', 'first_name', 'last_name', 'email_address', 'phone_number', 'activation_key', 'user', 'facebook', 'twitter', 'num_chilren']
    inlines = [ChildrenInline]
    search_fields = ['email_address', 'first_name', 'last_name']

class BlogAdmin(admin.ModelAdmin):
    fields = ['title', 'content', 'author', 'date_added']
    list_display = ['title', 'content', 'date_added']

class MessageAdmin(admin.ModelAdmin):
    fields = ['title', 'content', 'author', 'date_added']
    list_display = ['title', 'content', 'date_added']

class DonationAdmin(admin.ModelAdmin):
    fields = ['child', 'first_name', 'last_name', 'email_address', 'phone_number', 'donation', 'per_lap', 'date_added', 'paid']
    list_display = ['child', 'first_name', 'last_name', 'email_address', 'phone_number', 'donation', 'laps', 'per_lap', 'total', 'date_added', 'paid']
    search_fields = ['email_address', 'first_name', 'last_name', 'child__first_name', 'child__last_name']
    list_editable = ['per_lap', 'donation', 'paid']

class UserAdmin(UserAdmin):
    list_display = ['username', 'email', 'is_active', 'parent']
    inlines = [ParentInline]

admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Parent, ParentAdmin)
admin.site.register(Children, ChildrenAdmin)
admin.site.register(Blog, BlogAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(Donation, DonationAdmin)
