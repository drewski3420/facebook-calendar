import os
import requests
import json
from dateutil import parser
import datetime
import time
import logger as l
logger = l.setup_custom_logger(__name__)

dir = os.path.dirname(__file__)
fn = os.path.join(dir, 'configs/fbook.json')
with open(fn) as data_file:
    data = json.load(data_file)
access_token = data['fb_access_token']

params = {'access_token' : access_token
        ,'since' : int(time.time())
        }


def get_events():
    events_list = []
    new_event = {}
    URL = 'https://graph.facebook.com/v2.10/me/events/'
    
    while True:
        logger.info('Getting Next Events Page')
        events = requests.get(URL, params = params)
        for event in events.json()['data']:
            logger.info('Processing Event ID: {}'.format(event['id']))
            #print(json.dumps(event,indent=4))
            if 'description' in event:
                description = event['description']
            else:
                description = ''
            rsvp_status = event['rsvp_status']
            name = event['name']
            if 'place' in event:
                if 'location' in event['place']:
                    if 'street' in event['place']['location']:
                        street = event['place']['location']['street']
                    else:
                        street = ''
                    if 'city' in event['place']['location']:
                        city = event['place']['location']['city']
                    else:
                        city = ''
                    if 'state' in event['place']['location']:
                        state = event['place']['location']['state']
                    else:
                        state = ''
                    if 'name' in event['place']:
                        place_name = event['place']['name']
                    else:
                        place_name = ''
                    location = place_name + ' ' + street + ' ' + city + ', ' + state
                else:
                    location = ''
            else:
                location = ''
            if not 'event_times' in event:
                logger.info('Single Occurrent Event')
                start_time = parser.parse(event['start_time'])
                id = event['id']
                if 'end_time' in event:
                    end_time = parser.parse(event['end_time'])
                else:
                    end_time = start_time + datetime.timedelta(hours=1)
                logger.info('Building Event')
                new_event = build_fbook_event(id, name, description, rsvp_status, start_time, end_time, location)
                logger.info('Built Event')
                events_list.append(new_event)
                logger.info('Appended Event')
            else:
                logger.info('Reoccuring Event')
                for event_time in event['event_times']:
                    logger.info('Event ID {} Time: {}'.format(event_time['id'], event_time['start_time']))
                    start_time = parser.parse(event_time['start_time'])
                    id = event_time['id']
                    if 'end_time' in event_time:
                        end_time = parser.parse(event_time['end_time'])
                    else:
                        end_time = start_time + datetime.timedelta(hours=1)
                    logger.info('Building Event')
                    new_event = build_fbook_event(id, name, description, rsvp_status, start_time, end_time, location)
                    logger.info('Built Event')
                    events_list.append(new_event)
                    logger.info('Appended Event')
        if 'next' in events.json()['paging']:
            logger.info('Moving on to next page')
            URL = events.json()['paging']['next']
        else:
            break
    logger.info('Returning Events list with length {}'.format(len(events_list)))
    return events_list

def build_fbook_event(id, name, description, rsvp_status, start_time, end_time, location):
    the_event = {'id' : id
        ,'name' : name
        ,'description' : description
        ,'rsvp_status' : rsvp_status
        ,'start_time' : start_time#.strftime('%Y-%m-%d %H:%M:%S%z')
        ,'end_time' : end_time#.strftime('%Y-%m-%d %H:%M:%S%z')
        ,'location' : location
    }
    return the_event

def main():
    logger.info('Getting Events')
    events = get_events()
    logger.info('Got Events')
    return events

if __name__ == '__main__':
    main()
