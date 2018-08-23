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

params = {'access_token' : access_token}

def create_tables(conn):
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE events(team_id integer
                    ,team_name TEXT
                    ,team_abbrev TEXT
                    ,team_owner TEXT)
    ''')
    cursor.execute('''create table rosters (team_id integer
                    ,team_name integer
                    ,week integer
                    ,player_id integer
                    ,player_name text
                    ,player_position text
                    ,player_pro_team integer
                    ,actual_score real
                    ,projected_score real
                    ,health_status integer)
    ''')
    cursor.execute('''create table matchups (week integer
                    ,winning_team_id integer
                    ,winning_team_name text
                    ,winning_score real
                    ,losing_team_id integer
                    ,losing_team_name text
                    ,losing_score real)
    ''')
    cursor.execute('''create table awards (award text, winner text, datapoint text, week int, s integer, award_type text)''')
    cursor.execute('''Create table calendar (start_dt text, end_dt text, wk integer)''')
    cursor.execute('''with cte as (Select '2017-09-07' as start_dt, '2017-09-14' as end_dt, 1 as wk
                                    union all
                                    select date(start_dt,'+7 day') as start_dt, date(end_dt,'+7 day') as end_dt, wk + 1 as wk from cte where wk < 20)
                    insert into calendar (start_dt, end_dt, wk) select * from cte where wk < 20
    ''')
    cursor.execute('''create table byes (player_pro_team integer, bye_week integer)''')
    cursor.execute('''insert into byes (bye_week, player_pro_team) values ('5', '1'),
                    ('6', '2'),('9', '3'),('6', '4'),('9', '5'),('6', '6'),('5', '7'),('7', '8'),
                    ('8', '9'),('8', '10'),('11', '11'),('10', '12'),('10', '13'),('8', '14'),('1', '15'),
                    ('9', '16'),('9', '17'),('6', '18'),('8', '19'),('11', '20'),('10', '21'),('8', '22'),
                    ('9', '23'),('9', '24'),('11', '25'),('6', '26'),('1', '27'),('6', '28'),('11', '29'),
                    ('8', '30'),('10', '33'),('7', '34')''')
    conn.commit()
    return conn

def populate_tables(conn, league_id, year, espn_s2, swid):    
    cursor = conn.cursor()
    league = espnff.League(league_id, year, espn_s2, swid)
    for team in league.teams:
        team_id = team.team_id
        name = team.team_name
        abbrev = team.team_abbrev
        owner = team.owner
        cursor.execute('insert into teams (team_id, team_name, team_abbrev, team_owner) values (?,?,?,?)',(team.team_id, team.team_name, team.team_abbrev, team.owner))

def get_events():
    events_list = []
    new_event = {}
    URL = 'https://graph.facebook.com/v2.10/me/likes/'

    while True:
		likes = requests.get(URL, params = params)
		for like in likes.json()['data']:
			id = like['id']
			name = like['name']
			print(name)
			n_URL = 'https://graph.facebook.com/v2.10/{}/events/'.format(id)
			n_params = {'access_token' : access_token
						,'since' : int(time.time())
						}			
			while True:
				try:
					events = requests.get(n_URL, params = n_params)
					for event in events.json()['data']:
						if 'description' in event:
							description = event['description']
						else:
							description = ''
						print(description)
						if 'rsvp_status' in event:
							rsvp_status = event['rsvp_status']
						else:
							rsvp_status = ''
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
							logger.info('Single Occurrence Event')
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
					if 'paging' in events.json():
						if 'next' in events.json()['paging']:
							n_URL = events.json()['paging']['next']
						else:
							break
					else:
						break
				except Exception as e:
					logger.exception('Error in get_dates()',exc_info=True)
					logger.exception(events.json())
		if 'paging' in likes.json():
			if 'next' in likes.json()['paging']:
				URL = likes.json()['paging']['next']
			else:
				break
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
    print json.dumps(events, indent=4)
    return events

if __name__ == '__main__':
    main()
