import pytz
import base64
import django.contrib.staticfiles
import gdata.photos.service as gdata
import husky.helpers as h
import datetime as date
import re as regexp

from django.db.models import Count, Sum, Avg
from django.core.mail import send_mail
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
from django.contrib.sites.models import Site, get_current_site
from django.contrib.syndication.views import Feed
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.conf import settings

from socialregistration.contrib.facebook.models import FacebookProfile
from socialregistration.contrib.twitter.models import TwitterProfile

from husky.models import Parent, Children, Donation, Teacher, Grade, Album, Photo, Blog, Message, Link, Calendar
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
        try:
            parent  = Parent.objects.filter(email_address=request.user.email).get()
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
            motd=Message.objects.get(),
            bar_height=Donation().bar_height(),
            arrow_height=Donation().arrow_height(),
            calendar=Calendar().get_events(),
    ))
    return render_to_response('index.html', c, context_instance=RequestContext(request))

@checkUser
def nav(request, page='index', id=None):
    matched     = regexp.compile(r"^/nav/(?P<page_title>\w+)").match(request.path).groupdict()
    parent      = None
    my_twitter  = None
    my_facebook = None
    my_google   = None
    if request.user.is_authenticated:
        try:
            parent  = Parent.objects.filter(email_address=request.user.email).get()
            my_facebook = parent.facebook()
            my_twitter  = parent.twitter()
            my_google   = parent.google()
        except:
            pass
    c = Context(dict(
            page_title=matched['page_title'].title(),
            parent=parent,
            my_facebook=my_twitter,
            my_twitter=my_twitter,
            my_google=my_google,
            bar_height=Donation().bar_height(),
            arrow_height=Donation().arrow_height(),
    ))
    if matched['page_title'] == 'photos':
        c['albums'] = Album()
    elif matched['page_title'] == 'links':
        c['links'] = Link.objects.filter(status=1).all()
    elif matched['page_title'] == 'blog':
        if id:
            c['entries'] = [ Blog.objects.get(pk=id) ]
        else:
            c['entries'] = Blog.objects.order_by('-date_added')[:15]
    return render_to_response('%s.html'%page, c, context_instance=RequestContext(request))

@login_required(login_url='/accounts/login/')
def account(request, identifier=None):
    parent = Parent.objects.filter(email_address=request.user.email).get()
    c = Context(dict(
            page_title='Profile',
            parent=parent,
            my_facebook=parent.facebook,
            my_twitter=parent.twitter,
            my_google=parent.google,
            teachers=Teacher.objects.all(),
            facebook_api=settings.FACEBOOK_APP_ID
    ))
    if identifier:
        try:
            child  = Children.objects.get(identifier=identifier)
            c['child'] = child
            c['messages'] = messages.get_messages(request)
            c['page_title'] = '%s' % (child)
            return render_to_response('account/donations.html', c, context_instance=RequestContext(request))
        except:
            messages.error(request, 'Could not find Child for identity: %s' % identifier)
    c['messages'] = messages.get_messages(request)
    return render_to_response('account/index.html', c, context_instance=RequestContext(request))

def donation_sheet(request, identifier=None):
    c = Context(dict(
            page_title='Donation Sheet',
    ))
    if identifier and identifier == 'pdf':
        template = loader.get_template('account/donation_sheet.html')
        response = HttpResponse(mimetype='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="donation-sheet.pdf"'
        response.write(file("/tmp/donation-sheet.pdf"))
        p = canvas.Canvas(response)
        p.showPage()
        p.save()
        return response
    elif identifier:
        try:
            child  = Children.objects.get(identifier=identifier)
            c['child'] = child
            c['page_title'] = 'Donation Sheet: %s' % (child)
        except:
            messages.error(request, 'Could not find Child for identity: %s' % identifier)
    c['messages'] = messages.get_messages(request)
    return render_to_response('account/donation_sheet.html', c, context_instance=RequestContext(request))

def make_donation(request, identifier=None):
    c = Context(dict(
            page_title='Donate',
            make_donation=True,
    ))
    try:
        child = Children.objects.get(identifier=identifier)
        c['child'] = child
    except:
        messages.error(request, 'Could not find Child for identity: %s' % identifier)
        c['error'] = True
    c['messages'] = messages.get_messages(request)
    return render_to_response('donate.html', c, context_instance=RequestContext(request))

def teacher_donation(request, identifier=None):
    c = Context(dict(
            page_title='Donate',
            make_donation=True,
            teacher_donation=True,
    ))
    try:
        child = Children.objects.get(identifier=identifier)
        c['child'] = child
    except:
        messages.error(request, 'Could not find Child for identity: %s' % identifier)
        c['error'] = True
    c['messages'] = messages.get_messages(request)
    return render_to_response('donate.html', c, context_instance=RequestContext(request))

@login_required(login_url='/accounts/login/')
def donate(request, child_id=None):
    child  = Children.objects.get(identifier=child_id)
    c = Context(dict(
            page_title='Donator',
            child=child,
            donate=True,
    ))
    if request.POST:
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
                    date_added=date.datetime.now(),
                    child=child,
                )
                donation.save()
                messages.success(request, 'Thank you for making a Donation')
                c['success'] = True
            except Exception, e:
                messages.error(request, str(e))
        else:
            messages.error(request, 'Failed to Donator')
        c['form'] = form
    c['messages'] = messages.get_messages(request)
    if request.POST.get('make_donation'):
        if request.POST.get('teacher_donation'):
            c['teacher_donation'] = True
    return render_to_response('donate.html', c, context_instance=RequestContext(request))

