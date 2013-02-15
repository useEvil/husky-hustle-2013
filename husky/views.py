import pytz
import base64
import django.contrib.staticfiles
import gdata.photos.service as gdata
import husky.helpers as h
import datetime as date
import re as regexp

from django.db.models import Count, Sum, Avg, Max
from django.db import IntegrityError
from django.core.mail import send_mail, send_mass_mail
from django.template import Context, loader, RequestContext
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import simplejson
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.views import password_reset, password_reset_done, password_reset_confirm, password_reset_complete
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm, PasswordChangeForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site
from django.contrib.syndication.views import Feed
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.conf import settings

from socialregistration.contrib.facebook.models import FacebookProfile
from socialregistration.contrib.twitter.models import TwitterProfile

from husky.models import Parent, Children, ParentChildren, Donation, Teacher, Grade, Album, Photo, Content, Blog, Message, Link, Calendar
from husky.models import ContactForm, ParentRegistrationForm, ChildrenRegistrationForm, DonationForm
from husky.helpers import *

# Create your views here.
@checkUser
def index(request):
    parent      = None
    my_facebook = None
    my_twitter  = None
    my_google   = None
    if request.user.is_authenticated:
        parent = getParent(request)
        try:
            my_facebook = parent.facebook()
            my_twitter  = parent.twitter()
            my_google   = parent.google()
        except:
            pass
    c = Context(dict(
            page_title='Home',
            parent=parent,
            my_facebook=my_twitter,
            my_twitter=my_twitter,
            my_google=my_google,
            motd=Message.objects.latest('date_added'),
            content=Content.objects.filter(page='index').get(),
            bar_height=Donation().bar_height(),
            arrow_height=Donation().arrow_height(),
            calendar=Calendar().get_events(),
    ))
    return render_to_response('index.html', c, context_instance=RequestContext(request))

def nav(request, page='index', id=None):
    parent      = None
    my_twitter  = None
    my_facebook = None
    my_google   = None
    if request.user.is_authenticated:
        parent = getParent(request)
        try:
            my_facebook = parent.facebook()
            my_twitter  = parent.twitter()
            my_google   = parent.google()
        except:
            pass
    c = Context(dict(
            page_title=page.title(),
            parent=parent,
            my_facebook=my_twitter,
            my_twitter=my_twitter,
            my_google=my_google,
            bar_height=Donation().bar_height(),
            arrow_height=Donation().arrow_height(),
    ))
    print_log('==== bar_height [%s]' % Donation().bar_height(), settings.DEBUG)
    print_log('==== arrow_height [%s]' % Donation().arrow_height(), settings.DEBUG)
    if page == 'photos':
        c['albums'] = Album()
        c['content'] = Content.objects.filter(page=page).get()
    elif page == 'privacy' or page == 'getting_started':
        c['content'] = Content.objects.filter(page=page).get()
    elif page == 'links':
        c['links'] = Link.objects.filter(status=1).all()
        c['content'] = Content.objects.filter(page=page).get()
    elif page == 'blog':
        if id:
            c['entries'] = [ Blog.objects.get(pk=id) ]
        else:
            c['entries'] = Blog.objects.order_by('-date_added')[:15]
    return render_to_response('%s.html'%page, c, context_instance=RequestContext(request))

@login_required(login_url='/accounts/login/')
@checkUser
def account(request, identifier=None):
    parent = getParent(request)
    c = Context(dict(
            page_title='Profile',
            parent=parent,
            my_facebook=parent.facebook,
            my_twitter=parent.twitter,
            my_google=parent.google,
            teachers=Teacher().get_list(),
            facebook_api=settings.FACEBOOK_APP_ID
    ))
    if identifier:
        try:
            child = Children.objects.get(identifier=identifier)
            c['child'] = child
            c['messages'] = messages.get_messages(request)
            c['page_title'] = '%s' % (child)
            c['teachers'] = Teacher().get_donate_list()
            return render_to_response('account/donations.html', c, context_instance=RequestContext(request))
        except:
            messages.error(request, 'Could not find Student for identity: %s' % identifier)
    c['messages'] = messages.get_messages(request)
    return render_to_response('account/index.html', c, context_instance=RequestContext(request))

