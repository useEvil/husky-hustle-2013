import os

from M2Crypto import BIO, SMIME, X509

from django.conf import settings

cwd = os.path.dirname(os.path.realpath(__file__))
PAYPAL_PAYPAL_CERT = os.path.join(cwd, settings.PAYPAL_PAYPAL_CERT)
PAYPAL_PRIVATE_KEY = os.path.join(cwd, settings.PAYPAL_PRIVATE_KEY)
PAYPAL_PUBLIC_KEY = os.path.join(cwd, settings.PAYPAL_PUBLIC_KEY)


class PayPalError(Exception):
    '''Base class for PayPal errors'''

    @property
    def message(self, message=''):
        '''Returns the first argument used to construct this error.'''
        return message

class PayPal(object):

    def encrypt(self, attributes):
        plaintext = ''

        for key, value in attributes.items():
            plaintext += u'%s=%s\n' % (key, value)

        plaintext = plaintext.encode('utf-8')

        # Instantiate an SMIME object.
        s = SMIME.SMIME()

        # Load signer's key and cert. Sign the buffer.
        s.load_key_bio(BIO.openfile(PAYPAL_PRIVATE_KEY), BIO.openfile(PAYPAL_PUBLIC_KEY))

        p7 = s.sign(BIO.MemoryBuffer(plaintext), flags=SMIME.PKCS7_BINARY)

        # Load target cert to encrypt the signed message to.
        x509 = X509.load_cert_bio(BIO.openfile(PAYPAL_PAYPAL_CERT))
        sk = X509.X509_Stack()
        sk.push(x509)
        s.set_x509_stack(sk)

        # Set cipher: 3-key triple-DES in CBC mode.
        s.set_cipher(SMIME.Cipher('des_ede3_cbc'))

        # Create a temporary buffer.
        tmp = BIO.MemoryBuffer()

        # Write the signed message into the temporary buffer.
        p7.write_der(tmp)

        # Encrypt the temporary buffer.
        p7 = s.encrypt(tmp, flags=SMIME.PKCS7_BINARY)

        # Output p7 in mail-friendly format.
        out = BIO.MemoryBuffer()
        p7.write(out)

        return out.read()

    def download_csv(self, start_date=None, end_date=None):
        try:
            results = getHttpRequest(settings.PAYPAL_IPN_URL, 'cmd=TransactionSearch&STARTDATE=%s&ENDDATE=%s' % (start_date, end_date))
        except Exception, e:
            print 'Failed to Download Transactions'
        return results
