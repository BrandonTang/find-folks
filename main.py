from flask import Flask, render_template, request, session, url_for, redirect, flash
import hashlib
import pymysql.cursors

# Initialize the app from Flask
app = Flask(__name__)
app.secret_key = 'secret_key'

# Configure MySQL
conn = pymysql.connect(unix_socket='/Applications/MAMP/tmp/mysql/mysql.sock',
					   host='localhost',
                       user='root',
                       password='root',
                       db='findFolks',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)


@app.route('/')
def index():
	"""
	Return the home page for users not logged in.
	"""
	if session.get('logged_in') is True:
		return redirect(url_for('home'))
	return render_template('index.html')


@app.route('/login')
def login():
	"""
	Return the login page that calls login_auth on submit.
	"""
	return render_template('login.html')


@app.route('/login_auth', methods=['GET', 'POST'])
def login_auth():
	"""
	Authenticates user credentials, creates session for user if valid, else redirects to login with flash message.
	"""
	username = request.form['username']
	password = request.form['password']
	md5password = hashlib.md5(password.encode('utf-8')).hexdigest()
	cursor = conn.cursor()
	query = 'SELECT * FROM member WHERE username = %s and password = %s'
	cursor.execute(query, (username, md5password))
	user = cursor.fetchone()
	cursor.close()
	if user:
		session['username'] = username
		session['logged_in'] = True
		flash('User successfully logged in!', category='success')
		return redirect(url_for('home'))
	else:
		flash('Invalid login or username or password.', category='error')
		return redirect(url_for('login'))


@app.route('/register')
def register():
	"""
	Return the register page that calls register_auth on submit.
	"""
	return render_template('register.html')


@app.route('/register_auth', methods=['GET', 'POST'])
def register_auth():
	"""
	Checks if user already exists, redirects to register page if true, else creates new user.
	"""
	username = request.form['username']
	password = request.form['password']
	md5password = hashlib.md5(password.encode('utf-8')).hexdigest()
	first_name = request.form['first_name']
	last_name = request.form['last_name']
	email = request.form['email']
	zip_code = request.form['zip_code']
	cursor = conn.cursor()
	query = 'SELECT * FROM member WHERE username = %s'
	cursor.execute(query, username)
	user = cursor.fetchone()
	if user:
		flash('User already exists.', category='error')
		return redirect(url_for('register'))
	else:
		ins = 'INSERT INTO member VALUES (%s, %s, %s, %s, %s, %s)'
		cursor.execute(ins, (username, md5password, first_name, last_name, email, zip_code))
		conn.commit()
		cursor.close()
		flash('User successfully registered! You may login now.', category='success')
		return redirect(url_for('login'))


@app.route('/logout')
def logout():
	"""
	Logs out the user and removes information from session, then redirects to index page.
	"""
	session.pop('username')
	session.pop('logged_in')
	flash('User successfully logged out.', category='success')
	return redirect('/')


@app.route('/home')
def home():
	"""
	Return the homepage that shows upcoming events for current day and next three days.
	"""
	username = session['username']
	logged_in = session['logged_in']
	cursor = conn.cursor()
	query = 'SELECT category, keyword FROM interested_in WHERE username = %s'
	cursor.execute(query, username)
	data = cursor.fetchall()
	cursor.close()
	return render_template('home.html', username=username, posts=data, logged_in=logged_in)


@app.route('/create_groups', methods=['GET', 'POST'])
def create_groups():
	"""
	Return the create_groups page that allows users to create groups.
	"""



