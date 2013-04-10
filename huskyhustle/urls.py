from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.conf import settings

from djangorestframework.resources import ModelResource
from djangorestframework.views import ListOrCreateModelView, InstanceModelView

from husky.views import BlogFeed
from husky.models import Parent, Children, Donation, Teacher, Grade

admin.autodiscover()


class TeacherResource(ModelResource):
    model = Teacher

class GradeResource(ModelResource):
    model = Grade

class ParentResource(ModelResource):
    model = Parent

class ChildrenResource(ModelResource):
    model = Children

class DonationResource(ModelResource):
    model = Donation

urlpatterns = patterns('',
    # Site
    url(r'^$', 'husky.views.index', name='index'),
    url(r'^archive/album/(?P<album_id>\w+)$', 'husky.views.album', name='albums'),
    url(r'^archive/photo/(?P<album_id>\w+)/(?P<photo_id>\w+)$', 'husky.views.photo', name='photo'),
    url(r'^nav/(?P<page>\w+)/*(?P<id>\d+)*$', 'husky.views.nav', name='nav'),
    url(r'^JSON/(?P<child_id>[\w-]+)$', 'husky.views.json', name='json'),
    url(r'^paid/(?P<donation_id>[\w,-]+)$', 'husky.views.paid', name='paid'),
    url(r'^thank_you/*(?P<donation_id>[\w-]+)*$', 'husky.views.thank_you', name='thank_you'),
    url(r'^link/(?P<parent_id>[\w-]+)$', 'husky.views.link', name='link'),
    url(r'^emails/*$', 'husky.views.emails', name='emails'),
    url(r'^reminders/*$', 'husky.views.reminders', name='reminders'),
    url(r'^thanks/*$', 'husky.views.thanks', name='thanks'),
    url(r'^donate/(?P<child_id>[\w-]+)$', 'husky.views.donate', name='donate'),
    url(r'^donate-direct$', 'husky.views.donate_direct', name='donate-direct'),
    url(r'^make-donation/(?P<identifier>[\w-]*)$', 'husky.views.make_donation', name='make-donation'),
    url(r'^payment/(?P<identifier>[\w-]+)/*(?P<id>[\d,]*)$', 'husky.views.payment', name='payment'),
    url(r'^teacher-donation/(?P<identifier>[\w-]*)$', 'husky.views.teacher_donation', name='teacher-donation'),
    url(r'^account/(?P<identifier>[\w-]+)*$', 'husky.views.account', name='account'),
    url(r'^donation_sheet/(?P<identifier>[\w-]+)*/(?P<final>[\w-]+)*$', 'husky.views.donation_sheet', name='donation_sheet'),
    url(r'^accounts/profile/$', 'husky.views.account', name='profile'),
    url(r'^add/(?P<type>[\w]+)*$', 'husky.views.add', name='add'),
    url(r'^edit/(?P<type>[\w]+)*$', 'husky.views.edit', name='edit'),
    url(r'^delete/(?P<type>[\w]+)*$', 'husky.views.delete', name='delete'),
    url(r'^contact/*$', 'husky.views.contact', name='contact'),
    url(r'^register/*$', 'husky.views.register', name='register'),
    url(r'^results/*(?P<type>[\w-]*)$', 'husky.views.results', name='results'),
    url(r'^activate/(?P<key>[\w]+)*$', 'husky.views.activate', name='activate'),
    url(r'^request/(?P<type>[\w]+)/(?P<key>[\w]+)*$', 'husky.views.request', name='request'),
    url(r'^disconnect/(?P<parent_id>[\w]+)/(?P<social>[\w]+)*$', 'husky.views.disconnect', name='disconnect'),

    # override password function
    url(r'^accounts/password/reset/$', 'husky.views.reset', name='password_reset'),
    url(r'^accounts/password/reset/done/$', 'husky.views.reset_done', name='password_reset_done'),
    url(r'^accounts/password/reset/confirm/(?P<uidb36>[0-9A-Za-z]{1,13})-(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', 'husky.views.reset_confirm', name='password_reset_confirm'),
    url(r'^accounts/password/reset/complete/$', 'husky.views.reset_complete', name='password_reset_complete'),

    # account registration
    url(r'^accounts/', include('registration.backends.default.urls')),
    url(r'^social/', include('socialregistration.urls', namespace = 'socialregistration')),

    # rss feed
    url(r'^blog/feed$', BlogFeed()),

    # reports
    url(r'^admin/reporting/(?P<type>[\w-]+)$', 'husky.views.reporting', name='reporting'),
    url(r'^admin/reports/(?P<type>[\w-]+)$', 'husky.views.reports', name='reports'),
    url(r'^admin/results/(?P<type>[\w-]*)$', 'husky.views.results', name='results'),
    url(r'^admin/(?P<type>[\w]+)/calculate_totals/*(?P<id>[\d]*)$', 'husky.views.calculate_totals', name='calculate_totals'),
    url(r'^admin/send_teacher_reports/*(?P<id>[\d,]*)$', 'husky.views.send_teacher_reports', name='send_teacher_reports'),
    url(r'^admin/send_unpaid_reports$', 'husky.views.send_unpaid_reports', name='send_unpaid_reports'),
    url(r'^admin/send_unpaid_reminders/*(?P<type>[\w]*)/*(?P<donation_id>[\d]*)$', 'husky.views.send_unpaid_reminders', name='send_unpaid_reminders'),

    # admin
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),

    # REST API
    url(r'^REST/api-auth/', include('djangorestframework.urls', namespace='djangorestframework')),
    url(r'^REST/teacher/$', ListOrCreateModelView.as_view(resource=TeacherResource)),
    url(r'^REST/teacher/(?P<pk>[^/]+)/$', InstanceModelView.as_view(resource=TeacherResource)),
    url(r'^REST/grade/$', ListOrCreateModelView.as_view(resource=GradeResource)),
    url(r'^REST/grade/(?P<pk>[^/]+)/$', InstanceModelView.as_view(resource=GradeResource)),
    url(r'^REST/parent/$', ListOrCreateModelView.as_view(resource=ParentResource)),
    url(r'^REST/parent/(?P<pk>[^/]+)/$', InstanceModelView.as_view(resource=ParentResource)),
    url(r'^REST/children/$', ListOrCreateModelView.as_view(resource=ChildrenResource)),
    url(r'^REST/children/(?P<identifier>[^/]+)/$', InstanceModelView.as_view(resource=ChildrenResource)),
    url(r'^REST/donation/$', ListOrCreateModelView.as_view(resource=DonationResource)),
    url(r'^REST/donation/(?P<pk>[^/]+)/$', InstanceModelView.as_view(resource=DonationResource))
)
