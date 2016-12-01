#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect
import hashlib
import pymysql.cursors

#Initialize the app from Flask
app = Flask(__name__)

# Configure MySQL
conn = pymysql.connect(unix_socket='/Applications/MAMP/tmp/mysql/mysql.sock',
					   host='localhost',
                       user='root',
                       password='root',
                       db='meetup3',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)

#Define a route to hello function
@app.route('/')
def hello():
	if session.get('logged_in') is True:
		return redirect(url_for('home'))
	return render_template('index.html')


#Define route for login
@app.route('/login')
def login():
	return render_template('login.html')


#Define route for register
@app.route('/register')
def register():
	return render_template('register.html')


#Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
	#grabs information from the forms
	username = request.form['username']
	password = request.form['password']
	md5password = hashlib.md5(password).hexdigest()
	#cursor used to send queries
	cursor = conn.cursor()
	#executes query
	query = 'SELECT * FROM user WHERE username = %s and password = %s'
	cursor.execute(query, (username, md5password))
	#stores the results in a variable
	data = cursor.fetchone()
	#use fetchall() if you are expecting more than 1 data row
	cursor.close()
	if data:
		#creates a session for the the user
		#session is a built in
		session['username'] = username
		session['logged_in'] = True
		return redirect(url_for('home'))
	else:
		#returns an error message to the html page
		error = 'Invalid login or username'
		return render_template('login.html', error=error)


#Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
	#grabs information from the forms
	username = request.form['username']
	password = request.form['password']
	md5password = hashlib.md5(password).hexdigest()
	#cursor used to send queries
	cursor = conn.cursor()
	#executes query
	query = 'SELECT * FROM user WHERE username = %s'
	cursor.execute(query, username)
	#stores the results in a variable
	data = cursor.fetchone()
	#use fetchall() if you are expecting more than 1 data row
	error = None
	if data:
		#If the previous query returns data, then user exists
		error = "This user already exists."
		return render_template('register.html', error=error)
	else:
		ins = 'INSERT INTO user VALUES(%s, %s)'
		cursor.execute(ins, (username, md5password))
		conn.commit()
		cursor.close()
		return render_template('index.html')


@app.route('/home')
def home():
	username = session['username']
	logged_in = session['logged_in']
	cursor = conn.cursor()
	query = 'SELECT ts, blog_post FROM blog WHERE username = %s ORDER BY ts DESC'
	cursor.execute(query, username)
	data = cursor.fetchall()
	cursor.close()
	return render_template('home.html', username=username, posts=data, logged_in=logged_in)


@app.route('/tweets', methods=['GET', 'POST'])
def tweets():
	logged_in = False
	if session.get('logged_in') is True:
		logged_in = True
	cursor = conn.cursor()
	query = 'SELECT username FROM user'
	cursor.execute(query)
	all_users = cursor.fetchall()
	cursor.close()
	if request.method == 'POST':
		select_user = request.form.getlist('select_user')[0]
		cursor = conn.cursor()
		query = 'SELECT ts, blog_post FROM blog WHERE username = %s ORDER BY ts DESC'
		cursor.execute(query, select_user)
		user_tweets = cursor.fetchall()
		cursor.close()
		return render_template('tweets.html', posts=user_tweets, all_users=all_users, logged_in=logged_in)
	return render_template('tweets.html', all_users = all_users, logged_in=logged_in)

		
@app.route('/post', methods=['GET', 'POST'])
def post():
	username = session['username']
	cursor = conn.cursor()
	blog = request.form['blog']
	query = 'INSERT INTO blog (blog_post, username) VALUES(%s, %s)'
	cursor.execute(query, (blog, username))
	conn.commit()
	cursor.close()
	return redirect(url_for('home'))


@app.route('/logout')
def logout():
	session.pop('username')
	session.pop('logged_in')
	return redirect('/')


app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
	app.run('127.0.0.1', 5000, debug = True)