@app.route('/create_events', methods=['GET', 'POST'])
def create_events():
	"""
	Return the create_event page that allows users to create events.
	"""
	logged_in = False
	if session.get('logged_in') is True:
		logged_in = True
	# username = session.get('username')
	if request.method == "POST":
		title = request.form.get('title')
		description = request.form.get('description')
		start_time = request.form.get('start_time')
		end_time = request.form.get('end_time')
		location_name = request.form.get('location_name')
		zipcode = int(request.form.get('zipcode'))
		cursor = conn.cursor()
		query1 = 'INSERT INTO an_event (title, description, start_time, end_time, location_name, zipcode) VALUES (%s, %s, %s, %s, %s, %s)'
		cursor.execute(query1, (title, description, start_time, end_time, location_name, zipcode))
		conn.commit()
		cursor.close()
		# cursor = conn.cursor()
		# query2 = 'SELECT event_id FROM an_event WHERE title = %s AND description = %s'
		# cursor.execute(query2, (title, description))
		# event_id = cursor.fetchone()
		# query3 = 'SELECT group_id FROM a_group WHERE creator = %s'
		# cursor.execute(query3, username)
		# group_id = cursor.fetchone()
		# query4 = 'INSERT INTO organize (event_id, group_id) VALUES (%s, %s)'
		# cursor.execute(query4, (event_id, group_id))
		# conn.commit()
		# cursor.close()
		flash('Event successfully created!', category='success')
		return redirect(url_for('create_events'))
	return render_template('create_events.html', logged_in=logged_in)


@app.route('/friends', methods=['GET', 'POST'])
def friends():
	"""
	Return the friends page that lists all friends available and allows for adding and removing friends.
	"""
	logged_in = False
	if session.get('logged_in') is True:
		logged_in = True
	cursor = conn.cursor()
	query = 'SELECT * FROM member'
	cursor.execute(query)
	members = cursor.fetchall()
	cursor.close()
	return render_template('friends.html', members=members, logged_in=logged_in)


@app.route('/browse_events', methods=['GET', 'POST'])
def browse_events():
	"""
	Return the browse_events page that allows user to view and sign up for events under their interests.
	"""
	logged_in = False
	if session.get('logged_in') is True:
		logged_in = True
	cursor = conn.cursor()
	query = 'SELECT * FROM an_event'
	cursor.execute(query)
	events = cursor.fetchall()
	cursor.close()
	return render_template('browse_events.html', events=events, logged_in=logged_in)


@app.route('/rate_events', methods=['GET', 'POST'])
def rate_events():
	"""
	Return the rate_events page that allows users to rate past events they have participated in.
	"""
	events = []
	logged_in = False
	if session.get('logged_in') is True:
		logged_in = True
	username = session.get('username')
	cursor = conn.cursor()
	query = 'SELECT event_id FROM sign_up WHERE username = %s'
	cursor.execute(query, username)
	event_ids = cursor.fetchall()
	cursor.close()
	for event_id in event_ids:
		cursor = conn.cursor()
		query = 'SELECT * FROM an_event WHERE eventid = %s'
		cursor.execute(query, event_id)
		event_info = cursor.fetchone()
		cursor.close()
		events.append(event_info)
	if request.method == "POST":
		event = request.form.getlist('select_event')[0] # Grab event id
		rating = request.form.getlist('select_rating')[0]
		cursor = conn.cursor()
		query = 'UPDATE signup WITH rating'
		cursor.execute(query, (username, event, rating))
		conn.commit()
		cursor.close()
	return render_template('rate_events.html', events=events, logged_in=logged_in)


@app.route('/friends_events', methods=['GET', 'POST'])
def friends_events():
	"""
	Return the friends_events page that allows users to view events their friends signed up for.
	"""
	events = []
	logged_in = False
	if session.get('logged_in') is True:
		logged_in = True
	username = session.get('username')
	cursor = conn.cursor()
	query = 'SELECT * FROM friend WHERE friend_to = %s'
	cursor.execute(query, username)
	friends_list = cursor.fetchall()
	cursor.close()
	if request.method == "POST":
		friend = request.form.getlist('select_friend')[0]
		cursor = conn.cursor()
		query = 'SELECT event_id FROM sign_up WHERE username = %s'
		cursor.execute(query, friend)
		event_ids = cursor.fetchall()
		cursor.close()
		for event_id in event_ids:
			cursor = conn.cursor()
			query = 'SELECT * FROM event WHERE event_id = %s'
			cursor.execute(query, event_id)
			event_info = cursor.fetchone()
			events.append(event_info)
			cursor.close()
		return render_template('friends_events.html', events=events, friends=friends_list, logged_in=logged_in)
	return render_template('friends_events.html', friends=friends_list, logged_in=logged_in)


if __name__ == "__main__":
	app.run('127.0.0.1', 5000, debug = True)
