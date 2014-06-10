#!/usr/bin/env python
import os
import oauth2 as oauth
import urlparse

USER_AGENT = "discogstagger +http://github.com/jesseward"

class DiscogsAuth(object):
    ''' Returns an OAuth authentication handle for requests against the
        Discogs API. '''

    consumer_key = 'sxOsKeryYGLwrSsHtRVA'
    consumer_secret = 'npfUDQEVDgjNLPIqpSvcGyLWqaMcUaeX'

    request_token_url = 'http://api.discogs.com/oauth/request_token'
    authorize_url = 'http://www.discogs.com/oauth/authorize'
    access_token_url = 'http://api.discogs.com/oauth/access_token'

    def __init__(self):

        user = os.getenv("USER")
        if os.getenv("SUDO_USER") is not None:
            user = os.getenv("SUDO_USER")

        self.token_file = os.path.expanduser('~{0}/.config/discogstagger/token'.format(user))

        self.consumer = oauth.Consumer(self.consumer_key, self.consumer_secret)

        if not self.is_authenticated:
            self._get_request_token()

        self.access_token, self.access_token_secret = self._get_access_token()
        self.handle = self._return_handle()

    def _get_request_token(self):
        ''' completes the oauth handshakes for the request_token, verification and
            access_token. Then persists the access_token to disk. '''

        client = oauth.Client(self.consumer)
        resp, content = client.request(self.request_token_url, 'POST', headers={'user-agent': USER_AGENT })

        if resp['status'] != '200':
            raise Exception('Invalid response {0}.'.format(resp['status']))

        request_token = dict(urlparse.parse_qsl(content))

        auth = False

        while auth == False:
            print '=== ACTION REQUIRED ==='
            print 'In order to fetch images from discogs, you\'re required to grant the discogstagger application access to perform actions on behalf of your discogs account.'
            print 'Please visit {0}?oauth_token={1} and accept the authentication request'.format(
            self.authorize_url, request_token['oauth_token'])

            verification_code = raw_input('Please enter verification code provided at the above url:')
            token = oauth.Token(request_token['oauth_token'], request_token['oauth_token_secret'])
            token.set_verifier(verification_code)
            client = oauth.Client(self.consumer, token)

            resp, content = client.request(self.access_token_url, 'POST', headers={'user-agent': USER_AGENT })

            if resp['status'] != '200':
                raise Exception('Invalid response {0}.'.format(rep['status']))
            else:
                auth = True
        access_token = dict(urlparse.parse_qsl(content))

        with open(self.token_file, 'w') as fh:
            fh.write('{0}||{1}'.format(access_token['oauth_token'],
                access_token['oauth_token_secret']))

    def _return_handle(self):
        ''' returns an authenticated oauth Client handle. '''

        token = oauth.Token(key=self.access_token,
            secret=self.access_token_secret)
        return oauth.Client(self.consumer, token)

    def _get_access_token(self):

        with open(self.token_file, 'r') as fh:
            token = fh.read()
        return token.split('||')

    @property
    def is_authenticated(self):
        ''' return True is a token exists on the local file system. '''

        if os.path.isfile(self.token_file):
            return True
        else:
            return False
