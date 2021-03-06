"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to templates as 'h'.
"""
# Import helpers as desired, or define your own, ie:
#from webhelpers.html.tags import checkbox, password
import cgi
import locale
import datetime as date

from functools import wraps
from urllib import urlencode
from urllib2 import Request, urlopen
from socket import setdefaulttimeout
from django.http import HttpResponse, HttpResponseRedirect

try:
    from husky.models import Parent
except:
    pass


SHORT_DATE_FORMAT = '%Y-%m-%d'
LONG_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S'


def joinParts(*parts):
    return "_".join(parts)

def escapeValue(obj, elem=None):
    if elem:
        return cgi.escape(obj.__dict__[elem])
    else:
        return cgi.escape(obj)

def makeMoney(money):
    locale.setlocale( locale.LC_ALL, 'en_US' )
    return locale.currency(money, grouping=True)

def getColumnOne(monitors=[]):
    length = len(monitors)
    sets = (length / 2) + (length % 2)
    rows = [ ]
    for i in range(sets):
        rows.append(monitors[i])
    return rows

def getColumnTwo(monitors=[], prefs=None):
    length = len(monitors)
    sets = (length / 2) + (length % 2)
    rows     = [ ]
    for i in range(sets, length):
        rows.append(monitors[i])
    return rows

def dictToObject(obj, dict={}):
    for elem in dict.keys():
        if elem.startswith('_'):
            continue
        else:
            if dict[elem]: setattr(obj, elem, dict[elem])
    return obj

def checkUser(view_func):
    def _decorator(request, *args, **kwargs):
        if request.user.is_authenticated and hasattr(request.user, 'email'):
            try:
                getParent(request)
            except:
                return HttpResponseRedirect('/accounts/logout')
            finally:
                pass
        response = view_func(request, *args, **kwargs)
        return response
    return wraps(view_func)(_decorator)

def prevPhoto(list, index=0):
    index = int(index) - 1
    try:
        if index > 0:
            return list[index]
    except:
        pass
    return None

def nextPhoto(list, index=0):
    index = int(index) + 1
    try:
        return list[index]
    except:
        pass
    return None

def getParent(request):
    try:
        return Parent.objects.filter(email_address=request.user.email).get()
    except:
        return None

def printLog(message, debug=False):
    if not debug: return
    log = file('/home/useevil/logs/django.log', 'a')
    print >>log, message
    log.flush()
    log.close()

def getHttpRequest(uri=None, data=None):
    setdefaulttimeout(3)
    req = Request(uri, data)
    response = urlopen(req)
    content = ''
    try: content = response.read()
    except Exception, e: print "Failed to content: "%(e.reason)
    return content
