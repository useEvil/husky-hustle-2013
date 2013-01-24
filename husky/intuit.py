import urllib, urllib2
import urlparse
import string
try:
   import simplejson
except ImportError:
   import json as simplejson

from re import findall

INTUIT_BASE_URL = "https://paymentservices.ptcfe.intuit.com"
INTUIT_BASE_INIT_PATH = '/paypage/ticket/create?'
INTUIT_BASE_PAYPAGE_PATH = '/checkout/terminal?'
INTUIT_BASE_CAPTURE_PATH = '/paypage/capture?'
# Prod
INTUIT_AUTH_TICKET = 'SDK-TGT-170-9JataYuTa8Nd5OWc59DVtQ'
INTUIT_APP_LOGIN = 'huskypaymentsprod.www.huskyhustle.com'
INTUIT_APP_ID = 584692585
# Dev
#INTUIT_AUTH_TICKET = 'SDK-TGT-32-ltjSwnvLt3BLTIom46ZQHQ'
#INTUIT_APP_LOGIN = 'huskypayments.www.huskyhustle.com'
#INTUIT_APP_ID = 235888342

VERBS_PARAM = { 
        'INIT': {
            'AuthModel': 'desktop',
            'AppLogin': INTUIT_APP_LOGIN,
            'AuthTicket': INTUIT_AUTH_TICKET,
            'TxnType': 'Sale',
            'Amount': None,
        },
        'PAYPAGE': {
            'Ticket': None,
            'OpId': None,
            'action': 'checkout',
        },
        'CAPTURE': {
            'AuthModel': 'desktop',
            'AppLogin': INTUIT_APP_LOGIN,
            'AuthTicket': INTUIT_AUTH_TICKET,
            'OpId': None,
            'TxnId': None,
        },
}

class IntuitError(Exception):
    '''Base class for Intuit errors'''

    @property
    def message(self, message=''):
        '''Returns the first argument used to construct this error.'''
        return message

class Intuit(object):
    def initiate_payment(self, amount=0.00):
        params = VERBS_PARAM['INIT']
        params['Amount'] = amount
        url = INTUIT_BASE_URL + INTUIT_BASE_INIT_PATH
        code, content = self._makeRequest(url, params)
#        print '==== content [%s]'%(content)
        try: ticket = findall("Ticket=(.+)\n", content)[0]
        except IndexError: print 'Ticket Not Found'; sys.exit()
        try: op_id = findall("OpId=(.+)\n", content)[0]
        except IndexError: print 'OpId Not Found'; sys.exit()
        return ticket, op_id

    def paypage_url(self, ticket=None, op_id=None):
        if not ticket and not op_id: return
        params = VERBS_PARAM['PAYPAGE']
        params['Ticket'] = ticket
        params['OpId'] = op_id
        url = INTUIT_BASE_URL + INTUIT_BASE_PAYPAGE_PATH
        code, content = self._makeRequest(url, params)
        print '==== content [%s]'%(content)
        try: ticket = findall("Ticket=(.+)\n", content)[0]
        except IndexError: print 'Ticket Not Found'; sys.exit()
        try: op_id = findall("OpId=(.+)\n", content)[0]
        except IndexError: print 'OpId Not Found'; sys.exit()
        return ticket, op_id

    def _makeRequest(self, uri=None, data=None):
        if not uri and not data: return
        """ sends data to CloudZilla System """
        data = urllib.urlencode(data)
        request = urllib2.Request(uri, data)
        try:
            response = urllib2.urlopen(request)
            code     = response.code
            content  = response.read()
        except urllib2.URLError, e:
            print 'Failed to get Authenticated Session'
            raise IntuitError, e
            sys.exit()
        return code, content


if __name__ == '__main__':
    intuit = Intuit()
    ticket, op_id = intuit.initiate_payment(5.00)
    url = intuit.paypage_url(ticket, op_id)
    print "Ticket = %s" % ticket
    print "OpID   = %s" % op_id
