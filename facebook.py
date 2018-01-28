import requests
import json
from dateutil import parser
from datetime import datetime

with open('configs/fbook.json') as data_file:
	data = json.load(data_file)
access_token = data['fb_access_token']

params = {'access_token' : access_token}
URL = 'https://graph.facebook.com/v2.10/me/events/'

break_var = 0
while True:
	events = requests.get(URL, params = params)
#	print(json.dumps(events.json(),indent=4))
	for event in events.json()['data']:
		#print(json.dumps(event,indent=4))
		if 'description' in event:
			description = event['description']
		else:
			description = ''
		rsvp_status = event['rsvp_status']
		start_time = parser.parse(event['start_time'])
		name = event['name']
		id = event['id']
		if 'end_time' in event:
			end_time = parser.parse(event['end_time'])
		else:
			end_time = start_time + datetime.timedelta(hours=1)
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
		print(id)
		print(name)
		print(description)
		print(rsvp_status)
		print(start_time)
		print(end_time)
		
		print(location)
		print('----------------------------------------------------------')
		if start_time < parser.parse(datetime.datetime.utcnow().isoformat() + 'Z'):
			break_var = 1
			break
	if 'next' in events.json()['paging'] and break_var == 0:
		URL = events.json()['paging']['next']
	else:
		break
