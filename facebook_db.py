from __future__ import print_function
import logger as l
import os
import facebook
import allevents
import sqlite3



def create_conn():
	conn_file = 'data.db'
	try:
		os.remove(conn_file)
	except OSError:
		pass
	conn = sqlite3.connect(conn_file)
	conn.text_factory = str
	return conn
	
def create_tables(conn):
	cursor = conn.cursor()
	cursor.execute('''create table all_events (id integer
						,name text
						,description text
						,rsvp_status text
						,location text
						,start_time text
						,end_time text)
					''')
	cursor.execute('''create table facebook_events (id integer
						,name text
						,description text
						,rsvp_status text
						,location text
						,start_time text
						,end_time text)
					''')
	conn.commit()
	return conn
	
def load_events(conn):
	cursor = conn.cursor()
	
	#first get facebook events
	events = facebook.main()
	for event in events:
		id = encode_it(event['id'])
		name = encode_it(event['name'])
		description = encode_it(event['description'])
		location = encode_it(event['location'])
		rsvp_status = encode_it(event['rsvp_status'])
		start_time = event['start_time']
		end_time = event['end_time']
		cursor.execute('''insert into facebook_events (id, name, description, rsvp_status, location, start_time, end_time)
							VALUES (?,?,?,?,?,?,?)''',(id, name, description, rsvp_status, location, start_time, end_time))
		conn.commit()
	
	#then get all events
	events = allevents.main()
	for event in events:
		id = encode_it(event['id'])
		name = encode_it(event['name'])
		description = encode_it(event['description'])
		location = encode_it(event['location'])
		start_time = event['start_time']
		end_time = event['end_time']
		cursor.execute('''insert into all_events 	(id, name, description, location, start_time, end_time)
							VALUES (?,?,?,?,?,?)''',(id, name, description, location, start_time, end_time))
		conn.commit()
		
	#update rsvp status on all events
	cursor.execute('''	update all_events
						set rsvp_status = (Select rsvp_status from facebook_events where id = all_events.id and start_time = all_events.start_time)
						where exists (Select rsvp_status from facebook_events where id = all_events.id and start_time = all_events.start_time)
				''')
				
				
	#attending, maybe, declined
	return conn

def encode_it(a):
	return a.encode('utf-8').strip()


def main():
	conn = create_conn()
	conn = create_tables(conn)
	conn = load_events(conn)
	cursor = conn.cursor()
	cursor.execute('Select Count(*) as ct from facebook_events')
	for row in cursor:
		print(str(row[0]))
	cursor.execute('Select Count(*) as ct from all_events')
	for row in cursor:
		print(str(row[0]))


if __name__ == '__main__':
	main()
