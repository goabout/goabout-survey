#pylint: disable=bad-whitespace
"""
HAL relations used in the Go About API.
"""


RELATIONS_ROOT = 'http://rels.goabout.com/'
def rel(path):
    return RELATIONS_ROOT + path

TOKEN_URL  =   rel('oauth2-token')
AUTH_USER  =   rel('authenticated-user')
REGISTRATION = rel('registration')
USERS      =   rel('users')
USER       =   rel('user')
CLIENTS    =   rel('clients')
CLIENT     =   rel('client')
GEOCODER   =   rel('geocoder')
GEODECODER =   rel('geodecoder')
PLAN       =   rel('plan')
