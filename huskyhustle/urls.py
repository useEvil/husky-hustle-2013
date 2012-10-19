from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.conf import settings

from djangorestframework.resources import ModelResource
from djangorestframework.views import ListOrCreateModelView, InstanceModelView

from husky.views import BlogFeed
from husky.models import Parent, Children, Donation, Link, Teacher, Grade

admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    url(r'^$', 'husky.views.index', name='index'),
    url(r'^archive/album/(?P<album_id>\w+)$', 'husky.views.album', name='albums'),
    url(r'^archive/photo/(?P<album_id>\w+)/(?P<photo_id>\w+)$', 'husky.views.photo', name='photo'),
    url(r'^nav/(?P<page>\w+)/*(?P<id>\d+)*$', 'husky.views.nav', name='nav'),
    url(r'^JSON/(?P<child_id>[\w-]+)$', 'husky.views.json', name='json'),
    url(r'^paid/(?P<donation_id>[\w-]+)$', 'husky.views.paid', name='paid'),
    url(r'^reminders/*$', 'husky.views.reminders', name='reminders'),
    url(r'^donate/(?P<child_id>[\w-]+)$', 'husky.views.donate', name='donate'),
    url(r'^make-donation/(?P<identifier>[\w-]+)$', 'husky.views.make_donation', name='make-donation'),
    url(r'^teacher-donation/(?P<identifier>[\w-]+)$', 'husky.views.teacher_donation', name='teacher-donation'),
    url(r'^account/(?P<identifier>[\w-]+)*$', 'husky.views.account', name='account'),
    url(r'^donation_sheet/(?P<identifier>[\w-]+)*$', 'husky.views.donation_sheet', name='donation_sheet'),
    url(r'^accounts/profile/$', 'husky.views.account', name='profile'),
    url(r'^add/(?P<type>[\w]+)*$', 'husky.views.add', name='add'),
    url(r'^edit/(?P<type>[\w]+)*$', 'husky.views.edit', name='edit'),
    url(r'^delete/(?P<type>[\w]+)*$', 'husky.views.delete', name='delete'),
    url(r'^contact/*$', 'husky.views.contact', name='contact'),
    url(r'^register/*$', 'husky.views.register', name='register'),
    url(r'^activate/(?P<key>[\w]+)*$', 'husky.views.activate', name='activate'),
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

    # admin
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),

    # reports
    url(r'^admin/reporting/(?P<type>[\w-]+)$', 'husky.views.reporting', name='reporting'),
    url(r'^admin/reports/(?P<type>[\w-]+)$', 'husky.views.reports', name='reports'),

    # REST
    url(r'^api-auth/', include('djangorestframework.urls', namespace='djangorestframework'))
)

class TeacherResource(ModelResource):
    model = Teacher

class GradeResource(ModelResource):
    model = Grade

urlpatterns += patterns('',
    url(r'^$', ListOrCreateModelView.as_view(resource=TeacherResource)),
    url(r'^(?P<pk>[^/]+)/$', InstanceModelView.as_view(resource=TeacherResource)),
)
