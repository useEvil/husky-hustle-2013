import os
import csv
import pytz
import math
import base64
import urllib
import re as regexp
import datetime as date
import husky.bitly as bitly
import gdata.media as media
import gdata.photos.service as gdata
import gdata.calendar.client as cdata

from django.db import models
from django.db.models import Count, Sum, Avg, Max
from django.db.models.signals import post_save
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.sites.models import Site
from django import forms

from paypal import PayPal
from picasa import  PicasaField, PicasaStorage
from decimal import Decimal
from registration.forms import RegistrationForm

from socialregistration.contrib.facebook.models import FacebookProfile
from socialregistration.contrib.twitter.models import TwitterProfile
from socialregistration.contrib.openid.models import OpenIDProfile

from husky.helpers import *

DONATION_GOAL     = 50000
MAX_BAR_LENGTH    = 225
MAX_ARROW_HEIGHT  = 275
BASE_ARROW_HEIGHT = 73
RAFFLE_TICKET_AMT = 25


# Field Classes
class CurrencyField(models.DecimalField):

    def __init__(self, *args, **kwargs):
        kwargs['max_digits'] =  10
        kwargs['decimal_places'] = 2
        super(CurrencyField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        try:
            return super(CurrencyField, self).to_python(value).quantize(Decimal('0.01'))
        except AttributeError:
            return None


# Google Classes
class GoogleCalendarConnect(object):

    gd_client = cdata.CalendarClient(source=settings.PICASA_STORAGE_OPTIONS['source'])
    gd_client.ClientLogin(settings.PICASA_STORAGE_OPTIONS['email'], settings.PICASA_STORAGE_OPTIONS['password'], gd_client.source)

    def client(self):
        return self.gd_client


class GooglePhotoConnect(object):

    gd_client = gdata.PhotosService()
    gd_client.email = settings.PICASA_STORAGE_OPTIONS['email']
    gd_client.password = settings.PICASA_STORAGE_OPTIONS['password']
    gd_client.source = settings.PICASA_STORAGE_OPTIONS['source']
    gd_client.ProgrammaticLogin()

    def client(self):
        return self.gd_client


class Calendar(object):

    gd_client = GoogleCalendarConnect().client()

    def get_events(self):
        query = cdata.CalendarEventQuery()
        query.start_min = date.datetime.now().strftime('%Y-%m-%d')
#        query.start_max = (date.datetime.now() + date.timedelta(days=14)).strftime('%Y-%m-%d')
        feed = self.gd_client.GetCalendarEventFeed(q=query, visibility='public', sortorder='ascending', orderby='starttime')
        return feed


class Photo(object):

    gd_client = GooglePhotoConnect().client()

    def get_photo(self, album_id=None, photo_id=None):
        if not photo_id or not photo_id: return
        photo = self.gd_client.GetFeed('/data/feed/api/user/default/albumid/%s/photoid/%s' % (album_id, photo_id))
        return photo

    def get_photos(self, album_id=None):
        if not album_id: return
        photos = self.gd_client.GetFeed('/data/feed/api/user/default/albumid/%s?kind=photo' % (album_id))
        return photos

    def get_photos_by_tags(self, tags='huskyhustle'):
        photos = self.gd_client.GetFeed('/data/feed/api/all?kind=photo&tag=%s' % (tags))
        return photos


class Album(object):

    gd_client = GooglePhotoConnect().client()

    def get_album(self, album_id=None):
        if not album_id: return
        photos = Photo().get_photos(album_id)
        return photos

    def get_albums(self):
        albums = self.gd_client.GetUserFeed(user=settings.PICASA_STORAGE_OPTIONS['userid'])
        return albums


# Create your models here.
class Content(models.Model):

    page = models.CharField(max_length=100)
    content = models.TextField(max_length=65000, blank=True, null=True)
    date_added = models.DateTimeField(default=date.datetime.now())


class Blog(models.Model):

    title = models.CharField(max_length=100)
    author = models.ForeignKey(User)
    content = models.TextField(max_length=4000)
    date_added = models.DateTimeField(default=date.datetime.now())


class Message(models.Model):

    title = models.CharField(max_length=100)
    author = models.ForeignKey(User)
    content = models.TextField(max_length=4000)
    date_added = models.DateTimeField(default=date.datetime.now())


class Link(models.Model):

    title = models.CharField(max_length=50)
    url = models.CharField(max_length=255)
    shorten = models.CharField(max_length=255)
    status = models.IntegerField(blank=True, null=True, choices=((0,0), (1,1)))

    def __unicode__(self):
        return self.title

    def shortened(self):
        if not self.shorten:
            api = bitly.Api(login=settings.BITLY_LOGIN, apikey=settings.BITLY_APIKEY)
            self.shorten = api.shorten(self.url)
            self.save()
        return self.shorten


class Grade(models.Model):

    grade = models.IntegerField(blank=True, null=True)
    title = models.CharField(max_length=15)

    def __unicode__(self):
        return self.title

    def get_all(self):
        return Grade.objects.exclude(grade=-1).all()

    def most_donations_avg(self):
        avg = self.total_collected() / self.total_students()
        return round(avg, 2)

    def most_laps_avg(self):
        avg = float(self.total_laps()) / self.total_students()
        return round(avg, 2)

    def total_students(self):
        return Children.objects.filter(teacher__grade=self).count()

    def total_laps(self):
        results = Children.objects.filter(teacher__grade=self).exclude(disqualify=True).aggregate(num_laps=Sum('laps'))
        return results['num_laps'] or 0

    def total_donations(self):
        results = Donation.objects.filter(child__teacher__grade=self).aggregate(total_donations=Sum('donated'))
        return float(results['total_donations'] or 0)

    def total_collected(self):
        results = Children.objects.filter(teacher__grade=self).aggregate(total_collected=Sum('collected'))
        return float(results['total_collected'] or 0)

    def percent_completed(self):
        percentage = 0
        if self.total_collected() and self.total_donations():
            percentage = self.total_collected() / self.total_donations()
        return round(percentage, 3)


class Teacher(models.Model):

    title = models.CharField(max_length=5, choices=(('Mrs.', 'Mrs.'), ('Ms.', 'Ms.'), ('Miss', 'Miss'), ('Mr.', 'Mr.')), default='Mrs.')
    first_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50)
    email_address = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=25, blank=True, null=True, default='(714) 734-1878')
    room_number = models.CharField(max_length=5)
    website = models.CharField(max_length=255, blank=True, null=True)
    shorten = models.CharField(max_length=255, blank=True, null=True)
    grade = models.ForeignKey(Grade, related_name='teachers')
    list_type = models.IntegerField(blank=True, null=True)
    class Meta:
        ordering = ['last_name', 'first_name']

    def __unicode__(self):
        return '%s (%s) %s' % (self.full_name(), self.room_number, self.grade)

    def full_name(self):
        return '%s %s %s' % (self.title, self.first_name, self.last_name)

    def find(self, last_name=None):
        try:
            return Teacher.objects.filter(last_name__icontains=last_name).all()
        except ObjectDoesNotExist, e:
            return

    def total_students(self, exclude=None):
        if exclude and exclude == 1:
            return Children.objects.filter(teacher=self, laps__gt=0).exclude(disqualify=True).count()
        elif exclude and exclude == 2:
            return Children.objects.filter(teacher=self, collected__gt=0).count()
        else:
            return Children.objects.filter(teacher=self).count()

    def total_participation(self):
        return Children.objects.filter(teacher=self, collected__gt=0).count()

    def get_all(self):
        return Teacher.objects.exclude(grade__grade=-1).all()

    def get_donate_list(self):
        return Teacher.objects.exclude(list_type=2).order_by('grade','room_number').all()

    def get_list(self):
        return Teacher.objects.exclude(list_type=3).order_by('grade','room_number').all()

    def get_donations(self):
        total = Donation.objects.filter(child__teacher=self).aggregate(donated=Sum('donated'))
        return float(total['donated'] or 0)

    def get_donations_list(self):
        donators = []
        sponsors = []
        children = Children.objects.filter(teacher=self).all()
        for child in children:
            donation = child.total_sum()
            donators.append({'name': child.list_name(), 'total': float(donation['total_sum'] or 0)})
        donations = Donation.objects.filter(first_name__contains=self.last_name)
        totals = { }
        for index, donation in enumerate(donations):
            full_name = donation.child.list_name()
            if totals.has_key(full_name):
                totals[full_name] += donation.donated or 0
            else:
                totals[full_name] = donation.donated or 0
        for child, total in iter(sorted(totals.iteritems())):
            sponsors.append({'name': child, 'total': float(total or 0)})
        return donators, sponsors

    def shortened(self):
        if not self.shorten:
            api = bitly.Api(login=settings.BITLY_LOGIN, apikey=settings.BITLY_APIKEY)
            self.shorten = api.shorten(self.website)
            self.save()
        return self.shorten

    def reports_url(self):
        site = Site.objects.get_current()
        reports_url = 'http://%s/admin/results/donations-by-teacher?id=%s' % (site.domain, self.id)
        return reports_url


