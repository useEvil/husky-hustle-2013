import re as regexp

from django import forms
from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from husky.models import Parent, Children, Content, Blog, Message, Link, Donation, Grade, Teacher


class MostLapsListFilter(SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('Laps View')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = ''

    def lookups(self, request, model_admin):
        return (
            ('laps', _('Most Laps')),
            ('by_laps', _('By Laps')),
            ('no_laps', _('Missing Laps')),
            ('outstanding', _('Outstanding')),
        )
    def queryset(self, request, queryset):
        if self.value() == 'laps':
            return queryset.exclude(laps=None).order_by('-laps').all()
        elif self.value() == 'by_laps':
            return queryset.filter(sponsors__per_lap=True).all()
        elif self.value() == 'no_laps':
            return queryset.filter(laps=None).all()
        elif self.value() == 'outstanding':
            return queryset.filter(sponsors__paid=False).distinct().all()
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
            ('unpaid_lap', _('Unpaid Per Lap')),
            ('unpaid_flat', _('Unpaid Flat')),
            ('perlap', _('Paid Per Lap')),
            ('flat', _('Paid Flat')),
            ('direct', _('Direct')),
        )
    def queryset(self, request, queryset):
        if self.value() == 'unpaid_lap':
            return queryset.filter(paid=False, per_lap=True).order_by('email_address').all()
        elif self.value() == 'unpaid_flat':
            return queryset.filter(paid=False, per_lap=False).order_by('email_address').all()
        elif self.value() == 'perlap':
            return queryset.filter(paid=True, per_lap=True).all()
        elif self.value() == 'flat':
            return queryset.filter(paid=True, per_lap=False).all()
        elif self.value() == 'direct':
            return queryset.filter(child__parents=None).all()
        else:
            return queryset.all()

class ChildrenInline(admin.StackedInline):
    model = Parent.children.through
    extra = 1

class ParentInline(admin.StackedInline):
    model = Parent
    can_delete = False
    verbose_name_plural = 'parents'

class ChildrenAdmin(admin.ModelAdmin):
    fields = ['first_name', 'last_name', 'teacher', 'identifier', 'age', 'gender', 'laps', 'disqualify', 'date_added']
    list_display = ['first_name', 'last_name', 'teacher', 'identifier', 'disqualify', 'gender', 'laps', 'total_for_laps', 'total_due', 'total_got', 'total_raffle_tickets']
#    list_display = ['first_name', 'last_name', 'teacher', 'identifier', 'disqualify', 'gender', 'laps', 'total_for_laps', 'total_for_flat', 'total_due', 'total_got', 'total_raffle_tickets']
    search_fields = ['teacher__last_name', 'first_name', 'last_name', 'parents__first_name', 'parents__last_name', 'teacher__last_name']
    list_editable = ['laps', 'gender', 'disqualify']
    list_filter = [MostLapsListFilter]
    inlines = [ChildrenInline]
    save_on_top = True
    list_per_page = 40

class ParentAdmin(admin.ModelAdmin):
    fields = ['first_name', 'last_name', 'email_address', 'phone_number', 'activation_key', 'default', 'guardian', 'date_added']
    list_display = ['id', 'guardian', 'first_name', 'last_name', 'email_address', 'phone_number', 'user', 'facebook', 'twitter', 'google', 'default', 'num_children']
    list_editable = ['guardian', 'default']
    inlines = [ChildrenInline]
    search_fields = ['email_address', 'first_name', 'last_name']
    save_on_top = True

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
    def total_link(obj):
        if regexp.match('^(_parent_|_teacher_)', obj.email_address):
            return obj.total()
        else:
            return '<a href="%s" target="_email_link">%s</a>' % (obj.payment_url(), obj.total())
    total_link.allow_tags = True
    total_link.short_description = "Total"

    fields = ['child', 'first_name', 'last_name', 'email_address', 'phone_number', 'donation', 'per_lap', 'date_added', 'paid']
    list_display = ['child', 'teacher', 'first_name', 'last_name', 'email_address', 'donation', 'laps', 'per_lap', total_link, 'date_added', 'paid']
    search_fields = ['email_address', 'first_name', 'last_name', 'child__first_name', 'child__last_name', 'child__teacher__last_name']
    list_editable = ['per_lap', 'donation', 'paid']
    list_filter = [MostDonationsListFilter]
    save_on_top = True
    list_per_page = 50


class UserAdmin(UserAdmin):
    list_display = ['username', 'email', 'is_active', 'parent']
    inlines = [ParentInline]

class TeacherInline(admin.StackedInline):
    model = Teacher
    extra = 6
    verbose_name_plural = 'teachers'

class TeacherAdmin(admin.ModelAdmin):
    fields = ['grade', 'list_type', 'title', 'first_name', 'last_name', 'room_number', 'email_address', 'phone_number', 'website']
    list_display = ['grade', 'list_type', 'title', 'last_name', 'room_number', 'email_address', 'get_donations', 'total_students', 'total_participation']
    list_editable = ['list_type', 'last_name', 'room_number', 'email_address']

class GradeAdmin(admin.ModelAdmin):
    fields = ['grade', 'title']
    list_display = ['id', 'grade', 'title', 'total_students', 'total_laps', 'total_donations', 'total_collected', 'percent_completed', 'most_laps_avg', 'most_donations_avg']
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
