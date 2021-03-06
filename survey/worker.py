#!/usr/bin/env python
#
# Import data into the elasticsearch-based geocoder

import argparse
import logging
import os
import sys
from ConfigParser import ConfigParser
from gettext import gettext
from datetime import datetime

import relations
from session import GoAboutSession, OAuth2Error, InsecureTransportError

import mandrill
from gdata.spreadsheet.service import SpreadsheetsService, CellQuery
from gdata.spreadsheet import SpreadsheetsCellsFeed

from requests.exceptions import HTTPError
from util import confirm


DEFAULT_CONFIG = '~/.goabout-survey.conf'

logger = logging.getLogger(__name__)


class CommandError(Exception):
    pass

class ArgumentParser(argparse.ArgumentParser):

    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(1, gettext('%s: error: %s\n') % (self.prog, message))


def send_survey(google, mandrill_client, config):

    spreadsheet_id = config.get('gdrive', 'spreadsheet_id')
    worksheet_id = config.get('gdrive', 'worksheet_id')
    spreadsheet = google.GetWorksheetsFeed(spreadsheet_id)
    worksheet = google.GetListFeed(spreadsheet_id, worksheet_id)

    query = CellQuery()
    query.min_row = '1'
    cells = google.GetCellsFeed(key=spreadsheet_id, wksht_id=worksheet_id, query=query)

    logger.info('Google Spreadsheet: %s; tab: %s', spreadsheet.title.text,
        cells.title.text)

    for row in worksheet.entry:
        try:
            logger.info('Sending mail to %s', row.custom['email'].text)

            if row.custom['status'].text:
                logger.info(' -- SKIPPING; status = %s', row.custom['status'].text)
                continue

            row = google.UpdateRow(row, {'status': 'PROCESSING'})

            message = { 'global_merge_vars':
                        [
                          { "name": "survey_url"
                          , "content": row.custom['survey'].text
                          }
                        ]
                      , 'merge': True
                      , 'merge_language': 'mailchimp'
                      , 'to':
                        [
                          { 'email':  row.custom['email'].text
                          , 'type': 'to'
                          }
                        ],
                      }

            mandrill_client.messages.send_template(
                    template_name='its-in-car-survey',
                    template_content=None,
                    message=message,
                    async=False)

            row = google.UpdateRow(row, {'status': 'DONE', 'send': "{}Z".format(datetime.utcnow().isoformat()), 'reason': ''})

        except Exception as e:
            logger.exception(e)
            row = google.UpdateRow(row, {'status': 'ERROR', 'send': '', 'reason': str(e)})






def import_data(session, google, config):
    users = list_users(session, config)
    spreadsheet_id = config.get('gdrive', 'spreadsheet_id')
    worksheet_id = config.get('gdrive', 'worksheet_id')

    spreadsheet = google.GetWorksheetsFeed(spreadsheet_id)
    worksheet = google.GetListFeed(spreadsheet_id, worksheet_id)

    logger.info('Working with Google Spreadsheet: %s; tab: %s',
            spreadsheet.title.text, worksheet.title.text)

    datafile = open(args.data, "r")
    lines = iter(datafile.readlines())

    for user in users:
        row = {
            'href': str(user.links['self'].url()),
            'email': str(user.properties['email']),
            'survey': next(lines).strip()
        }
        logger.debug("Inserting %s", row)
        google.InsertRow(row, spreadsheet_id, worksheet_id)

def clear(google, args, config):

    if not confirm(prompt='Trash all data?', resp=False):
        return

    spreadsheet_id = config.get('gdrive', 'spreadsheet_id')
    worksheet_id = config.get('gdrive', 'worksheet_id')

    spreadsheet = google.GetWorksheetsFeed(spreadsheet_id)
    worksheet = google.GetListFeed(spreadsheet_id, worksheet_id)

    logger.info('Working with Google Spreadsheet: %s; tab: %s',
            spreadsheet.title.text, worksheet.title.text)

    worksheet = google.GetListFeed(spreadsheet_id, worksheet_id)

    for row in reversed(worksheet.entry):
        logger.debug('deleting row for %s', row.custom['email'].text)
        google.DeleteRow(row)


def list_users(session, config):
    """
    List all users
    """
    logger.info("Fetching all users")
    root = session.hal_get(config.get('api', 'url'))
    if relations.USERS not in root.links:
        raise CommandError("No permission to add users")
    users_url = root.links[relations.USERS].url()

    try:
        users = session.hal_get(users_url)
        return users.embedded['item']
    except HTTPError, err:
        logger.error("(%s) Failure retrieving users: %s", err.response.status_code, err.response.text)



def connect_google_drive(config):
    logger.debug("Initialising client")
    username = config.get('gdrive', 'username')
    password = config.get('gdrive', 'password')
    gd_client = SpreadsheetsService(email=username, password=password)
    gd_client.source = 'GoAbout survey tool'
    gd_client.ProgrammaticLogin()

    return gd_client

def connect_api(config):
    try:
        credentials = dict(config.items('api'))
        return GoAboutSession(**credentials)
    except InsecureTransportError, err:
        fail("API must use HTTPS (or set OAUTHLIB_INSECURE_TRANSPORT=1)")
    except OAuth2Error, err:
        fail("authentication error: %s" % err.description)
    except CommandError, err:
        fail(err.message)

    fail("Something went horridly wrong!")

def connect_mandrill(config):
    return mandrill.Mandrill(config.get('mandrill', 'key'))

def parse_args(args=None):
    parser = ArgumentParser(
            description='Send every user a link to a survey.',
            formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-c', '--config', metavar='CONFIGFILE', dest='configfile',
            help='path to additional and authoritative configuration file')
    parser.add_argument('--import', metavar='DATA', dest='data',
            help='import url\'s from a datafile')
    parser.add_argument('--clear', dest='clear', action='store_true', help='remove data from the sheet')
    parser.add_argument('--send', dest='send', action='store_true', help='Actually send the emails!')

    parser.add_argument('-q', '--quiet', dest='quiet', action='store_true',
            help='makes this command quiet, outputting only errors. This also mutes --debug.')
    parser.add_argument('-d', '--debug', dest='debug', action='store_true',
            help='show debugging output')


    return parser.parse_args(args)


def parse_config(options=None):
    logger.info("Reading configuration files")
    parser = ConfigParser()
    locations = [ '/etc/goabout/goabout-survey.conf',  os.path.expanduser(DEFAULT_CONFIG) ]
    if options.configfile:
        locations.append(options.configfile)

    logger.debug("Trying for these locations: %s", locations)
    files = parser.read(locations)

    if len(files) <= 0:
        logger.error("Coudn't find any configuration, tried %s", locations)
    else:
        logger.info("Used %s for configuration", files)

    return parser

def setup_logging(args):


    loglevel = logging.INFO
    if args.quiet:
        loglevel = logging.ERROR
    elif args.debug:
        loglevel = logging.DEBUG

    logging.basicConfig(format='%(levelname)7s : %(message)s', level=logging.ERROR)

    logging.getLogger("survey").setLevel(loglevel)
    logging.getLogger("survey.session").setLevel(logging.ERROR)


def main():
    args = parse_args()
    setup_logging(args)
    config = parse_config(args)

    session = connect_api(config)
    google = connect_google_drive(config)
    mandrill = connect_mandrill(config)

    if (args.clear):
        clear(google, args, config)
        return

    if (args.data):
        import_data(session, google, config)
        return

    if (args.send):
        send_survey(google, mandrill, config)


    sys.exit(0)

if __name__ == '__main__':
    main()