class Children(models.Model):

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    identifier = models.CharField(max_length=100, unique=True)
    date_added = models.DateTimeField(default=date.datetime.now())
    laps = models.IntegerField(blank=True, null=True)
    age = models.IntegerField(blank=True, null=True)
    gender = models.CharField(max_length=1, blank=True, null=True, choices=(('M', 'Boy'), ('F', 'Girl')))
    collected = CurrencyField(blank=True, null=True)
    disqualify = models.IntegerField(default=0, choices=((0, 'No'), (1, 'Yes')))
    pledged = CurrencyField(blank=True, null=True)
    teacher = models.ForeignKey(Teacher, related_name='students')
    class Meta:
        ordering = ['last_name', 'first_name']

    def __unicode__(self):
        return self.list_name()

    def list_name(self):
        return '%s, %s' % (self.last_name, self.first_name)

    def full_name(self):
        return '%s %s' % (self.first_name, self.last_name)

    def find(self, parent_only=None, first_name=None, last_name=None):
        try:
            if parent_only == '1':
                if first_name and last_name:
                    return Children.objects.filter(parents__first_name__icontains=first_name, parents__last_name__icontains=last_name).distinct().all()
                elif first_name:
                    return Children.objects.filter(parents__first_name__icontains=first_name).distinct().all()
                elif last_name:
                    return Children.objects.filter(parents__last_name__icontains=last_name).distinct().all()
            else:
                if first_name and last_name:
                    return Children.objects.filter(first_name__icontains=first_name, last_name__icontains=last_name).distinct().all()
                elif first_name:
                    return Children.objects.filter(first_name__icontains=first_name).distinct().all()
                elif last_name:
                    return Children.objects.filter(last_name__icontains=last_name).distinct().all()
        except ObjectDoesNotExist, e:
            return

    def get_collected_list(self):
        return Children.objects.filter(collected__gt=0).order_by('-collected').all()

    def donate_url(self):
        site = Site.objects.get_current()
        donate_url = 'http://%s/make-donation/%s' % (site.domain, self.identifier)
        return donate_url

    def manage_url(self):
        site = Site.objects.get_current()
        manage_url = 'http://%s/account/%s' % (site.domain, self.identifier)
        return manage_url

    def facebook_share_url(self):
        site = Site.objects.get_current()
        params = 'app_id=' + settings.FACEBOOK_APP_ID + '&link=' + self.donate_url() + '&picture=' + ('http://%s/static/images/hickslogo-1.jpg' % site.domain) + '&name=' + urllib.quote('Husky Hustle') + '&caption=' + urllib.quote('Donate to %s' % self.full_name()) + '&description=' + urllib.quote("Donate and help further our children's education.") + '&redirect_uri=' + 'http://%s/' % site.domain
        share_url = 'https://www.facebook.com/dialog/feed?' + params
        return share_url

    def twitter_share_url(self):
        share_url = 'https://twitter.com/intent/tweet?button_hashtag=HuskyHustle&url=%s' % self.donate_url()
        return share_url

    def google_share_url(self):
        share_url = 'https://plus.google.com/share?url=%s' % self.donate_url()
        return share_url

    def grades(self):
        return Grade.objects.all()

    def teachers(self):
        return Teacher.objects.filter(grade=self.teacher.grade).all()

    def donations(self):
        return Donation.objects.filter(child=self).count()

    def sponsors_flat(self):
        return Donation.objects.filter(child=self, per_lap=False).exclude(last_name='teacher').all()

    def sponsors_perlap(self):
        return Donation.objects.filter(child=self, per_lap=True).all()

    def sponsors_teacher(self):
        return Donation.objects.filter(child=self, last_name='teacher').all()

    def sponsored_principle(self):
        try:
            return Donation.objects.filter(child=self, first_name='Mrs. Agopian').get()
        except ObjectDoesNotExist, e:
            return

    def parent(self):
        try:
            return self.parents.filter(parentchildren__default=1).get()
        except ObjectDoesNotExist, e:
            return

    def is_default(self, parent):
        return ParentChildren.objects.filter(children=self, parent=parent).get().default

    def has_parents(self):
        return ParentChildren.objects.filter(children=self).all()

    def total_sum(self):
        return Donation.objects.filter(child=self).aggregate(total_sum=Sum('donated'))

    def total_for_laps(self):
        total_due = 0
        for sponsor in self.sponsors_perlap():
            total_due += sponsor.total()
        return total_due

    def total_for_flat(self):
        total_due = 0
        for sponsor in self.sponsors_flat():
            total_due += sponsor.total() 
        return total_due

    def total_for_sponsors(self):
        total_due = 0
        for sponsor in self.sponsors_teacher():
            total_due += sponsor.total()
        return total_due

    def total_raffle_tickets(self):
        tickets = int(self.collected / RAFFLE_TICKET_AMT)
        return tickets

    def total_due(self):
        total_due = 0
        for sponsor in self.sponsors_flat():
            if not sponsor.paid:
                total_due += sponsor.total() 
        for sponsor in self.sponsors_perlap():
            if not sponsor.paid:
                total_due += sponsor.total()
        for sponsor in self.sponsors_teacher():
            if not sponsor.paid:
                total_due += sponsor.total()
        return total_due

    def total_got(self):
        total_got = 0
        for sponsor in self.sponsors_flat():
            if sponsor.paid:
                total_got += sponsor.total()
        for sponsor in self.sponsors_perlap():
            if sponsor.paid:
                total_got += sponsor.total()
        for sponsor in self.sponsors_teacher():
            if sponsor.paid:
                total_got += sponsor.total()
        return total_got

    def grand_totals(self):
        total_due = self.total_due()
        total_got = self.total_got()
        return [total_got, total_due, (total_due + total_got)]

    def calculate_totals(self, id=None):
        if id:
            total_collected = 0
            total_pledged = 0
            child = Children.objects.get(pk=id)
            for sponsor in child.sponsors.all():
                total_pledged += sponsor.total() or 0
                if sponsor.paid:
                    total_collected += sponsor.total() or 0
            self.collected = total_collected
            self.pledged = total_pledged
            self.save()
        else:
            children = Children.objects.all()
            for child in children:
                total_collected = 0
                total_pledged = 0
                for sponsor in child.sponsors.all():
                    total_pledged += sponsor.total() or 0
                    if sponsor.paid:
                        total_collected += sponsor.total() or 0
                child.collected = total_collected
                child.pledged = total_pledged
                child.save()


