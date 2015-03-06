#pylint: disable=undefined-variable,unused-import,star-args,unused-argument
"""
Session wrapper for OAuth2 authentication against the Go About API
"""


import logging

from dougrain import Document
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient, LegacyApplicationClient
from oauthlib.oauth2.rfc6749.errors import OAuth2Error, InsecureTransportError

import survey.relations as rels
from survey.util import display_str


MAX_DISPLAY = 4096

LOGGER = logging.getLogger(__name__)


class GoAboutSession(OAuth2Session):
    """
    Requests session object that authenticates to the Go About API.

    The authentication happens immediately in the constructor, which is
    a blocking operation.
    """
    def __init__(self, url, client_id, client_secret,
                 user_email=None, user_password=None):
        self.url = url
        self.credentials = {
            'client_id': client_id,
            'client_secret': client_secret,
        }
        if user_email is not None:
            client = LegacyApplicationClient(client_id)
            self.credentials.update({
                'username': user_email,
                'password': user_password,
            })
        else:
            client = BackendApplicationClient(client_id)
        super(GoAboutSession, self).__init__(client=client)

        root_doc = self.hal_get(self.url)
        token_url = root_doc.links[rels.TOKEN_URL].url()
        self.fetch_token(token_url=token_url, **self.credentials)

    def request(self, method, url, raise_for_status=True, **kwargs):
        """
        Perform a HTTP request.
        """
        response = super(GoAboutSession, self).request(method, url, **kwargs)
        LOGGER.debug('received: %s', display_str(response.content, MAX_DISPLAY))
        if raise_for_status:
            response.raise_for_status()
        return response

    def hal_request(self, method, url, **kwargs):
        """
        Perform a HTTP request and parse the response body as a HAL
        representation.
        """
        response = self.request(*args, **kwargs)
        return Document.from_object(response.json())

    def hal_get(self, url, **kwargs):
        """
        Perform a HTTP GET request and parse the response body as a HAL
        representation.
        """
        response = self.get(url, **kwargs)
        return Document.from_object(response.json())

    def hal_post(self, url, **kwargs):
        """
        Perform a HTTP POST request and parse the response body as a
        HAL representation.
        """
        response = self.post(url, **kwargs)
        return Document.from_object(response.json())

    def hal_put(self, url, **kwargs):
        """
        Perform a HTTP PUT request and parse the response body as a HAL
        representation.
        """
        response = self.put(url, **kwargs)
        return Document.from_object(response.json())