@checkUser
def album(request, album_id=None):
    album = Album().get_album(album_id)
    c = Context(dict(
            page_title=album.title.text,
            album=album
    ))
    return render_to_response('photos.html', c, context_instance=RequestContext(request))

@checkUser
def photo(request, album_id=None, photo_id=None):
    album = Album().get_album(album_id)
    photo = Photo().get_photo(album_id, photo_id)
    c = Context(dict(
            page_title=photo.title.text,
            photo_album=album,
            photo=photo
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
                user    = form.save(form['email_address'].data, form['password1'].data)
                key     = base64.urlsafe_b64encode('%s-%s' % (form['last_name'].data, form['email_address'].data))
                expires = date.datetime.now() + date.timedelta(settings.ACCOUNT_ACTIVATION_DAYS)
                parent  = Parent(
                                first_name=form['first_name'].data,
                                last_name=form['last_name'].data,
                                email_address=form['email_address'].data,
                                phone_number=form['phone_number'].data,
                                activation_key=key,
                                key_expires=expires,
                                date_added=date.datetime.now(),
                                site=Site.objects.get_current(),
                                user=user,
                            )
                parent.save()
                c['key'] = key
                c['parent_name'] = parent.full_name
                c['email_address'] = parent.email_address
                c['subject'] = 'Husky Hustle: Parent Registration'
                _send_email_teamplate('register-activation', c)
                messages.success(request, 'Successfully Registered Account')
                auth = authenticate(username=form['email_address'].data, password=form['password1'].data)
                login(request, auth)
            except Exception, e:
                messages.error(request, 'Failed to Register Account: %s' % str(e))
                c['form'] = form
                c['messages'] = messages.get_messages(request)
                return render_to_response('registration/registration_form.html', c, context_instance=RequestContext(request))
    else:
        form = ParentRegistrationForm()
        messages.error(request, 'Failed to Register Account')
        c['form'] = form
        c['messages'] = messages.get_messages(request)
        return render_to_response('registration/registration_form.html', c, context_instance=RequestContext(request))
    return HttpResponseRedirect('/account/')

def activate(request, key=None):
    c = Context(dict(
            page_title='Home',
    ))
    template = 'registration/login.html'
    try:
        user = User.objects.filter(parent__activation_key=key).get()
    except Exception, e:
        messages.error(request, 'Failed to Activate Account: %s' % str(e))
        user = None
    if user:
        if user.is_active:
            messages.error(request, 'Account already Activated')
        elif user.parent.key_expires < date.datetime.today(pytz.utc):
            messages.error(request, 'Activation Key has already Expired.  Please Re-Register.')
            template = 'registration/registration_form.html'
        else:
            user.is_active = True
            user.save()
            c['subject'] = 'Husky Hustle: Account Activated'
            c['parent_name'] = user.parent.full_name
            c['email_address'] = user.parent.email_address
            _send_email_teamplate('register-parent', c)
            messages.success(request, 'Account Activated')
    c['messages'] = messages.get_messages(request)
    return render_to_response(template, c, context_instance=RequestContext(request))

def contact(request):
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
    c = Context({'form': form, 'messages': messages.get_messages(request), 'page_title': 'Contact'})
    return render_to_response('contact.html', c, context_instance=RequestContext(request))

@login_required(login_url='/accounts/login/')
def add(request, type=None):
    parent = Parent.objects.filter(email_address=request.user.email).get()
    c = Context(dict(
            page_title='Profile',
            parent=parent,
            my_facebook=parent.facebook,
            my_twitter=parent.twitter,
            my_google=parent.google,
            teachers=Teacher.objects.all(),
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
                    identifier='%s-%s-%s'%(request.POST.get('first_name').lower(), request.POST.get('last_name').lower(), teacher.room_number),
                    date_added=date.datetime.now(),
                    teacher=teacher,
                    parent=parent,
                )
                child.save()
                c['child_name'] = child.full_name
                c['parent_name'] = parent.full_name
                c['email_address'] = parent.email_address
                c['child_identifier'] = child.identifier
                c['subject'] = 'Husky Hustle: Child Registration'
                _send_email_teamplate('register-child', c)
                messages.success(request, 'Child Added')
            except Exception, e:
                messages.error(request, str(e))
        else:
            messages.error(request, 'Failed to Add Child')
        c['form'] = form
    c['messages'] = messages.get_messages(request)
#    return HttpResponseRedirect('/accounts/profile/')
    return render_to_response('account/index.html', c, context_instance=RequestContext(request))

def edit(request, type=None):
    if request.POST:
        if type == 'child':
            try:
                teacher = Teacher.objects.get(pk=request.POST.get('teacher')),
                child = Children.objects.get(pk=request.POST.get('id'))
                child.first_name = request.POST.get('first_name')
                child.last_name = request.POST.get('last_name')
                child.teacher = teacher
                child.identifier = '%s-%s-%s'%(request.POST.get('first_name').lower(), request.POST.get('last_name').lower(), teacher.room_number)
                child.save()
                messages.success(request, 'Successfully Updated Child')
            except Exception, e:
                messages.error(request, 'Failed to Update Child: %s' % str(e))
        elif type == 'profile':
            try:
                parent = Parent.objects.filter(email_address=request.user.email).get()
                parent.first_name = request.POST.get('first_name')
                parent.last_name = request.POST.get('last_name')
                parent.email_address = request.POST.get('email_address')
                parent.phone_number = request.POST.get('phone_number')
                user = parent.user
                user.email = request.POST.get('email_address')
                user.username = request.POST.get('email_address')
                user.save()
                parent.save()
                messages.success(request, 'Successfully Updated Profile')
            except Exception, e:
                messages.error(request, 'Failed to Update Profile: %s' % str(e))
        elif type == 'sponsor':
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

def reminders(request):
    c = Context(dict(
            subject='Husky Hustle: Parent Registration',
    ))
    donators = request.POST.getlist('donators')
    if request.POST.get('custom_message'):
        c['custom_message'] = request.POST.get('custom_message')
    for donator in donators:
        donation = Donation.objects.get(pk=donator)
        c['name'] = donation.full_name
        c['email_address'] = donation.email_address
        c['child_name'] = donation.child.full_name
        c['child_identifier'] = donation.child.identifier
        _send_email_teamplate('reminder', c)
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
    object = Donation.objects.get(pk=donation_id)
    object.paid = True
    object.save()
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




def reporting(request, type=None):
    c = Context(dict(
            page_title='Reporting',
    ))
    return render_to_response('admin/bar_chart.html', c, context_instance=RequestContext(request))

def reports(request, type=None):
    json = {
        'label': ['label A', 'label B', 'label C', 'label D'],
        'values': []
    }
    if type == 'most-laps':
        grades = Grade.objects.all()
        for grade in grades:
            num_laps = Children.objects.filter(grade=grade).aggregate(num_laps=Sum('laps'))
            json['values'].append({'label': grade.title, 'values': [num_laps['num_laps']]})
    return HttpResponse(simplejson.dumps(json), mimetype='application/json')


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
            row['cell'].append('<a href="#" class="show-edit" id="edit_sponsor_%s">%s</a>' % (donation.id, donation.first_name))
            row['cell'].append(donation.last_name)
            row['cell'].append(donation.email_address)
            row['cell'].append(donation.phone_number)
            row['cell'].append(donation.child.laps or 0)
        row['cell'].append("%01.2f" % (donation.donation or 0))
        row['cell'].append("%01.2f" % (donation.total()))
        if donation.last_name == 'teacher':
            row['cell'].append('<span class="hidden">no</span>')
        else:
            row['cell'].append(donation.per_lap and 'yes' or 'no')
        row['cell'].append(donation.date_added.strftime('%m/%d/%Y'))
        row['cell'].append(donation.paid and '<span class="success">Paid</span>' or '<input type="checkbox" value="paid" name="paid" id="paid-%s" class="set-paid" alt="Mark as Paid" />' % donation.id)
        row['cell'].append('<input type="checkbox" value="%s" name="reminder" id="reminder-%s" class="set-reminder" />' % (donation.id, donation.id))
        result['rows'].append(row)
        count += 1
    return result

def _send_email_teamplate(template, data):
    t = loader.get_template('email/%s.txt' % template)
    send_mail(data['subject'], t.render(data), settings.EMAIL_HOST_USER, [data['email_address']])


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