def donation_sheet(request, identifier=None):
    c = Context(dict(
            page_title='Pledge Sheet',
    ))
    if identifier and identifier == 'pdf':
        response = HttpResponse(mimetype='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="donation-sheet.pdf"'
        response.write(file("%s/docs/donation_sheet.pdf" % settings.MEDIA_ROOT).read())
        return response
    elif identifier and identifier == 'print':
        c['page_title'] = 'Pledge Sheet'
    elif identifier:
        try:
            child  = Children.objects.get(identifier=identifier)
            c['child'] = child
            c['page_title'] = 'Pledge Sheet: %s' % (child)
        except:
            messages.error(request, 'Could not find Student for identity: %s' % identifier)
    c['messages'] = messages.get_messages(request)
    return render_to_response('account/donation_sheet.html', c, context_instance=RequestContext(request))

def make_donation(request, identifier=None):
    parent = getParent(request)
    c = Context(dict(
            page_title='Donate',
            parent=parent,
            teachers=Teacher().get_donate_list(),
            make_donation=True,
    ))
    if identifier == 'search':
        c['search'] = True
        c['parent_only'] = request.GET.get('parent_only')
        if c['parent_only'] == '1':
            first_name = request.GET.get('parent_first_name')
            last_name = request.GET.get('parent_last_name')
        else:
            first_name = request.GET.get('student_first_name')
            last_name = request.GET.get('student_last_name')
        if first_name or last_name:
            if first_name and last_name:
                c['search'] = '%s %s' % (first_name, last_name)
            else:
                c['search'] = first_name or last_name
            try:
                children = Children().find(c['parent_only'], first_name, last_name)
                c['children'] = children
            except Exception, e:
                messages.error(request, 'Could not find Records matching: %s' % (c['search']))
                c['error'] = True
            if not children:
                messages.error(request, 'Could not find Records matching: %s' % (c['search']))
                c['error'] = True
    elif identifier:
        try:
            child = Children.objects.get(identifier=identifier)
            c['child'] = child
        except:
            messages.error(request, 'Could not find Student for identity: %s' % identifier)
            c['error'] = True
    c['messages'] = messages.get_messages(request)
    return render_to_response('donate.html', c, context_instance=RequestContext(request))

def teacher_donation(request, identifier=None):
    parent = getParent(request)
    c = Context(dict(
            page_title='Donate',
            parent=parent,
            teachers=Teacher().get_list(),
            teachers_donate=Teacher().get_donate_list(),
            teacher_donation=True,
            make_donation=True,
    ))
    if not identifier: 
        return render_to_response('donate.html', c, context_instance=RequestContext(request))
    try:
        child = Children.objects.get(identifier=identifier)
        c['child'] = child
    except:
        messages.error(request, 'Could not find Student for identity: %s' % identifier)
        c['error'] = True
    c['messages'] = messages.get_messages(request)
    return render_to_response('donate.html', c, context_instance=RequestContext(request))

def payment(request, identifier=None, id=None):
    c = Context(dict(
            page_title='Payment',
    ))
    try:
        child = Children.objects.get(identifier=identifier)
        c['child'] = child
    except:
        messages.error(request, 'Could not find Student for identity: %s' % identifier)
        c['error'] = True
    if request.GET.get('amount'):
        c['encrypted_block'] = Donation().encrypted_block(Donation().button_data(request.GET.get('amount'), id))
        c['total'] = request.GET.get('amount')
    else:
        try:
            donation = Donation.objects.get(id=id)
            c['donation'] = donation
            c['encrypted_block'] = donation.encrypted_block()
            c['total'] = donation.total()
        except:
            messages.error(request, 'Could not find Donation for ID: %s' % id)
            c['error'] = True
    c['messages'] = messages.get_messages(request)
    return render_to_response('payment.html', c, context_instance=RequestContext(request))

def donate(request, child_id=None):
    child = Children.objects.get(identifier=child_id)
    from_account = None
    teacher_donation = None
    c = Context(dict(
            page_title='Donator',
            parent=getParent(request),
            teachers=Teacher().get_donate_list(),
            child=child,
            donate=True,
    ))
    if request.POST:
        from_account = request.POST.get('from_account')
        make_donation = request.POST.get('make_donation')
        teacher_donation = request.POST.get('teacher_donation')
        form = DonationForm(request.POST)
        if form.is_valid():
            try:
                donation = Donation(
                    first_name=request.POST.get('first_name'),
                    last_name=request.POST.get('last_name'),
                    email_address=request.POST.get('email_address'),
                    phone_number=request.POST.get('phone_number'),
                    per_lap=request.POST.get('per_lap') or 0,
                    donation=request.POST.get('donation'),
                    date_added=date.datetime.now(pytz.utc),
                    child=child,
                )
                donation.save()
                messages.success(request, from_account and 'Donation Added Successfully' or 'Thank you for making a Pledge')
                c_parent = child.parent()
                c['success'] = True
                c['donate_url'] = child.donate_url()
                c['child_full_name'] = child.full_name
                c['child_identifier'] = child.identifier
                c['amount'] = donation.donation
                c['full_name'] = donation.full_name()
                c['is_per_lap'] = donation.per_lap
                c['payment_url'] = donation.payment_url()
                c['email_address'] = donation.email_address
                c['subject'] = 'Husky Hustle: Thank you for making a Pledge'
                c['domain'] = Site.objects.get_current().domain
                if not teacher_donation:
                    _send_email_teamplate('donate', c)
                if c_parent:
                    c['email_address'] = c_parent.email_address
                    c['parent_full_name'] = c_parent.full_name
                    c['subject'] = 'Husky Hustle: Congratulations %s just got a Donation' % (child.first_name)
                    _send_email_teamplate('donated', c)
            except Exception, e:
                c['make_donation'] = make_donation or False
                if from_account: c['error'] = True
                messages.error(request, str(e))
        else:
            c['make_donation'] = make_donation or False
            if from_account: c['error'] = True
            messages.error(request, 'Failed to Add %s' % (teacher_donation and 'Donation' or 'Sponsor'))
        c['form'] = form
    c['messages'] = messages.get_messages(request)
    c['teacher_donation'] = teacher_donation or False
    if from_account:
        return HttpResponseRedirect('/account/%s' % child.identifier)
    else:
        return render_to_response('donate.html', c, context_instance=RequestContext(request))

def donate_direct(request):
    c = Context(dict(
            page_title='Donator',
            parent=getParent(request),
            donate=True,
    ))
    if request.POST:
        form = DonationForm(request.POST)
        if form.is_valid():
            teacher = Teacher.objects.get(pk=request.POST.get('student_teacher_id'))
            identifier = '%s-%s-%s'%(replace_space(request.POST.get('student_first_name')), replace_space(request.POST.get('student_last_name')), teacher.room_number)
            try:
                child = Children.objects.get(identifier=identifier)
            except Exception, e:
                child = Children(
                    first_name=request.POST.get('student_first_name'),
                    last_name=request.POST.get('student_last_name'),
                    date_added=date.datetime.now(pytz.utc),
                    identifier=identifier,
                    teacher=teacher,
                )
                child.save()
            try:
                donation = Donation(
                    first_name=request.POST.get('first_name'),
                    last_name=request.POST.get('last_name'),
                    email_address=request.POST.get('email_address'),
                    phone_number=request.POST.get('phone_number'),
                    per_lap=request.POST.get('per_lap') or 0,
                    donation=request.POST.get('donation'),
                    date_added=date.datetime.now(pytz.utc),
                    child=child,
                )
                donation.save()
                messages.success(request, 'Thank you for making a Pledge')
                c_parent = child.parent()
                c['success'] = True
                c['donate_url'] = child.donate_url()
                c['child_full_name'] = child.full_name
                c['child_identifier'] = child.identifier
                c['amount'] = donation.donation
                c['full_name'] = donation.full_name()
                c['is_per_lap'] = donation.per_lap
                c['payment_url'] = donation.payment_url()
                c['email_address'] = donation.email_address
                c['subject'] = 'Husky Hustle: Thank you for making a Pledge'
                c['domain'] = Site.objects.get_current().domain
                if not request.POST.get('teacher_donation'):
                    _send_email_teamplate('donate', c)
                if c_parent:
                    c['email_address'] = c_parent.email_address
                    c['parent_full_name'] = c_parent.full_name
                    c['subject'] = 'Husky Hustle: Congratulations %s just got a Donation' % (child.first_name)
                    _send_email_teamplate('donated', c)
            except Exception, e:
                messages.error(request, str(e))
        else:
            messages.error(request, 'Failed to Add Sponsor')
        c['form'] = form
    c['messages'] = messages.get_messages(request)
    if request.POST.get('make_donation') and request.POST.get('teacher_donation'):
        c['teacher_donation'] = True
    return render_to_response('donate.html', c, context_instance=RequestContext(request))

def album(request, album_id=None):
    album = Album().get_album(album_id)
    c = Context(dict(
            page_title=album.title.text,
            parent=getParent(request),
            album=album
    ))
    return render_to_response('photos.html', c, context_instance=RequestContext(request))

def photo(request, album_id=None, photo_id=None):
    album = Album().get_album(album_id)
    photo = Photo().get_photo(album_id, photo_id)
    c = Context(dict(
            page_title=photo.title.text,
            parent=getParent(request),
            photo_album=album,
            photo=photo,
            prev=prevPhoto(album.entry, request.GET.get('index')),
            next=nextPhoto(album.entry, request.GET.get('index')),
            index=int(request.GET.get('index'))
    ))
    return render_to_response('photos.html', c, context_instance=RequestContext(request))

@checkUser
def register(request):
    c = Context(dict(
            page_title='Register',
    ))
    if request.method == 'POST':
        post = request.POST.copy()
        post.__setitem__('email', post.get('email_address'))
        post.__setitem__('username', post.get('email_address'))
        form = ParentRegistrationForm(post)
        if form.is_valid():
            try:
                user = form.save(form['email_address'].data, form['password1'].data)
                expires = date.datetime.now(pytz.utc) + date.timedelta(settings.ACCOUNT_ACTIVATION_DAYS)
                key = base64.urlsafe_b64encode('%s-%s' % (form['email_address'].data, expires)).replace('=','')
                parent = Parent(
                                first_name=form['first_name'].data,
                                last_name=form['last_name'].data,
                                email_address=form['email_address'].data,
                                phone_number=post.get('phone_number'),
                                guardian=post.get('guardian'),
                                activation_key=key,
                                key_expires=expires,
                                date_added=date.datetime.now(pytz.utc),
                                site=Site.objects.get_current(),
                                user=user,
                            )
                parent.save()
                c['key'] = key
                c['parent_name'] = parent.full_name
                c['activate_url'] = parent.activate_url()
                c['email_address'] = parent.email_address
                c['subject'] = 'Husky Hustle: Parent Registration'
                c['domain'] = Site.objects.get_current().domain
                _send_email_teamplate('register-activation', c)
                return render_to_response('registration/registration_complete.html', c, context_instance=RequestContext(request))
            except Exception, e:
                messages.error(request, 'Failed to Register Account: %s' % str(e))
                c['form'] = form
                c['messages'] = messages.get_messages(request)
                return render_to_response('registration/registration_form.html', c, context_instance=RequestContext(request))
        else:
            messages.error(request, 'Failed to Register Account')
            c['form'] = form
        c['messages'] = messages.get_messages(request)
    return render_to_response('registration/registration_form.html', c, context_instance=RequestContext(request))

def activate(request, key=None):
    c = Context(dict(
            page_title='Home',
    ))
    template = 'registration/login.html'
    if not key:
        key = request.GET.get('key')
    if not key:
        return render_to_response('registration/registration_complete.html', c, context_instance=RequestContext(request))
    try:
        user = User.objects.filter(parent__activation_key=key).get()
    except Exception, e:
        messages.error(request, 'Failed to Activate Account: %s' % str(e))
        user = None
    if user:
        if user.is_active:
            messages.error(request, 'Account already Activated')
        elif user.parent.key_expires < date.datetime.now(pytz.utc):
            c['new_key'] = key
            messages.error(request, 'Activation Key has already Expired.  Request a new activation key')
            template = 'registration/registration_form.html'
        else:
            user.is_active = True
            user.save()
            c['subject'] = 'Husky Hustle: Account Activated'
            c['parent_name'] = user.parent.full_name
            c['email_address'] = user.parent.email_address
            c['domain'] = Site.objects.get_current().domain
            _send_email_teamplate('register-parent', c)
            messages.success(request, 'Successfully Activated Account')
    c['messages'] = messages.get_messages(request)
    return render_to_response(template, c, context_instance=RequestContext(request))

def request(request, type=None, key=None):
    parent = getParent(request)
    c = Context(dict(
            page_title='Home',
            parent=parent,
    ))
    if type == 'key':
        user = User.objects.filter(parent__activation_key=key).get()
        expires = date.datetime.now(pytz.utc) + date.timedelta(settings.ACCOUNT_ACTIVATION_DAYS)
        key = base64.urlsafe_b64encode('%s-%s-%s' % (user.parent.email_address, expires)).replace('=','')
        user.parent.activation_key = key
        user.parent.key_expires = expires
        user.parent.save()
        c['key'] = key
        c['parent_name'] = user.parent.full_name
        c['email_address'] = user.parent.email_address
        c['subject'] = 'Husky Hustle: Parent Activation'
        c['domain'] = Site.objects.get_current().domain
        _send_email_teamplate('register-activation', c)
        messages.success(request, 'New Activation Key Sent')
        c['messages'] = messages.get_messages(request)
        return render_to_response('registration/registration_complete.html', c, context_instance=RequestContext(request))
    elif type == 'link':
        link = Parent.objects.get(id=key)
        c['link_url'] = parent.link_url()
        c['full_name'] = link.full_name
        c['request_id'] = parent.id
        c['email_address'] = link.email_address
        c['request_full_name'] = parent.full_name
        c['subject'] = 'Husky Hustle: Account Link Request'
        c['domain'] = Site.objects.get_current().domain
        _send_email_teamplate('account-link', c)
        messages.success(request, 'Your Request has been sent')
    else:
        messages.error(request, 'No action provided for this request')
    return HttpResponseRedirect('/account/')

def contact(request):
    c = Context(dict(
            page_title='Contact',
            parent=getParent(request),
    ))
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            sender  = form.cleaned_data['sender']
            cc_myself  = form.cleaned_data['cc_myself']
            recipients = [settings.PICASA_STORAGE_OPTIONS['email']]
            if cc_myself:
                recipients.append(sender)
            send_mail(subject, message, sender, recipients)
            messages.success(request, 'Successfully Sent')
    else:
        form = ContactForm()
    c['form'] = form
    c['messages'] = messages.get_messages(request)
    return render_to_response('contact.html', c, context_instance=RequestContext(request))

def results(request, type=None):
    c = Context(dict(
            page_title='Results',
            parent=getParent(request),
            type=type or 'all',
    ))
    if 'admin' in request.path:
        return render_to_response('admin/results.html', c, context_instance=RequestContext(request))
    else:
        return render_to_response('results.html', c, context_instance=RequestContext(request))

def reporting(request, type=None):
    c = Context(dict(
            page_title='Reporting',
            parent=getParent(request),
            type=type,
    ))
    return render_to_response('admin/chart.html', c, context_instance=RequestContext(request))

@login_required(login_url='/accounts/login/')
def add(request, type=None):
    parent = getParent(request)
    c = Context(dict(
            page_title='Profile',
            parent=parent,
            my_facebook=parent.facebook,
            my_twitter=parent.twitter,
            my_google=parent.google,
            teachers=Teacher().get_list(),
            facebook_api=settings.FACEBOOK_APP_ID
    ))
    if request.POST:
        form = ChildrenRegistrationForm(request.POST)
        if form.is_valid():
            try:
                teacher = Teacher.objects.get(pk=request.POST.get('teacher'))
                child = Children(
                    first_name=request.POST.get('first_name'),
                    last_name=request.POST.get('last_name'),
                    identifier='%s-%s-%s'%(replace_space(request.POST.get('first_name')), replace_space(request.POST.get('last_name')), teacher.room_number),
                    date_added=date.datetime.now(pytz.utc),
                    teacher=teacher,
                )
                child.save()
                pc = ParentChildren(parent=parent, children=child, default=1)
                pc.save()
                c['child_name'] = child.full_name
                c['parent_name'] = parent.full_name
                c['email_address'] = parent.email_address
                c['child_identifier'] = child.identifier
                c['donate_url'] = child.donate_url()
                c['manage_url'] = child.manage_url()
                c['subject'] = 'Husky Hustle: Student Registration'
                c['domain'] = Site.objects.get_current().domain
                _send_email_teamplate('register-child', c)
                messages.success(request, 'Child Added')
            except IntegrityError, e:
                other_parent = None
                current_parent = None
                try:
                    other_parent = Parent.objects.filter(children__identifier=child.identifier, parentchildren__default=1).get()
                    current_parent = Parent.objects.filter(children__identifier=child.identifier, pk=parent.id).get()
                except:
                    pass
                if not current_parent:
                    c['linked'] = other_parent
                    c['linked_child'] = child
                    messages.error(request, 'Student has already been added by another Parent')
                else:
                    messages.error(request, 'You have already added this Student')
            except Exception, e:
                messages.error(request, str(e))
        else:
            messages.error(request, 'Failed to Add Student')
        c['form'] = form
    c['messages'] = messages.get_messages(request)
#    return HttpResponseRedirect('/accounts/profile/')
    return render_to_response('account/index.html', c, context_instance=RequestContext(request))

@login_required(login_url='/accounts/login/')
def link(request, parent_id=None):
    try:
        parent = getParent(request)
        linked = Parent.objects.get(pk=parent_id)
        for child in parent.children.all():
            pc = ParentChildren(parent=linked, children=child, default=0)
            pc.save()
        c['full_name'] = parent.full_name
        c['linked_full_name'] = linked.full_name
        c['subject'] = 'Husky Hustle: Account Link Request'
        _send_email_teamplate('account-link-accepted', c)
        messages.success(request, 'Successfully Linked Account')
    except Exception, e:
        messages.error(request, 'Failed to Link Account: %s' % str(e))
    return HttpResponseRedirect('/account/')

@login_required(login_url='/accounts/login/')
def edit(request, type=None):
    if request.POST:
        if type == 'child':
            form = ChildrenRegistrationForm(request.POST)
            if form.is_valid():
                try:
                    teacher = Teacher.objects.get(pk=request.POST.get('teacher'))
                    child = Children.objects.get(pk=request.POST.get('id'))
                    child.first_name = request.POST.get('first_name')
                    child.last_name = request.POST.get('last_name')
                    child.teacher = teacher
                    child.identifier = '%s-%s-%s'%(replace_space(request.POST.get('first_name')), replace_space(request.POST.get('last_name')), teacher.room_number)
                    child.save()
                    messages.success(request, 'Successfully Updated Student')
                except Exception, e:
                    messages.error(request, 'Failed to Update Student: %s' % str(e))
        elif type == 'profile':
            form = ParentRegistrationForm(post)
            if form.is_valid():
                try:
                    parent = getParent(request)
                    parent.first_name = request.POST.get('first_name')
                    parent.last_name = request.POST.get('last_name')
                    parent.email_address = request.POST.get('email_address')
                    parent.phone_number = request.POST.get('phone_number')
                    parent.guardian = request.POST.get('guardian')
                    user = parent.user
                    user.email = request.POST.get('email_address')
                    user.username = request.POST.get('email_address')
                    user.save()
                    parent.save()
                    messages.success(request, 'Successfully Updated Profile')
                except Exception, e:
                    messages.error(request, 'Failed to Update Profile: %s' % str(e))
        elif type == 'sponsor':
            form = DonationForm(request.POST)
            if form.is_valid():
                try:
                    donation = Donation.objects.get(pk=request.POST.get('id'))
                    donation.first_name = request.POST.get('first_name')
                    donation.last_name = request.POST.get('last_name')
                    donation.email_address = request.POST.get('email_address')
                    donation.phone_number = request.POST.get('phone_number')
                    donation.donation = request.POST.get('donation')
                    donation.per_lap = request.POST.get('per_lap') or 0
                    donation.save()
                    messages.success(request, 'Successfully Updated Sponsor')
                except Exception, e:
                    messages.error(request, 'Failed to Update Sponsor: %s' % str(e))
    return HttpResponse(simplejson.dumps({'result': 'OK', 'status': 200}), mimetype='application/json')

@login_required(login_url='/accounts/login/')
def delete(request, type=None):
    if request.POST:
        if type == 'sponsor':
            donators = request.POST.getlist('donators')
            for donator in donators:
                try:
                    object = Donation.objects.get(pk=donator)
                    object.delete()
                    messages.success(request, 'Successfully Deleted Sponsor: %s' % object.full_name())
                except Exception, e:
                    messages.error(request, 'Failed to Delete Sponsor: %s' % str(e))
    return HttpResponse(simplejson.dumps({'result': 'OK', 'status': 200}), mimetype='application/json')

def emails(request):
    c = Context(dict(
            subject='Husky Hustle: Help Support %s' % request.POST.get('child_first_name'),
            body=request.POST.get('custom_message')
    ))
    addresses = request.POST.get('email_addresses')
    if not addresses:
        messages.success(request, 'You must provide email addresses')
        return HttpResponse(simplejson.dumps({'result': 'NOTOK', 'status': 400, 'message': 'You must provide email addresses.'}), mimetype='application/json')
    p = regexp.compile(r'\s*,\s*')
    addresses = filter(None, p.split(addresses))
    data = []
    for address in addresses:
        c['email_address'] = address
        data.append(_send_email_teamplate('emails', c, 1))
    send_mass_mail(data)
    messages.success(request, 'Successfully Sent Emails')
    return HttpResponse(simplejson.dumps({'result': 'OK', 'status': 200}), mimetype='application/json')

def reminders(request):
    c = Context(dict(
            subject='Husky Hustle: Payment Reminder',
    ))
    donators = request.POST.getlist('donators')
    if request.POST.get('custom_message'):
        c['custom_message'] = request.POST.get('custom_message')
    data = []
    for donator in donators:
        donation = Donation.objects.get(pk=donator)
        c['name'] = donation.full_name
        c['email_address'] = donation.email_address
        c['child_name'] = donation.child.full_name
        c['child_identifier'] = donation.child.identifier
        c['donation_id'] = donation.id
        c['payment_url'] = donation.payment_url()
        c['domain'] = Site.objects.get_current().domain
        data.append(_send_email_teamplate('reminder', c, 1))
    send_mass_mail(data)
    messages.success(request, 'Successfully Sent Reminders')
    return HttpResponse(simplejson.dumps({'result': 'OK', 'status': 200}), mimetype='application/json')

def disconnect(request, parent_id=None, social=None):
    parent = Parent.objects.get(pk=parent_id)
    try:
        if social == 'facebook':
            parent.facebook().delete()
        elif social == 'twitter':
            parent.twitter().delete()
        elif social == 'google':
            parent.google().delete()
        messages.success(request, 'Successfully Disconnected')
    except Exception, e:
        messages.error(request, 'Failed to Disconnect: %s' % str(e))
    return HttpResponse(simplejson.dumps({'result': 'OK', 'status': 200}), mimetype='application/json')

def paid(request, donation_id=None):
    for id in donation_id.split(','):
        try:
            object = Donation.objects.get(pk=id)
            object.paid = True
            object.donated = object.total()
            object.save()
            messages.success(request, 'Successfully set Sponsor to Paid')
        except Exception, e:
            messages.error(request, 'Failed to set Sponsor to Paid: %s' % str(e))
    return HttpResponse(simplejson.dumps({'result': 'OK', 'status': 200}), mimetype='application/json')

@csrf_exempt
def thank_you(request, donation_id=None):
    c = Context(dict(
            page_title='Thank You',
    ))
    print_log('==== request.POST [%s]' % request.POST, settings.DEBUG)
    print_log('==== request.GET [%s]' % request.GET, settings.DEBUG)
    if donation_id:
        try:
            object = Donation.objects.get(pk=donation_id)
            object.paid = True
            object.save()
            messages.success(request, 'Successfully set Sponsor to Paid')
        except Exception, e:
            messages.error(request, 'Failed to set Sponsor to Paid: %s' % str(e))
    elif request.GET.get('custom') or request.POST.get('custom'):
        donation_id = request.GET.get('custom')
        try:
            object = Donation.objects.get(pk=donation_id)
            object.paid = True
            object.save()
            messages.success(request, 'Successfully set Sponsor to Paid')
        except Exception, e:
            messages.error(request, 'Failed to set Sponsor to Paid: %s' % str(e))
    else:
        return render_to_response('thank_you.html', c, context_instance=RequestContext(request))
    return HttpResponse(simplejson.dumps({'result': 'OK', 'status': 200}), mimetype='application/json')

@csrf_protect
def reset(request):
    return password_reset(request, template_name='registration/reset_password.html')

def reset_done(request):
    return password_reset_done(request, template_name='registration/reset_password_done.html')

@sensitive_post_parameters()
@never_cache
def reset_confirm(request, uidb36=None, token=None):
    return password_reset_confirm(request, uidb36, token, template_name='registration/reset_password_confirm.html')

def reset_complete(request):
    return password_reset_complete(request, template_name='registration/reset_password_complete.html')

@never_cache
def json(request, child_id=None):
    offset     = request.GET.get('offset') or 0
    limit      = request.GET.get('limit')  or 30
    query      = request.GET.get('query')  or None
    field      = request.GET.get('qtype')  or None
    sortname   = request.GET.get('sortname')  or 'id'
    sortorder  = request.GET.get('sortorder') or 'asc'
    donations  = Donation().get_donations(child_id, limit, offset, query, field, sortname, sortorder)
    total      = Donation().get_donations_total(child_id, query, field)
    data       = _formatData(donations, total)
    return HttpResponse(simplejson.dumps(data), mimetype='application/json')

def reports(request, type=None):
    json = {'label': [], 'values': []}
    grades = Grade.objects.all()
    if type == 'most-laps':
        for index, grade in enumerate(grades):
            json['values'].append({'label': grade.title, 'values': [], 'labels': []})
            teachers = Teacher.objects.filter(grade=grade).exclude(list_type=3).all()
            for teacher in teachers:
                num_laps = Children.objects.filter(teacher=teacher).aggregate(num_laps=Sum('laps'))
                json['values'][index]['values'].append(num_laps['num_laps'] or 0)
                json['values'][index]['labels'].append(teacher.full_name())
    elif type == 'most-donations':
        for index, grade in enumerate(grades):
            json['values'].append({'label': grade.title, 'values': [], 'labels': []})
            teachers = Teacher.objects.filter(grade=grade).exclude(list_type=3).all()
            for teacher in teachers:
                children = Children.objects.filter(teacher=teacher).all()
                total = 0
                for child in children:
                    total += child.collected or 0
                json['values'][index]['values'].append(float(total))
                json['values'][index]['labels'].append(teacher.full_name())
    elif type == 'most-laps-by-child':
        for index, grade in enumerate(grades):
            json['values'].append({'label': grade.title, 'values': [], 'labels': []})
            children = Children.objects.filter(teacher__grade=grade).annotate(max_laps=Max('laps')).order_by('laps')[:20]
            for child in children:
                json['values'][index]['values'].append(child.max_laps or 0)
                json['values'][index]['labels'].append(child.full_name())
    elif type == 'most-donations-by-child':
        for index, grade in enumerate(grades):
            json['values'].append({'label': grade.title, 'values': [], 'labels': []})
            children = Children.objects.filter(teacher__grade=grade).annotate(max_funds=Max('collected')).order_by('collected')[:20]
            for child in children:
                json['values'][index]['values'].append(float(child.collected or 0))
                json['values'][index]['labels'].append(child.full_name())
    return HttpResponse(simplejson.dumps(json), mimetype='application/json')

@login_required(login_url='/admin/')
def calculate_totals(request, type=None, id=None):
    if type == 'donation':
        Donation().calculate_totals(id)
    if type == 'children':
        Children().calculate_totals(id)
    if type == 'both':
        Donation().calculate_totals()
        Children().calculate_totals()
    return HttpResponse(simplejson.dumps({'result': 'OK', 'status': 200}), mimetype='application/json')


def _formatData(data, total):
    if not data and not total: return
    result = { }
    count  = 1
    result['rows']  = [ ]
    result['total'] = total
    for donation in data:
        row = {'id': donation.id, 'cell': [ donation.id ]}
        if donation.last_name == 'teacher':
            row['cell'].append(donation.first_name)
            row['cell'].append('<span class="hidden">%s</span>' % donation.last_name)
            row['cell'].append('<span class="hidden">%s</span>' % donation.email_address)
            row['cell'].append('<span class="hidden">%s</span>' % donation.phone_number)
            row['cell'].append('<span class="hidden">0</span>')
        else:
            row['cell'].append(donation.paid and donation.first_name or '<a href="#" class="show-edit" id="edit_sponsor_%s">%s</a>' % (donation.id, donation.first_name))
            row['cell'].append(donation.last_name)
            row['cell'].append(donation.email_address)
            row['cell'].append(donation.phone_number)
            row['cell'].append(donation.child.laps or 0)
        row['cell'].append("%01.2f" % (donation.donation or 0))
        row['cell'].append('<span abbr="total">%01.2f</span>' % (donation.total()))
        if donation.last_name == 'teacher':
            row['cell'].append('<span class="hidden">no</span>')
        else:
            row['cell'].append(donation.per_lap and 'yes' or 'no')
        row['cell'].append(donation.date_added.strftime('%m/%d/%Y'))
        row['cell'].append(donation.paid and '<span class="success">Paid</span>' or '<input type="checkbox" value="paid" name="paid" id="paid-%s" class="set-paid" title="If your Sponsor has paid you, you can makr their Donation as Paid." />' % donation.id)
        row['cell'].append('<input type="checkbox" value="%s" name="reminder" id="reminder-%s" class="set-reminder" />' % (donation.id, donation.id))
        result['rows'].append(row)
        count += 1
    return result

def _send_email_teamplate(template, data, mass=None):
    if data.has_key('body'):
        body = data['body']
    else:
        t = loader.get_template('email/%s.txt' % template)
        body = t.render(data)
    if mass:
        return data['subject'], body, settings.EMAIL_HOST_USER, [data['email_address']]
    else:
        send_mail(data['subject'], body, settings.EMAIL_HOST_USER, [data['email_address']])

def replace_space(string):
     # Replace all runs of whitespace with a single dash
     string = regexp.sub(r"\s+", '-', string.lower())

     return string

class BlogFeed(Feed):
    title = "Husky Hustle Site News"
    link  = "/nav/blog/"
    description = "Updates on changes and additions to huskyhustle.com."

    def items(self):
        return Blog.objects.order_by('-date_added')[:15]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.content

    def item_author_name(self, item):
        return item.author

    def item_pubdate(self, item):
        return item.date_added

    def item_link(self, item):
        domain = Site.objects.get_current().domain
        return 'http://%s/nav/blog/%d' % (domain, item.id)

