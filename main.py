import datetime
import hashlib
import pymysql.cursors
from flask import Flask, render_template, request, session, url_for, redirect, flash

# Initialize the app from Flask
app = Flask(__name__)
app.secret_key = 'secret_key'

# Configure MySQL for Mac
conn = pymysql.connect(
    unix_socket='/Applications/MAMP/tmp/mysql/mysql.sock',
    host='localhost',
    user='root',
    password='root',
    db='findFolks',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)
# Configure MySQL for Windows
# conn = pymysql.connect(
#     host='localhost',
#     user='root',
#     password='',
#     db='findfolks',
#     charset='utf8mb4',
#     cursorclass=pymysql.cursors.DictCursor
# )


@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Return the home page for users.
    """
    logged_in = False
    if session.get('logged_in') is True:
        logged_in = True
    username = session.get('username')
    range_start_date = datetime.date.today()
    range_end_date = range_start_date + datetime.timedelta(days=3)
    range_start_date = str(range_start_date) + " 00:00:00"
    range_end_date = str(range_end_date) + " 00:00:00"
    cursor = conn.cursor()
    query = 'SELECT * FROM an_event WHERE start_time BETWEEN %s AND %s'
    cursor.execute(query, (range_start_date, range_end_date))
    events = cursor.fetchall()
    cursor.close()
    cursor = conn.cursor()
    query = 'SELECT * FROM a_group'
    cursor.execute(query)
    conn.commit()
    groups = cursor.fetchall()
    cursor.close()
    cursor = conn.cursor()
    query = 'SELECT * FROM interest'
    cursor.execute(query)
    interests = cursor.fetchall()
    conn.commit()
    cursor.close()
    if request.method == "POST":
        interest = request.form.get('select_interest')
        interest = interest.split(', ')
        category = interest[0]
        keyword = interest[1]
        cursor = conn.cursor()
        query = 'SELECT * FROM a_group NATURAL JOIN about WHERE category = %s AND keyword = %s'
        cursor.execute(query, (category, keyword))
        groups = cursor.fetchall()
        conn.commit()
        cursor.close()
        return render_template('index.html', events=events, groups=groups, interests=interests, logged_in=logged_in,
                               username=username)
    return render_template('index.html', events=events, groups=groups, interests=interests, logged_in=logged_in,
                           username=username)


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
        return redirect(url_for('index'))
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


@app.route('/filter_events', methods=['GET', 'POST'])
def filter_events():
    """
    Return the view my events page that shows upcoming events for current day and next three days and also allows filtering.
    """
    logged_in = False
    if session.get('logged_in') is True:
        logged_in = True
    username = session.get('username')
    cursor = conn.cursor()
    query = 'SELECT * FROM a_group'
    cursor.execute(query)
    groups = cursor.fetchall()
    conn.commit()
    cursor.close()
    range_start_date = datetime.date.today()
    range_end_date = range_start_date + datetime.timedelta(days=3)
    range_start_date = str(range_start_date) + " 00:00:00"
    range_end_date = str(range_end_date) + " 00:00:00"
    cursor = conn.cursor()
    query = 'SELECT * FROM (an_event NATURAL JOIN sign_up NATURAL JOIN organize) JOIN a_group USING (group_id) WHERE username = %s AND start_time BETWEEN %s AND %s'
    cursor.execute(query, (username, range_start_date, range_end_date))
    events = cursor.fetchall()
    conn.commit()
    cursor.close()
    if request.method == "POST":
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        group_name = request.form.getlist('select_group')[0]
        cursor = conn.cursor()
        query = 'SELECT * FROM (an_event NATURAL JOIN sign_up NATURAL JOIN organize) JOIN a_group USING (group_id) WHERE username = %s AND group_name = %s AND start_time BETWEEN %s AND %s'
        cursor.execute(query, (username, group_name, start_time, end_time))
        events = cursor.fetchall()
        conn.commit()
        cursor.close()
        return render_template('filter_events.html', username=username, events=events, groups=groups,
                               logged_in=logged_in)
    return render_template('filter_events.html', username=username, events=events, groups=groups, logged_in=logged_in)


@app.route('/add_interests', methods=['GET', 'POST'])
def add_interests():
    """
    Return the add interests page that allows users to add their interests.
    """
    logged_in = False
    if session.get('logged_in') is True:
        logged_in = True
    username = session.get('username')
    cursor = conn.cursor()
    query = 'SELECT * FROM interested_in WHERE username = %s'
    cursor.execute(query, username)
    interests = cursor.fetchall()
    conn.commit()
    cursor.close()
    if request.method == "POST":
        category = request.form.get('category')
        keyword = request.form.get('keyword')
        cursor = conn.cursor()
        query = 'SELECT category, keyword FROM interest WHERE category = %s AND keyword = %s'
        cursor.execute(query, (category, keyword))
        existing_interest = cursor.fetchall()
        conn.commit()
        cursor.close()
        if len(existing_interest) == 0:
            cursor = conn.cursor()
            query = 'INSERT INTO interest (category, keyword) VALUES (%s, %s)'
            cursor.execute(query, (category, keyword))
            conn.commit()
            cursor.close()
            flash("Brand new interest added to FindFolks!")
        cursor = conn.cursor()
        query = 'SELECT username, category, keyword FROM interested_in WHERE username = %s AND category = %s AND keyword = %s'
        cursor.execute(query, (username, category, keyword))
        duplicate_interest = cursor.fetchall()
        conn.commit()
        cursor.close()
        if len(duplicate_interest) == 0:
            cursor = conn.cursor()
            query = 'INSERT INTO interested_in (username, category, keyword) VALUES (%s, %s, %s)'
            cursor.execute(query, (username, category, keyword))
            conn.commit()
            cursor.close()
            flash("New interest for member has been added!")
        return redirect(url_for('add_interests'))
    return render_template('add_interests.html', interests=interests, logged_in=logged_in)


@app.route('/create_groups', methods=['GET', 'POST'])
def create_groups():
    """
    Return the create_groups page that allows users to create groups.
    """
    logged_in = False
    if session.get('logged_in') is True:
        logged_in = True
    username = session.get('username')
    cursor = conn.cursor()
    query = 'SELECT * FROM interest'
    cursor.execute(query)
    interests = cursor.fetchall()
    conn.commit()
    cursor.close()
    cursor = conn.cursor()
    query = 'SELECT * FROM location'
    cursor.execute(query)
    locations = cursor.fetchall()
    conn.commit()
    cursor.close()
    if request.method == "POST":
        interest_categories = []
        interest_keywords = []
        group_name = request.form.get('group_name')
        description = request.form.get('description')
        interest_list = request.form.getlist('select_interests')
        location = request.form.getlist('location')[0]
        location = location.split(', ')
        location_name = location[0]
        zipcode = location[1]
        for each_interest in interest_list:
            interest = each_interest.split(', ')
            interest_categories.append(interest[0])
            interest_keywords.append(interest[1])
        cursor = conn.cursor()
        query = 'INSERT INTO a_group (group_name, description, creator) VALUES (%s, %s, %s)'
        cursor.execute(query, (group_name, description, username))
        conn.commit()
        cursor.close()
        flash("Group has been created!")
        cursor = conn.cursor()
        query = 'SELECT group_id FROM a_group WHERE group_name = %s AND description = %s'
        cursor.execute(query, (group_name, description))
        group_id = cursor.fetchone()
        created_group_id = group_id['group_id']
        conn.commit()
        cursor.close()
        cursor = conn.cursor()
        query = 'INSERT INTO meets_at (group_id, location_name, zipcode) VALUES (%s, %s, %s)'
        cursor.execute(query, (created_group_id, location_name, zipcode))
        conn.commit()
        cursor.close()
        flash("Group location has been updated!")
        for category, keyword in zip(interest_categories, interest_keywords):
            cursor = conn.cursor()
            query = 'INSERT INTO about (category, keyword, group_id) VALUES (%s, %s, %s)'
            cursor.execute(query, (category, keyword, created_group_id))
            conn.commit()
            cursor.close()
        flash("Group interests have been added!")
        cursor = conn.cursor()
        query = 'INSERT INTO belongs_to (group_id, username, authorized) VALUES (%s, %s, 1)'
        cursor.execute(query, (created_group_id, username))
        conn.commit()
        cursor.close()
        flash("You have been added as an authorized user to the group!")
        return redirect(url_for('create_groups'))
    return render_template('create_groups.html', locations=locations, interests=interests, logged_in=logged_in)


@app.route('/create_events', methods=['GET', 'POST'])
def create_events():
    """
    Return the create_event page that allows users to create events.
    """
    logged_in = False
    if session.get('logged_in') is True:
        logged_in = True
    username = session.get('username')
    cursor = conn.cursor()
    query = 'SELECT * FROM belongs_to JOIN a_group USING (group_id) WHERE username = %s AND authorized = 1'
    cursor.execute(query, username)
    groups = cursor.fetchall()
    conn.commit()
    cursor.close()
    cursor = conn.cursor()
    query = 'SELECT * FROM location'
    cursor.execute(query)
    locations = cursor.fetchall()
    conn.commit()
    cursor.close()
    if request.method == "POST":
        title = request.form.get('title')
        description = request.form.get('description')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        location = request.form.getlist('location')[0]
        location = location.split(', ')
        location_name = location[0]
        zipcode = location[1]
        select_group = request.form.getlist('select_group')[0]
        cursor = conn.cursor()
        query1 = 'INSERT INTO an_event (title, description, start_time, end_time, location_name, zipcode) VALUES (%s, %s, %s, %s, %s, %s)'
        cursor.execute(query1, (title, description, start_time, end_time, location_name, zipcode))
        conn.commit()
        cursor.close()
        cursor = conn.cursor()
        query2 = 'SELECT event_id FROM an_event WHERE title = %s AND description = %s'
        cursor.execute(query2, (title, description))
        event_id = cursor.fetchone()
        created_event_id = event_id['event_id']
        query3 = 'SELECT group_id FROM a_group WHERE group_name = %s'
        cursor.execute(query3, select_group)
        group_id = cursor.fetchone()
        selected_group_id = group_id['group_id']
        query4 = 'INSERT INTO organize (event_id, group_id) VALUES (%s, %s)'
        cursor.execute(query4, (created_event_id, selected_group_id))
        conn.commit()
        cursor.close()
        flash('Event successfully created!', category='success')
        return redirect(url_for('create_events'))
    return render_template('create_events.html', groups=groups, locations=locations, logged_in=logged_in)


@app.route('/groups', methods=['GET', 'POST'])
def groups():
    """
    Return the groups page that lists groups that a member has the ability to join.
    """
    logged_in = False
    if session.get('logged_in') is True:
        logged_in = True
    username = session.get('username')
    cursor = conn.cursor()
    query = 'SELECT * FROM belongs_to JOIN (a_group NATURAL JOIN meets_at) USING (group_id) WHERE username != %s AND group_id NOT IN (SELECT group_id FROM belongs_to JOIN a_group USING (group_id) WHERE username = %s)'
    cursor.execute(query, (username, username))
    groups = cursor.fetchall()
    conn.commit()
    cursor.close()
    cursor = conn.cursor()
    query = 'SELECT * FROM belongs_to JOIN (a_group NATURAL JOIN meets_at) USING (group_id) WHERE username = %s'
    cursor.execute(query, username)
    your_groups = cursor.fetchall()
    conn.commit()
    cursor.close()
    if request.method == "POST":
        group_id = request.form.get('select_group')
        cursor = conn.cursor()
        query = 'INSERT INTO belongs_to (group_id, username) VALUES (%s, %s)'
        cursor.execute(query, (group_id, username))
        conn.commit()
        cursor.close()
        flash("Successfully joined group!")
        return redirect(url_for('groups'))
    return render_template('groups.html', groups=groups, your_groups=your_groups, logged_in=logged_in)


@app.route('/friends', methods=['GET', 'POST'])
def friends():
    """
    Return the friends page that lists all friends available and allows for adding and removing friends.
    """
    logged_in = False
    if session.get('logged_in') is True:
        logged_in = True
    username = session.get('username')
    cursor = conn.cursor()
    query = 'SELECT * FROM member WHERE username NOT IN (SELECT friend_to FROM friend WHERE friend_of = %s)'
    cursor.execute(query, username)
    members = cursor.fetchall()
    conn.commit()
    cursor.close()
    cursor = conn.cursor()
    query = 'SELECT friend_to FROM friend WHERE friend_of = %s'
    cursor.execute(query, username)
    friends = cursor.fetchall()
    conn.commit()
    cursor.close()
    if request.method == "POST":
        friend = request.form.get('select_member')
        cursor = conn.cursor()
        query = 'INSERT INTO friend (friend_of, friend_to) VALUES (%s, %s)'
        cursor.execute(query, (username, friend))
        conn.commit()
        cursor.close()
        flash("Successfully added friend!")
        return redirect(url_for('friends'))
    return render_template('friends.html', members=members, friends=friends, logged_in=logged_in)


@app.route('/browse_events', methods=['GET', 'POST'])
def browse_events():
    """
    Return the browse_events page that allows user to view and sign up for events under their interests.
    """
    logged_in = False
    if session.get('logged_in') is True:
        logged_in = True
    username = session.get('username')
    range_start_date = datetime.date.today()
    range_start_date = str(range_start_date) + " 00:00:00"
    cursor = conn.cursor()
    query = 'SELECT * FROM an_event WHERE start_time <= %s AND end_time >= %s AND event_id NOT IN (SELECT event_id FROM sign_up WHERE username = %s)'
    cursor.execute(query, (range_start_date, range_start_date, username))
    events = cursor.fetchall()
    cursor.close()
    if request.method == "POST":
        event_id = request.form.get('select_event')
        cursor = conn.cursor()
        query = 'INSERT INTO sign_up (event_id, username) VALUES (%s, %s)'
        cursor.execute(query, (event_id, username))
        conn.commit()
        cursor.close()
        flash("Successfully signed up for event!")
        return redirect(url_for('browse_events'))
    return render_template('browse_events.html', events=events, logged_in=logged_in)


@app.route('/rate_events', methods=['GET', 'POST'])
def rate_events():
    """
    Return the rate_events page that allows users to rate past events they have participated in.
    """
    logged_in = False
    if session.get('logged_in') is True:
        logged_in = True
    username = session.get('username')
    range_start_date = datetime.date.today()
    range_start_date = str(range_start_date) + " 00:00:00"
    cursor = conn.cursor()
    query = 'SELECT * FROM sign_up JOIN an_event USING (event_id) WHERE username = %s AND end_time < %s'
    cursor.execute(query, (username, range_start_date))
    events = cursor.fetchall()
    conn.commit()
    cursor.close()
    cursor = conn.cursor()
    query = 'SELECT title, avg(rating) rating FROM sign_up JOIN an_event USING (event_id) WHERE rating != 0 GROUP BY title'
    cursor.execute(query)
    ratings = cursor.fetchall()
    conn.commit()
    cursor.close()
    if request.method == "POST":
        event_id = request.form.getlist('select_event')[0]
        rating = request.form.getlist('select_rating')[0]
        cursor = conn.cursor()
        query = 'UPDATE sign_up SET rating = %s WHERE event_id = %s AND username = %s'
        cursor.execute(query, (rating, event_id, username))
        conn.commit()
        cursor.close()
        flash("Successfully rated event!")
        return redirect(url_for('rate_events'))
    return render_template('rate_events.html', ratings=ratings, events=events, logged_in=logged_in)


@app.route('/friends_events', methods=['GET', 'POST'])
def friends_events():
    """
    Return the friends_events page that allows users to view events their friends signed up for.
    """
    logged_in = False
    if session.get('logged_in') is True:
        logged_in = True
    username = session.get('username')
    cursor = conn.cursor()
    query = 'SELECT * FROM friend WHERE friend_of = %s'
    cursor.execute(query, username)
    friends_list = cursor.fetchall()
    cursor.close()
    if request.method == "POST":
        friend = request.form.getlist('select_friend')[0]
        cursor = conn.cursor()
        query = 'SELECT * FROM sign_up JOIN an_event USING (event_id) WHERE username = %s'
        cursor.execute(query, friend)
        events = cursor.fetchall()
        cursor.close()
        return render_template('friends_events.html', events=events, friends=friends_list, logged_in=logged_in)
    return render_template('friends_events.html', friends=friends_list, logged_in=logged_in)


if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug=True)
