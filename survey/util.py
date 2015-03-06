"""
Utilities, intended to be used by any module.
"""

def display_str(data, max_length=0):
    if 0 < max_length < 5:
        raise ValueError("max_length must be 0 or > 5")
    string = repr(data)
    if len(string) > max_length:
        string = string[:max_length-4] + "...'"
    return string


def format_as_curl(response):

    headers = ""
    if len(response.request.headers) > 0:
        headers = '-H' + ' -H'.join("'%s: %s'" % h for h in response.request.headers.items())

    method = ''
    payload = ''
    if response.request.method != 'GET':
        method = '-X %s ' % response.request.method
        payload = " -d'%s'" % response.request.body.replace("'", "\\'")


    return "curl %s%s%s '%s'" % (method, headers, payload, response.request.url)


def confirm(prompt=None, resp=False):
    """prompts for yes or no response from the user. Returns True for yes and
    False for no.

    'resp' should be set to the default value assumed by the caller when
    user simply types ENTER.

    >>> confirm(prompt='Create Directory?', resp=True)
    Create Directory? [y]|n:
    True
    >>> confirm(prompt='Create Directory?', resp=False)
    Create Directory? [n]|y:
    False
    >>> confirm(prompt='Create Directory?', resp=False)
    Create Directory? [n]|y: y
    True

    """

    if prompt is None:
        prompt = 'Confirm'

    if resp:
        prompt = '%s [%s]|%s: ' % (prompt, 'y', 'n')
    else:
        prompt = '%s [%s]|%s: ' % (prompt, 'n', 'y')

    while True:
        ans = raw_input(prompt)
        if not ans:
            return resp
        if ans not in ['y', 'Y', 'n', 'N']:
            print 'please enter y or n.'
            continue
        if ans == 'y' or ans == 'Y':
            return True
        if ans == 'n' or ans == 'N':
            return False
