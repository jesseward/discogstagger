#!/usr/bin/env python
import os

import discogs_client as dc

USER_AGENT = "discogstagger +http://github.com/jesseward"


class DiscogsWrapper(object):
    ''' Returns an OAuth authentication handle for requests against the
        Discogs API. '''

    consumer_key = 'sxOsKeryYGLwrSsHtRVA'
    consumer_secret = 'npfUDQEVDgjNLPIqpSvcGyLWqaMcUaeX'

    def __init__(self):

        user = os.getenv("USER")
        if os.getenv("SUDO_USER") is not None:
            user = os.getenv("SUDO_USER")

        self.token_file = os.path.expanduser('~{0}/.config/discogstagger/token'.format(user))

        if self.is_authenticated:
            token, secret = self._get_access_token()
            self.discogs = dc.Client(USER_AGENT, consumer_key=self.consumer_key,
                    consumer_secret=self.consumer_secret, token=token,
                    secret=secret)
        # otherwise handle authentication process.
        else:
            self.discogs = dc.Client(USER_AGENT)
            self._get_request_token()


    def _get_request_token(self):
        """
        completes the oauth handshakes for the request_token, verification and
        access_token. Then persists the access_token to disk.
        """

        self.discogs.set_consumer_key(self.consumer_key, self.consumer_secret)
        token, secret, url = self.discogs.get_authorize_url()

        auth = False

        while auth == False:
            print '=== ACTION REQUIRED ==='
            print 'In order to fetch images from discogs, you\'re required to grant the discogs-banner application access to perform actions on behalf of your discogs account.'
            print 'Please visit {url} and accept the authentication request'.format(
                   url=url)

            verification_code = raw_input('Verification code :').decode('utf8')

            try:
                access_token, access_secret = self.discogs.get_access_token(
                        verification_code)
            except HTTPError:
                print 'Unable to authenticate.'
                raise

            if access_token:
                auth = True

        # persist token to disk.
        with open(self.token_file, 'w') as fh:
            fh.write('{token}||{secret}'.format(token=access_token, secret=
                    access_secret))

    def _get_access_token(self):
        """
        :return: two strings str a = auth token, str b = auth token secret
        """

        with open(self.token_file, 'r') as fh:
            token, secret = fh.read().split('||')

        return token.decode('utf8'), secret.decode('utf8')

    @property
    def is_authenticated(self):
        """ return True is a token exists on the local file system. """

        # very rudimentary check. Simply ensures the file exists on the local
        # disk.
        if os.path.isfile(self.token_file):
            return True