class Parent(models.Model):

    GUARDIAN_CHOICES = ((1,'Mother'), (2,'Father'), (3,'Guardian'))

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email_address = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=25, blank=True, null=True)
    default = models.BooleanField(default=1)
    guardian = models.IntegerField(default=1, choices=GUARDIAN_CHOICES)
    activation_key = models.CharField(max_length=200)
    key_expires = models.DateTimeField()
    date_added = models.DateTimeField(default=date.datetime.now())
    site = models.ForeignKey(Site)
    user = models.OneToOneField(User, unique=True)
    children = models.ManyToManyField(Children, related_name='parents', through='ParentChildren')
    class Meta:
        ordering = ['last_name', 'first_name']

    def __unicode__(self):
        return '%s (%s)' % (self.full_name(), self.email_address)

    def full_name(self):
        return '%s %s' % (self.first_name, self.last_name)

    def get_my_children(self):
        return Children.objects.filter(parent=self, parentchildren__default=1).all()

    def activate_url(self):
        site = Site.objects.get_current()
        activate_url = 'http://%s/activate/%s' % (site.domain, self.activation_key)
        return activate_url

    def link_url(self, request_id=None):
        if not request_id: request_id = self.id
        site = Site.objects.get_current()
        link_url = 'http://%s/link/%s' % (site.domain, request_id)
        return link_url

    def links(self):
        try:
            child = self.children.all()[0]
        except IndexError:
            return None
        try:
            return child.parents.exclude(pk=self.id).all()
        except ObjectDoesNotExist, e:
            return None

    def num_children(self):
        return self.children.count()

    def facebook(self, user_id=None):
        if not user_id:
            user_id = self.user.id
        try:
            facebook = FacebookProfile.objects.filter(user_id=user_id).get()
        except ObjectDoesNotExist, e:
            return
        return facebook

    def twitter(self, user_id=None):
        if not user_id:
            user_id = self.user.id
        try:
            twitter = TwitterProfile.objects.filter(user_id=user_id).get()
        except ObjectDoesNotExist, e:
            return
        return twitter

    def google(self, user_id=None):
        if not user_id:
            user_id = self.user.id
        try:
            google = OpenIDProfile.objects.filter(user_id=user_id).get()
        except ObjectDoesNotExist, e:
            return
        return google.identity and True or False

    def is_fathter(self):
        return self.guardian == 0

    def is_mother(self):
        return self.guardian == 1

    def is_guardian(self):
        for choice in self.GUARDIAN_CHOICES:
            if choice[0] == self.guardian:
                return choice[1]

    def has_child(self, child=None):
        try:
            ParentChildren.objects.filter(parent=self, children=child).get()
            return 1
        except ObjectDoesNotExist, e:
            return 0


