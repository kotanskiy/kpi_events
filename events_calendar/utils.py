from ast import literal_eval
from datetime import timedelta

import httplib2
from django.shortcuts import get_object_or_404
from googleapiclient import discovery
from oauth2client.client import flow_from_clientsecrets


from re import sub

from events_calendar.models import Event, Index
from kpi_events import settings


def delete_indexes():
    Index.objects.all().delete()
    print("All indexes deleted")


def split_str(string):
    return set(str.upper(sub(r'[^a-zA-Zа-яА-Я0-9 ]', r'', string).replace("  ", " ")).split(" "))


def create_indexes():
    last_pk = Event.objects.order_by('-pk')[0].pk
    indexes = {}
    for i in range(1, last_pk+1):
        try:
            event = get_object_or_404(Event, pk=i)
            words = split_str(event.description + " " + event.name)
            for word in words:
                if len(word) > 1:
                    if not indexes.get(word):
                        indexes[word] = set()
                    indexes[word].add(event.pk)
        except:
            pass
    for key in indexes:
        Index.objects.create(word=key, links=indexes[key])
        print("For {0} created index {1}".format(key, indexes[key]))


def add_index(pk):
    event = get_object_or_404(Event, pk=pk)
    words = split_str(event.description + " " + event.name)
    for word in words:
        if len(word) > 1:
            indexes = set()
            try:
                values = get_object_or_404(Index, word=word)
                indexes = literal_eval(values.links)
                indexes.add(pk)
                Index.objects.filter(word=word).update(links=indexes)
            except:
                indexes.add(pk)
                Index.objects.create(word=word, links=indexes)


def find(request):
    search_words = split_str(request)
    result = []
    for key in search_words:
        try:
            values = get_object_or_404(Index, word=key)
            result.append(literal_eval(values.links))
            rez = result[0]
            for i in range(len(result) - 1):
                rez = set(rez) & set(result[i + 1])
            events = []
            # time = datetime.now()
            for i in rez:
                events.append(Event.objects.get(pk=i, published=True))
                # event = Event.objects.get(pk=i)
                # if (time < event.end_date):
                #     events.append(event)
            return events
        except:
            return []

def update():
    delete_indexes()
    create_indexes()

FLOW = flow_from_clientsecrets(
    settings.GOOGLE_OAUTH2_CLIENT_SECRETS_JSON,
    scope='https://www.googleapis.com/auth/calendar',
    redirect_uri='https://events.kpi.ua/oauth2callback')

FLOW.params['access_type'] = 'offline'         # offline access
FLOW.params['include_granted_scopes'] = 'true' # incremental auth
FLOW.params['prompt']='consent'

def transform_datetime(date, start_date):
    try:
        result = str(date.strftime('%Y-%m-%dT%H:%M:%S'))
    except AttributeError:
        new_date = start_date + timedelta(hours=3)
        result = str(new_date.strftime('%Y-%m-%dT%H:%M:%S'))
    return result

def create_event_for_google_calendar(credential, event_id, request):
    event = get_object_or_404(Event, pk=event_id)
    # if not event:
    #     print('Мы не получили event через event_id')
    http = credential.authorize(httplib2.Http())
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
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 24 * 60},
                {'method': 'popup', 'minutes': 10},
            ],
        },
    }

    event = service.events().insert(calendarId='primary', body=event).execute()
    if event not in request.user.profile.google_calendar_events.all():
        request.user.profile.google_calendar_events.add(event_id)
    print('Event created: %s' % (event.get('htmlLink')))
