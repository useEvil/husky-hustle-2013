from husky.models import Parent, Children, Content, Blog, Message, Link, Donation, Grade, Teacher

from django import forms
from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _


class MostLapsListFilter(SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('Laps View')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = ''

    def lookups(self, request, model_admin):
        return (
            ('laps', _('Most Laps')),
        )
    def queryset(self, request, queryset):
        if self.value() == 'laps':
            return queryset.all().order_by('-laps')
        else:
            return queryset.all()

class MostDonationsListFilter(SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('Donation Views')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = ''

    def lookups(self, request, model_admin):
        return (
            ('unpaid', _('Unpaid')),
            ('perlap', _('Per Lap Donations')),
            ('flat', _('Flat Donations')),
            ('direct', _('Direct Donations')),
        )
    def queryset(self, request, queryset):
        if self.value() == 'unpaid':
            return queryset.filter(paid=False).all()
        if self.value() == 'perlap':
            return queryset.filter(per_lap=True).all()
        if self.value() == 'flat':
            return queryset.filter(per_lap=False).all()
        if self.value() == 'direct':
            return queryset.filter(child__parents=None).all()

class ChildrenAdmin(admin.ModelAdmin):
    fields = ['first_name', 'last_name', 'teacher', 'identifier', 'laps', 'date_added']
    list_display = ['first_name', 'last_name', 'teacher', 'identifier', 'laps', 'total_due', 'total_got']
    search_fields = ['teacher__last_name', 'first_name', 'last_name', 'parents__first_name', 'parents__last_name']
    list_editable = ['laps']
    list_filter = [MostLapsListFilter]

class ChildrenInline(admin.StackedInline):
    model = Parent.children.through
    extra = 2

class ParentInline(admin.StackedInline):
    model = Parent
    can_delete = False
    verbose_name_plural = 'parents'

class ParentAdmin(admin.ModelAdmin):
    fields = ['first_name', 'last_name', 'email_address', 'phone_number', 'activation_key', 'default', 'guardian', 'date_added']
    list_display = ['id', 'guardian', 'first_name', 'last_name', 'email_address', 'phone_number', 'user', 'facebook', 'twitter', 'google', 'default', 'num_children']
    list_editable = ['guardian', 'default']
    inlines = [ChildrenInline]
    search_fields = ['email_address', 'first_name', 'last_name']

class ContentModelForm( forms.ModelForm ):
    content = forms.CharField( widget=forms.Textarea(attrs={'cols': 125, 'rows': 50}) )
    class Meta:
        model = Content

class ContentAdmin(admin.ModelAdmin):
    fields = ['page', 'content', 'date_added']
    list_display = ['page', 'content', 'date_added']
    form = ContentModelForm

class BlogAdmin(admin.ModelAdmin):
    fields = ['title', 'content', 'author', 'date_added']
    list_display = ['title', 'content', 'date_added']

class MessageAdmin(admin.ModelAdmin):
    fields = ['title', 'content', 'author', 'date_added']
    list_display = ['title', 'content', 'date_added']

class DonationAdmin(admin.ModelAdmin):
    fields = ['child', 'first_name', 'last_name', 'email_address', 'phone_number', 'donation', 'per_lap', 'date_added', 'paid']
    list_display = ['child', 'teacher', 'first_name', 'last_name', 'email_address', 'phone_number', 'donation', 'laps', 'per_lap', 'total', 'date_added', 'paid']
    search_fields = ['email_address', 'first_name', 'last_name', 'child__first_name', 'child__last_name', 'child__teacher__last_name']
    list_editable = ['per_lap', 'donation', 'paid']
    list_filter = [MostDonationsListFilter]

class UserAdmin(UserAdmin):
    list_display = ['username', 'email', 'is_active', 'parent']
    inlines = [ParentInline]

class TeacherInline(admin.StackedInline):
    model = Teacher
    extra = 6
    verbose_name_plural = 'teachers'

class TeacherAdmin(admin.ModelAdmin):
    fields = ['grade', 'list_type', 'title', 'first_name', 'last_name', 'room_number', 'email_address', 'phone_number', 'website']
    list_display = ['grade', 'list_type', 'title', 'last_name', 'room_number', 'email_address', 'phone_number']
    list_editable = ['list_type', 'last_name', 'room_number', 'phone_number']

class GradeAdmin(admin.ModelAdmin):
    fields = ['grade', 'title']
    list_display = ['id', 'grade', 'title']
    list_editable = ['grade', 'title']
    inlines = [TeacherInline]

class LinkAdmin(admin.ModelAdmin):
    fields = ['title', 'url', 'status']
    list_display = ['title', 'url', 'shorten', 'status']
    list_editable = ['status']

admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Parent, ParentAdmin)
admin.site.register(Children, ChildrenAdmin)
admin.site.register(Content, ContentAdmin)
admin.site.register(Blog, BlogAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(Donation, DonationAdmin)
admin.site.register(Link, LinkAdmin)
admin.site.register(Grade, GradeAdmin)
admin.site.register(Teacher, TeacherAdmin)