class ParentChildren(models.Model):
    parent = models.ForeignKey(Parent)
    children = models.ForeignKey(Children)
    default = models.BooleanField(default=1)


class Donation(models.Model):

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email_address = models.CharField(max_length=100, default='_parent_@huskyhustle.com')
    phone_number = models.CharField(max_length=25, blank=True, null=True)
    child = models.ForeignKey(Children, related_name='sponsors')
    donation = CurrencyField(blank=True, null=True)
    donated = CurrencyField(blank=True, null=True)
    per_lap = models.BooleanField()
    paid = models.BooleanField(default=True)
    date_added = models.DateTimeField(default=date.datetime.now())
    class Meta:
        ordering = ['last_name', 'first_name']

    def __unicode__(self):
        return self.full_name()

    def full_name(self):
        return '%s %s' % (self.first_name, self.last_name)

    def laps(self):
        return self.child.laps or 0

    def teacher(self):
        return self.child.teacher or ''

    def total(self):
        if self.per_lap:
           amount = self.donation * (self.child.laps or 0)
           return CurrencyField().to_python(amount)
        else:
            return self.donation

    def bar_height(self):
        try:
            results = Donation.objects.all().aggregate(donated=Sum('donated'))
            total   = results['donated'] or 0
            percentage = total / DONATION_GOAL
            return int(MAX_BAR_LENGTH * percentage)
        except:
            return 0

    def arrow_height(self):
        try:
            results = Donation.objects.filter(paid=True).aggregate(donated=Sum('donated'))
            total   = results['donated'] or 0
            percentage = total / DONATION_GOAL
            return int((MAX_ARROW_HEIGHT * percentage) + BASE_ARROW_HEIGHT)
        except:
            return BASE_ARROW_HEIGHT

    def get_donations(self, children, limit=30, offset=0, query=None, field='id', sortname='id', sortorder='asc'):
        results = []
        try:
            limited = int(limit) + int(offset)
            if sortorder == 'desc':
                sortname = '-%s'%sortname
            if query:
                if field == 'last_name':
                    results = Donation.objects.filter(child__identifier__in=children, last_name__contains=query).order_by(sortname)[offset:limited]
                elif field == 'first_name':
                    results = Donation.objects.filter(child__identifier__in=children, first_name__contains=query).order_by(sortname)[offset:limited]
                elif field == 'email_address':
                    results = Donation.objects.filter(child__identifier__in=children, email_address__contains=query).order_by(sortname)[offset:limited]
                elif field == 'phone_number':
                    results = Donation.objects.filter(child__identifier__in=children, phone_number__contains=query).order_by(sortname)[offset:limited]
                else:
                    results = Donation.objects.filter(child__identifier__in=children, id=query).order_by(sortname)[offset:limited]
            else:
                results = Donation.objects.filter(child__identifier__in=children).order_by(sortname)[offset:limited]
        except Exception, e:
            pass
        return results

    def get_donations_total(self, children, query=None, field='id'):
        try:
            if query:
                if field == 'last_name':
                    return Donation.objects.filter(child__identifier__in=children, last_name__contains=query).count()
                elif field == 'first_name':
                    return Donation.objects.filter(child__identifier__in=children, first_name__contains=query).count()
                elif field == 'email_address':
                    return Donation.objects.filter(child__identifier__in=children, email_address__contains=query).count()
                elif field == 'phone_number':
                    return Donation.objects.filter(child__identifier__in=children, phone_number__contains=query).count()
                else:
                    return Donation.objects.filter(child__identifier__in=children, id=query).count()
            else:
                return Donation.objects.filter(child__identifier__in=children).count()
        except:
            return 0

    def get_reminders(self, parent_id=None):
        try:
            return Donation.objects.filter(child__parent=parent_id, paid=False).all()
        except Exception, e:
            return [parent_id, str(e)]

    def get_reminders_total(self, parent_id=None):
        try:
            return Donation.objects.filter(child__parent=parent_id, paid=False).count()
        except Exception, e:
            return 0

    def get_total(self, ids=None):
        try:
            donation = Donation.objects.filter(id__in=ids).aggregate(total=Sum('donated'))
            return donation['total']
        except Exception, e:
            return 0

    def reports_totals_by_grade(self):
        json = {'label': [], 'values': []}
        grades = Grade.objects.all()
        for index, grade in enumerate(grades):
            json['values'].append({'label': grade.title, 'values': [], 'labels': []})
            json['values'][index]['values'].append(grade.total_collected())
            json['values'][index]['labels'].append('Laps: %d; Donations' % grade.total_laps())
        return json

    def reports_most_laps_by_grade(self):
        json = {'label': [], 'values': []}
        grades = Grade.objects.all()
        for index, grade in enumerate(grades):
            json['values'].append({'label': grade.title, 'values': [], 'labels': []})
            teachers = Teacher.objects.filter(grade=grade).exclude(list_type=3).all()
            laps = { }
            for teacher in teachers:
                num_laps = Children.objects.filter(teacher=teacher, laps__gt=0).exclude(disqualify=True).aggregate(num_laps=Sum('laps'))
                laps[teacher.full_name()] = num_laps['num_laps'] or 0
            for key, value in sorted(laps.iteritems(), key=lambda (v,k): (k,v), reverse=True):
                json['values'][index]['values'].append(value)
                json['values'][index]['labels'].append(key)
        return json

    def reports_most_laps_by_grade_avg(self):
        json = {'label': [], 'values': []}
        grades = Grade.objects.all()
        for index, grade in enumerate(grades):
            json['values'].append({'label': grade.title, 'values': [], 'labels': []})
            teachers = Teacher.objects.filter(grade=grade).exclude(list_type=3).all()
            laps = { }
            for teacher in teachers:
                results  = Children.objects.filter(teacher=teacher, laps__gt=0).exclude(disqualify=True).aggregate(num_laps=Sum('laps'))
                students = teacher.total_students(1)
                avg_laps = 0
                if results['num_laps'] and students:
                    avg_laps = float(results['num_laps']) / students
                laps[teacher.full_name()] = round(avg_laps, 2)
            for key, value in sorted(laps.iteritems(), key=lambda (v,k): (k,v), reverse=True):
                json['values'][index]['values'].append(value)
                json['values'][index]['labels'].append(key)
        return json

    def reports_most_laps_by_child_by_grade(self, gender=None):
        json = {'label': [], 'values': []}
        grades = Grade.objects.all()
        for index, grade in enumerate(grades):
            json['values'].append({'label': grade.title, 'values': [], 'labels': []})
            if gender:
                children = Children.objects.filter(teacher__grade=grade, gender=gender, laps__gt=0).exclude(disqualify=True).annotate(max_laps=Max('laps')).order_by('-laps')[:20]
            else:
                children = Children.objects.filter(teacher__grade=grade, laps__gt=0).exclude(disqualify=True).annotate(max_laps=Max('laps')).order_by('-laps')[:20]
            for child in children:
                json['values'][index]['values'].append(child.max_laps or 0)
                json['values'][index]['labels'].append(child.full_name())
        return json

    def reports_most_donations_by_grade(self):
        json = {'label': [], 'values': []}
        grades = Grade.objects.all()
        for index, grade in enumerate(grades):
            json['values'].append({'label': grade.title, 'values': [], 'labels': []})
            teachers = Teacher.objects.filter(grade=grade).exclude(list_type=3).all()
            totals = { }
            for teacher in teachers:
                results = Children.objects.filter(teacher=teacher).aggregate(total_collected=Sum('collected'))
                totals[teacher.full_name()] = float(results['total_collected'] or 0)
            for key, value in sorted(totals.iteritems(), key=lambda (v,k): (k,v), reverse=True):
                json['values'][index]['values'].append(value)
                json['values'][index]['labels'].append(key)
        return json

    def reports_most_donations_by_grade_avg(self):
        json = {'label': [], 'values': []}
        grades = Grade.objects.all()
        for index, grade in enumerate(grades):
            json['values'].append({'label': grade.title, 'values': [], 'labels': []})
            teachers = Teacher.objects.filter(grade=grade).exclude(list_type=3).all()
            totals = { }
            for teacher in teachers:
                results = Children.objects.filter(teacher=teacher).aggregate(total_collected=Sum('collected'))
                students = teacher.total_students()
                total_collected = 0
                if results['total_collected'] and students:
                    total_collected = results['total_collected'] / students
                totals[teacher.full_name()] = round(total_collected, 2)
            for key, value in sorted(totals.iteritems(), key=lambda (v,k): (k,v), reverse=True):
                json['values'][index]['values'].append(value)
                json['values'][index]['labels'].append(key)
        return json

    def reports_most_donations_by_day_by_sponsor(self):
        json = {'label': [], 'values': []}
        now = date.datetime.now(pytz.utc)
        for index in range(1, 11):
            end = date.datetime(now.year, now.month, now.day, 23, 59, 59, 0, pytz.utc) - date.timedelta(index-1)
            start = date.datetime(now.year, now.month, now.day, 23, 59, 59, 0, pytz.utc) - date.timedelta(index)
            json['values'].append({'label': end.strftime('%m/%d/%Y'), 'values': [], 'labels': []})
            results = Donation.objects.filter(date_added__range=(start, end)).exclude(last_name='teacher').order_by('-donated')
            for result in results:
                json['values'][index-1]['values'].append(float(result.donated or 0))
                json['values'][index-1]['labels'].append('<span id="%d">%s (%s)</span>'%(result.id, result.full_name(), result.child))
        return json

    def reports_most_donations_by_day(self):
        json = {'label': [], 'values': []}
        donated = Donation.objects.aggregate(donated=Sum('donated'))
        collected = Children.objects.aggregate(collected=Sum('collected'))
        json['values'].append({'label': 'Pledged', 'values': [float(donated['donated'] or 0)], 'labels': ['Total Pledged']})
        json['values'].append({'label': 'Collected', 'values': [float(collected['collected'] or 0)], 'labels': ['Total Collected']})
        now = date.datetime.now(pytz.utc)
        for index in range(2, 12):
            end = date.datetime(now.year, now.month, now.day, 23, 59, 59, 0, pytz.utc) - date.timedelta(index-1)
            start = date.datetime(now.year, now.month, now.day, 23, 59, 59, 0, pytz.utc) - date.timedelta(index)
            json['values'].append({'label': end.strftime('%m/%d/%Y'), 'values': [], 'labels': []})
            results = Donation.objects.filter(date_added__range=(start, end)).aggregate(donated=Sum('donated'))
            json['values'][index]['values'].append(float(results['donated'] or 0))
            json['values'][index]['labels'].append(start.strftime('%m/%d/%Y'))
        return json

    def reports_most_donations_by_child_by_grade(self):
        json = {'label': [], 'values': []}
        grades = Grade.objects.all()
        for index, grade in enumerate(grades):
            json['values'].append({'label': grade.title, 'values': [], 'labels': []})
            children = Children.objects.filter(teacher__grade=grade).annotate(max_funds=Max('collected')).order_by('-collected')[:20]
            for child in children:
                json['values'][index]['values'].append(float(child.collected or 0))
                json['values'][index]['labels'].append(child.full_name())
        return json

    def reports_most_donations_by_child(self):
        json = {'label': [], 'values': []}
        children = Children.objects.annotate(max_funds=Max('collected')).order_by('-collected')[:20]
        for child in children:
            json['values'].append({'label': child.id, 'values': [float(child.max_funds or 0)], 'labels': [child.full_name()]})
        return json

    def reports_most_donations_by_child_pledged(self):
        json = {'label': [], 'values': []}
        children = Children.objects.annotate(max_funds=Max('pledged')).order_by('-pledged')[:20]
        for child in children:
            json['values'].append({'label': child.id, 'values': [float(child.max_funds or 0)], 'labels': [child.full_name()]})
        return json

    def reports_donations_by_teacher(self, id=0):
        json = {'label': [], 'values': []}
        if id == 0:
            donation = Donation.objects.filter(first_name__contains='Agopian').aggregate(donated=Sum('donated'))
            if donation:
                json['values'].append({'label': 0, 'values': [float(donation['donated'] or 0)], 'labels': ['Mrs. Agopian']})
            teachers = Teacher.objects.exclude(list_type=3).all()
            for index, teacher in enumerate(teachers):
                donation = teacher.get_donations()
                if donation:
                    json['values'].append({'label': teacher.id, 'values': [donation], 'labels': [teacher.full_name()]})
        else:
            teacher = Teacher.objects.filter(id=id).get()
            children = Children.objects.filter(teacher=teacher).all()
            json['values'].append({'label': 'Donations', 'values': [], 'labels': []})
            for child in children:
                donation = child.total_sum()
                if donation['total_sum']:
                    json['values'][0]['values'].append(float(donation['total_sum'] or 0))
                    json['values'][0]['labels'].append(child.full_name())
            donations = Donation.objects.filter(first_name__contains=teacher.last_name).order_by('-donated')
            json['values'].append({'label': 'Sponsors', 'values': [], 'labels': []})
            totals = { }
            for index, donation in enumerate(donations):
                full_name = donation.child.full_name()
                if totals.has_key(full_name):
                    totals[full_name] += donation.donated or 0
                else:
                    totals[full_name] = donation.donated or 0
            for child, total in totals.iteritems():
                json['values'][1]['values'].append(float(total or 0))
                json['values'][1]['labels'].append(child)
        return json

    def reports_unpaid_donations(self):
        data = []
        total_donated = 0
        donations = Donation.objects.exclude(paid=1).order_by('child__teacher__last_name', 'child__last_name', 'child__first_name')
        for index, donation in enumerate(donations):
            total_donated += donation.total() or 0
            data.append({'id': index+1, 'date': donation.date_added, 'teacher': donation.child.teacher, 'parent': donation.child.parent, 'child': donation.child, 'name': donation.full_name(), 'donation': donation.donation or 0, 'type': donation.per_lap and 'Per Lap' or 'Flat', 'total': donation.total() or 0, 'paid': donation.paid and 'Yes' or 'No'})
        data.append({'id': '&nbsp;', 'date': 'Total', 'parent': '&nbsp;', 'child': '&nbsp;', 'teacher': '&nbsp;', 'name': '&nbsp;', 'donation': None, 'total': total_donated, 'paid': '&nbsp;'})
        return data

    def verify_paypal_donations(self, grade=None):
        data = []
        count = 0
        total_paid = 0
        total_donated = 0
        cwd = os.path.dirname(os.path.realpath(__file__))
        PAYPAL_CSV_REPORT = os.path.join(cwd, settings.PAYPAL_CSV_REPORT)
        with open(PAYPAL_CSV_REPORT, 'rb') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            fields = []
            for index, row in enumerate(csv_reader):
                if index == 0:
                    for r in row: fields.append(r.strip())
                    continue
                row = dict(zip(fields, row))
                ids = row['Item ID'].split('-')[-1]
                if regexp.match('[0-9.,]+', ids):
                    total_paid += float(row['Gross'])
                    for id in ids.split(','):
                        count += 1
                        try:
                            donation = Donation.objects.filter(id=id).get()
                            if not grade or donation.child.teacher.grade.title == grade:
                                total_donated += donation.donated or 0
                                data.append({'id': count, 'date': row['Date'], 'parent': donation.child.parent, 'child': donation.child, 'teacher': donation.child.teacher, 'name': row['Name'], 'emnail': row['From Email Address'], 'item': row['Item ID'], 'gross': row['Gross'], 'donation': donation.donated or 0, 'paid': donation.paid and 'Yes' or 'No'})
                        except:
                            data.append({'id': count, 'date': row['Date'], 'parent': 'N/A', 'child': 'N/A', 'teacher': 'N/A', 'name': row['Name'], 'emnail': row['From Email Address'], 'item': row['Item ID'], 'gross': row['Gross'], 'donation': 'N/A', 'paid': 'N/A'})
                else:
                    count += 1
                    try:
                        names = row['Name'].split()
                        donation = Donation.objects.filter(first_name=names[0], last_name=names[1]).get()
                        if not grade or donation.child.teacher.grade.title == grade:
                            total_donated += donation.donated or 0
                            data.append({'id': count, 'date': row['Date'], 'parent': donation.child.parent, 'child': donation.child, 'teacher': donation.child.teacher, 'name': row['Name'], 'emnail': row['From Email Address'], 'item': row['Item ID'], 'gross': row['Gross'], 'donation': donation.donated or 0, 'paid': donation.paid and 'Yes' or 'No'})
                    except:
                        data.append({'id': count, 'date': row['Date'], 'parent': 'N/A', 'child': 'N/A', 'teacher': 'N/A', 'name': row['Name'], 'emnail': row['From Email Address'], 'item': row['Item ID'], 'gross': row['Gross'], 'donation': 'N/A', 'paid': 'N/A'})
        data.append({'id': '&nbsp;', 'date': 'Total', 'parent': '&nbsp;', 'child': '&nbsp;', 'teacher': '&nbsp;', 'name': '&nbsp;', 'emnail': '&nbsp;', 'item': '&nbsp;', 'gross': total_paid, 'donation': total_donated, 'paid': '&nbsp;'})
        return data

    def calculate_totals(self, id=None):
        if id:
            result = Donation.objects.get(pk=id)
            result.donated = result.total()
            result.save()
        else:
            results = Donation.objects.all()
            for result in results:
                result.donated = result.total()
                result.save()

    def thank_you_url(self):
        site = Site.objects.get_current()
        thank_you_url = 'http://%s/thank_you' % (site.domain)
        return thank_you_url

    def payment_url(self, ids=None):
        site = Site.objects.get_current()
        if not ids: ids = self.id
        payment_url = 'http://%s/payment/%s/%s' % (site.domain, self.child.identifier, ids)
        return payment_url

    def button_data(self, amount=None, ids=None):
        if not amount: amount = self.total()
        if not ids: ids = self.id
        site = Site.objects.get_current()
        data = {
            'rm': 1,
            'lc': 'US',
            'no_note': 0,
            'no_shipping': 2,
            'cmd': '_donations',
            'currency_code': 'USD',
            'business': settings.PAYPAL_BUS_ID,
            'item_number': 'husky-hustle-donation-%s' % (ids),
            'item_name': 'Husky Hustle Online Donations',
            'return': 'http://%s/thank_you' % (site.domain),
            'notify_url': 'http://%s/paid/%s' % (site.domain, ids),
            'cert_id': settings.PAYPAL_CERT_ID,
            'amount': amount,
        }
        return data

    def encrypted_block(self, data=None):
        if not data: data = self.button_data()
        paypal = PayPal()
        return paypal.encrypt(data)


