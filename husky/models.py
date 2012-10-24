import math
import base64
import urllib
import husky.bitly
import re as regexp
import datetime as date
import gdata.media as media
import gdata.photos.service as gdata
import gdata.calendar.client as cdata

from django.db import models
from django.db.models import Sum
from django.db.models.signals import post_save
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.sites.models import Site
from django import forms

from picasa import  PicasaField, PicasaStorage
from decimal import Decimal
from registration.forms import RegistrationForm

from socialregistration.contrib.facebook.models import FacebookProfile
from socialregistration.contrib.twitter.models import TwitterProfile
from socialregistration.contrib.openid.models import OpenIDProfile

from husky.helpers import *

DONATION_GOAL     = 30000
MAX_BAR_LENGTH    = 225
MAX_ARROW_HEIGHT  = 275
BASE_ARROW_HEIGHT = 73


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
    date_added = models.DateTimeField()


class Blog(models.Model):

    title = models.CharField(max_length=100)
    author = models.ForeignKey(User)
    content = models.TextField(max_length=4000)
    date_added = models.DateTimeField()


class Message(models.Model):

    title = models.CharField(max_length=100)
    author = models.ForeignKey(User)
    content = models.TextField(max_length=4000)
    date_added = models.DateTimeField()


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
        return self.shorten


class Grade(models.Model):

    grade = models.IntegerField(blank=True, null=True)
    title = models.CharField(max_length=15)

    def __unicode__(self):
        return self.title


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

    def __unicode__(self):
        return '%s (%s) %s' % (self.full_name(), self.room_number, self.grade)

    def full_name(self):
        return '%s %s %s' % (self.title, self.first_name, self.last_name)

    def shortened(self):
        if not self.shorten:
            api = bitly.Api(login=settings.BITLY_LOGIN, apikey=settings.BITLY_APIKEY)
            self.shorten = api.shorten(self.website)
        return self.shorten


class Parent(models.Model):

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email_address = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=25)
    activation_key = models.CharField(max_length=200)
    key_expires = models.DateTimeField()
    date_added = models.DateTimeField()
    site = models.ForeignKey(Site)
    user = models.OneToOneField(User, unique=True)

    def __unicode__(self):
        return '%s (%s)' % (self.full_name(), self.email_address)

    def full_name(self):
        return '%s %s' % (self.first_name, self.last_name)

    def num_chilren(self):
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
        return google


class Children(models.Model):

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    identifier = models.CharField(max_length=100, unique=True)
    date_added = models.DateTimeField()
    laps = models.IntegerField(blank=True, null=True)
    collected = CurrencyField(blank=True, null=True)
    parent = models.ForeignKey(Parent, related_name='children')
    teacher = models.ForeignKey(Teacher, related_name='students')

    def __unicode__(self):
        return self.full_name()

    def full_name(self):
        return '%s %s' % (self.first_name, self.last_name)

    def donate_url(self):
        site = self.parent.site
        donate_url = 'http://%s/make-donation/%s' % (site.domain, self.identifier)
        return donate_url

    def facebook_share_url(self):
        site = self.parent.site
        params = 'app_id=' + settings.FACEBOOK_APP_ID + '&link=' + self.donate_url() + '&picture=' + ('http://%s/static/images/hickslogo-1.jpg' % site.domain) + '&name=' + urllib.quote('Husky Hustle') + '&caption=' + urllib.quote('Donate to %s' % self.full_name()) + '&description=' + urllib.quote("Donate and help further our children's education.") + '&redirect_uri=' + 'http://%s/' % site.domain
        fb_share_url = 'https://www.facebook.com/dialog/feed?' + params
        return fb_share_url

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
        return [total_got, total_due]

    def calculate_totals(self, id=None):
        if id:
            total = 0
            result = Children.objects.get(pk=id)
            for sponsor in result.sponsors.all():
                total += sponsor.donated
            self.collected = total
            self.save()
        else:
            results = Children.objects.all()
            for result in results:
                total = 0
                for sponsor in result.sponsors.all():
                    total += sponsor.donated
                result.collected = total
                result.save()


class Donation(models.Model):

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email_address = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=25)
    child = models.ForeignKey(Children, related_name='sponsors')
    donation = CurrencyField(blank=True, null=True)
    donated = CurrencyField(blank=True, null=True)
    per_lap = models.BooleanField()
    paid = models.BooleanField()
    date_added = models.DateTimeField()

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

    def get_donations(self, child_id, limit=30, offset=0, query=None, field='id', sortname='id', sortorder='asc'):
        results = []
        try:
            limited = int(limit) + int(offset)
            if sortorder == 'desc':
                sortname = '-%s'%sortname
            if query:
                if field == 'last_name':
                    results = Donation.objects.filter(child__identifier=child_id, last_name__contains=query).order_by(sortname)[offset:limited]
                elif field == 'first_name':
                    results = Donation.objects.filter(child__identifier=child_id, first_name__contains=query).order_by(sortname)[offset:limited]
                elif field == 'email_address':
                    results = Donation.objects.filter(child__identifier=child_id, email_address__contains=query).order_by(sortname)[offset:limited]
                elif field == 'phone_number':
                    results = Donation.objects.filter(child__identifier=child_id, phone_number__contains=query).order_by(sortname)[offset:limited]
                else:
                    results = Donation.objects.filter(child__identifier=child_id, id=query).order_by(sortname)[offset:limited]
            else:
                results = Donation.objects.filter(child__identifier=child_id).order_by(sortname)[offset:limited]
        except Exception, e:
            pass
        return results

    def get_donations_total(self, child_id, query=None, field='id'):
        try:
            if query:
                if field == 'last_name':
                    return Donation.objects.filter(child__identifier=child_id, last_name__contains=query).count()
                elif field == 'first_name':
                    return Donation.objects.filter(child__identifier=child_id, first_name__contains=query).count()
                elif field == 'email_address':
                    return Donation.objects.filter(child__identifier=child_id, email_address__contains=query).count()
                elif field == 'phone_number':
                    return Donation.objects.filter(child__identifier=child_id, phone_number__contains=query).count()
                else:
                    return Donation.objects.filter(child__identifier=child_id, id=query).count()
            else:
                return Donation.objects.filter(child__identifier=child_id).count()
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


class DonationForm(forms.Form):

    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    email_address = forms.EmailField(max_length=100)
    phone_number = forms.CharField(max_length=25)
    donation = CurrencyField()

    def clean(self):
        if 'donation' in self.cleaned_data:
            value  = self.cleaned_data['donation']
            result = CurrencyField.to_python(value)
            if not result:
                raise forms.ValidationError("Donation needs to be a Currency value")
            return value


class ChildrenRegistrationForm(forms.Form):

    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    teacher = forms.CharField(max_length=100)


class ParentRegistrationForm(RegistrationForm):

    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    email_address = forms.EmailField(max_length=100)
    phone_number = forms.CharField(max_length=25)

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
