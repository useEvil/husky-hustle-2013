import os
import sys

from urllib import urlencode
from urllib2 import Request, urlopen
from socket import setdefaulttimeout
from subprocess import call


HOST = 'www.huskyhustle.com'
PRINTER = 'Brother_MFC_9460CDN'
# HOST = 'dev.husky-hustle.com'
# PRINTER = 'PDFwriter'

class PrintPDF(object):

    def getChildren(self, id=None):
        uri = 'http://%s/REST/children/?format=json' % HOST
        if id:
            uri = 'http://%s/REST/children/%s/?format=json' % (HOST, id)
        content = self.getHttpRequest(uri)
        content = content.replace('null', 'None')
        json = eval(content)
        return id and [json] or json

    def pledgeForms(self, id=None):
        children = self.getChildren(id)
        for child in children:
            print 'Printing: %s' % child['identifier']
            uri = "http://%s/donation_sheet/%s/final" % (HOST, child['identifier'])
            cmd = 'wkpdf --source=%s --output=docs/pledge-sheet-%s.pdf --stylesheet-media="screen" --paper=tabloid' % (uri, child['identifier'])
            call(cmd, shell=True)
#            cmd = 'lp -d "%s" -o media=Legal -o natural-scaling=115 docs/pledge-sheet-%s.pdf' % (PRINTER, child['identifier'])
#            call(cmd, shell=True)

    def getHttpRequest(self, uri=None, data=None):
        setdefaulttimeout(3)
        req = Request(uri, data)
        response = urlopen(req)
        content = ''
        try: content = response.read()
        except Exception, e: print "Failed to content: "%(e.reason)
        return content

if __name__ == '__main__':
    id = sys.argv[1] or None
    pr_pdf = PrintPDF()
    pr_pdf.pledgeForms(id)

    print 'Finished printing Pledge Forms'
