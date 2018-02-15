from __future__ import print_function
import logger as l
import httplib2
import os
import facebook
import allevents
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
import json
import datetime
from datetime import timedelta
from bs4 import BeautifulSoup
import requests
from dateutil import parser
import pytz
try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

logger = l.setup_custom_logger(__name__)

SCOPES = 'https://www.googleapis.com/auth/calendar'
CLIENT_SECRET_FILE = 'configs/client_secret.json'
APPLICATION_NAME = 'Google Calendar API Python Quickstart'

def get_credentials():
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir,'.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,'calendar-python-quickstart.json')

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

def build_event(id, name, description, rsvp_status, start_time, end_time, location):
    event = {}
    event['start'] = {}
    event['end'] = {}
    event['attachments'] = {}
    event['attendees'] = {}
    start_str = start_time.strftime('%Y-%m-%dT%H:%M:%S')
    end_str = end_time.strftime('%Y-%m-%dT%H:%M:%S')
    event['summary'] = name
    event['location'] = location
    event['description'] = 'www.facebook.com/events/{}'.format(id)
    event['description'] += '\n\n\n'
    event['description'] += description
    event['start']['dateTime'] = start_str
    event['start']['timeZone'] = 'America/New_York'
    event['end']['dateTime'] = end_str
    event['end']['timeZone'] = 'America/New_York'
    return event

def get_cal_id(service, cal_name):
    cals = service.calendarList().list().execute()
    for cal in cals['items']:
        if cal['summary'] == cal_name:
            cal_id = cal['id']
    return cal_id
    
def clear_calendar(cal_id,service):
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time   
    eventsResult = service.events().list(calendarId=cal_id, timeMin=now, singleEvents=True, orderBy='startTime').execute()
    for event in eventsResult['items']:
        service.events().delete(calendarId=cal_id, eventId=event['id']).execute()

def main():
    credentials = get_credentials()
    logger.info('Got Credentials')
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)
    logger.info('Got Service')
    logger.info('Running RSVP Events')
    rsvp_events(service)
    logger.info('Ran RSVP Events')
    logger.info('Running All Events')
    all_events(service)
    logger.info('Ran All Events')

def rsvp_events(service):    
    #get calendar ID
    cal_id = get_cal_id(service,'Facebook Events')
    logger.info('Got Cal_id: {}'.format(cal_id))
    #first delete all upcoming events
    clear_calendar(cal_id,service)
    logger.info('Cleared Calendar')
    #now add new events - first get list of current SunRay showtimes
    events = facebook.main()
    add_events(events,cal_id,service)

def all_events(service):    
    #get calendar ID
    cal_id = get_cal_id(service,'Facebook All Events')
    logger.info('Got Cal_id: {}'.format(cal_id))
    #first delete all upcoming events
    clear_calendar(cal_id,service)
    logger.info('Cleared Calendar')
    #now add new events - first get list of current SunRay showtimes
    events = allevents.main()
    add_events(events,cal_id,service)

def add_events(events,cal_id,service):
    logger.info('Got events from facebook.py')
    logger.info('Number of events (showtimes) received: {}'.format(len(events)))
    #now loop through and add event
    for event in events:
        logger.info('Processing event ID {}, Date {},'.format(event['id'], event['start_time']))
        id = event['id']
        name = event['name']
        description = event['description']
        rsvp_status = event['rsvp_status']
        start_time = event['start_time']
        end_time = event['end_time']
        location = event['location']
        ev = build_event(id, name, description, rsvp_status, start_time, end_time, location)
        logger.info('Event built')
        service.events().insert(calendarId=cal_id, body=ev).execute()
        logger.info('Event added')

if __name__ == '__main__':
    main()

def lambda_handler(event, context):
    main()
