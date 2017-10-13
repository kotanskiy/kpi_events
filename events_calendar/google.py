from __future__ import print_function
import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

import datetime

try:
    import argparse
    flags = tools.argparser.parse_args([])
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/calendar-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/calendar'
CLIENT_SECRET_FILE = 'events_calendar/client_secret.json'
APPLICATION_NAME = 'KPI Events'


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'calendar-python.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def transform_datetime(date, start_date):
    try:
        result = str(date.strftime('%Y-%m-%dT%H:%M:%S'))
    except AttributeError:
        new_date = start_date + datetime.timedelta(hours=3)
        result = str(new_date.strftime('%Y-%m-%dT%H:%M:%S'))
    return result

def create_event(event):
    """Shows basic usage of the Google Calendar API.

    Creates a Google Calendar API service object and outputs a list of the next
    10 events on the user's calendar.
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)

    event = {
        'summary': event.name,
        'location': event.place_of_event,
        'description': event.description,
        'start': {
            'dateTime': transform_datetime(event.start_date, event.start_date),
            'timeZone': 'Europe/Kiev',
        },
        'end': {
            'dateTime': transform_datetime(event.end_date, event.start_date),
            'timeZone': 'Europe/Kiev',
        },
        'recurrence': [
            'RRULE:FREQ=DAILY;COUNT=1'
        ],
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 24 * 60},
                {'method': 'popup', 'minutes': 10},
            ],
        },
    }

    event = service.events().insert(calendarId='primary', body=event).execute()
    print('Event created: %s' % (event.get('htmlLink')))
