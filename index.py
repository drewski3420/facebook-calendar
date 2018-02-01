from __future__ import print_function
import httplib2
import os
import facebook
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

def get_cal_id(service):
    cals = service.calendarList().list().execute()
    for cal in cals['items']:
        if cal['summary'] == 'Facebook Events':
            cal_id = cal['id']
    return cal_id
	
def clear_calendar(cal_id,service):
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time   
    eventsResult = service.events().list(calendarId=cal_id, timeMin=now, singleEvents=True, orderBy='startTime').execute()
    for event in eventsResult['items']:
		service.events().delete(calendarId=cal_id, eventId=event['id']).execute()

def add_event(service, ev, cal_id):
	service.events().insert(calendarId=cal_id, body=ev).execute()
	
def main():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)
    
    #get calendar ID
    cal_id = get_cal_id(service)

    #first delete all upcoming events
    clear_calendar(cal_id,service)

    #now add new events - first get list of current SunRay showtimes
    events = facebook.main()
    
    #now loop through and add event
    for event in events:
		id = event['id']
		name = event['name']
		description = event['description']
		rsvp_status = event['rsvp_status']
		start_time = event['start_time']
		end_time = event['end_time']
		location = event['location']
		ev = build_event(id, name, description, rsvp_status, start_time, end_time, location)
		add_event(service,ev,cal_id)

if __name__ == '__main__':
    main()

def lambda_handler(event, context):
    main()