class DonationForm(forms.Form):

    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    email_address = forms.EmailField(max_length=100)
    donation = CurrencyField()

    def clean(self):
        if 'donation' in self.cleaned_data:
            value  = self.cleaned_data['donation']
            result = CurrencyField.to_python(value)
            if not result:
                raise forms.ValidationError("Donation needs to be a Currency value")
            return value

        if 'phone_number' in self.cleaned_data:
            value = self.cleaned_data['phone_number']
            phoneMatchRegex = regexp.compile(r"^[0-9\-\(\) \.]*$")
            phoneSplitRegex = regexp.compile(r"[\-\(\) \.]")
            if not value:
                raise forms.ValidationError("Phone number is required")
            if not phoneMatchRegex.match(value):
                raise forms.ValidationError("Phone number can only have dashes, parenthesis, spaces, dots and numbers in them")
            phone = "".join(phoneSplitRegex.split(value))
            if len(phone) > 10:
                raise forms.ValidationError("Phone number can only be 10 digits long")


class ChildrenRegistrationForm(forms.Form):

    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    teacher = forms.CharField(max_length=100)


class ParentForm(forms.Form):

    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    email_address = forms.EmailField(max_length=100)


class ParentRegistrationForm(RegistrationForm):

    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    email_address = forms.EmailField(max_length=100)

    def clean(self):
        """
        Verifiy that the values entered into the two password fields
        match. Note that an error here will end up in
        ``non_field_errors()`` because it doesn't apply to a single
        field.
        
        """
        if 'password1' in self.cleaned_data and 'password2' in self.cleaned_data:
            passwordMatchRegex = regexp.compile(r"^[\w.@+-]+$")
            if self.cleaned_data['password1'] != self.cleaned_data['password2']:
                raise forms.ValidationError('Passwords do not match')
            if len(self.cleaned_data['password1']) < 6:
                raise forms.ValidationError("Passwords must be 6 or more characters")
            if not passwordMatchRegex.match(self.cleaned_data['password1']):
                raise forms.ValidationError("Passwords can only contain letters, numbers or @ . + - _ characters")
            self.cleaned_data['password'] = self.cleaned_data['password1']

        if 'phone_number' in self.cleaned_data:
            value = self.cleaned_data['phone_number']
            phoneMatchRegex = regexp.compile(r"^[0-9\-\(\) \.]*$")
            phoneSplitRegex = regexp.compile(r"[\-\(\) \.]")
            if not value:
                raise forms.ValidationError("Phone number is required")
            if not phoneMatchRegex.match(value):
                raise forms.ValidationError("Phone number can only have dashes, parenthesis, spaces, dots and numbers in them")
            phone = "".join(phoneSplitRegex.split(value))
            if len(phone) > 10:
                raise forms.ValidationError("Phone number can only be 10 digits long")

        return self.cleaned_data

    def save(self, email_address, password):
        user = User.objects.create_user(email_address, email_address, password)
        user.is_active = False
        user.save()
        return user


class PasswordResetForm(PasswordResetForm):

    email = forms.EmailField(max_length=100)

    def save(self, email_address):
        user = User.objects.filter(email=email_address).get()
        user.password = User.objects.make_random_password()
        user.save()
        return user


class ContactForm(forms.Form):

    subject = forms.CharField(max_length=100)
    message = forms.CharField()
    sender = forms.EmailField()
    cc_myself = forms.BooleanField(required=False)
