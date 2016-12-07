from flask import Flask, render_template, request, session, url_for, redirect, flash
import hashlib
import pymysql.cursors

# Initialize the app from Flask
app = Flask(__name__)
app.secret_key = 'secret_key'

#conn = pymysql.connect(
# 					   host='localhost',
#                       user='root',
#                       password='',
#                       db='findfolks',
#                       charset='utf8mb4',
#                       cursorclass=pymysql.cursors.dictcursor
#                       )

# Configure MySQL
conn = pymysql.connect(
    unix_socket='/Applications/MAMP/tmp/mysql/mysql.sock',
    host='localhost',
    user='root',
    password='root',
    db='findFolks',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)


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


@app.route('/add_interests', methods=['GET', 'POST'])
def add_interests():
    logged_in = False
    if session.get('logged_in') is True:
        logged_in = True
    username = session.get('username')
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
    return render_template('add_interests.html', logged_in=logged_in)


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
    if request.method == "POST":
        interest_categories = []
        interest_keywords = []
        group_name = request.form.get('group_name')
        description = request.form.get('description')
        interest_list = request.form.getlist('select_interests')
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
    return render_template('create_groups.html', interests=interests, logged_in=logged_in)


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
    query = 'SELECT group_id FROM belongs_to WHERE username = %s AND authorized = 1'
    cursor.execute(query, username)
    group_ids = cursor.fetchall()
    conn.commit()
    cursor.close()
    groups = []
    for each_group_id in group_ids:
        group_id = each_group_id['group_id']
        cursor = conn.cursor()
        query = 'SELECT group_name FROM a_group WHERE group_id = %s'
        cursor.execute(query, group_id)
        group_name = cursor.fetchone()
        each_group_name = group_name['group_name']
        groups.append(each_group_name)
        conn.commit()
        cursor.close()
    if request.method == "POST":
        title = request.form.get('title')
        description = request.form.get('description')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        location_name = request.form.get('location_name')
        zipcode = int(request.form.get('zipcode'))
        select_group = request.form.getlist('select_group')
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
    return render_template('create_events.html', groups=groups, logged_in=logged_in)


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
    # query that finds all groups with the same interest of the user
    query = 'SELECT group_name, description FROM a_group g JOIN about a ON g.group_id = a.group_id JOIN interested_in i ON a.category = i.category AND a.keyword = i.keyword JOIN member m ON i.username = m.username WHERE m = %s'
    cursor.execute(query, username)
    groups = cursor.fetchall()
    conn.commit()
    cursor.close()
    return render_template('groups.html', groups=groups, logged_in=logged_in)


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
    query = 'SELECT * FROM member'
    cursor.execute(query)
    members = cursor.fetchall()
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
        event = request.form.getlist('select_event')[0]  # Grab event id
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
    app.run('127.0.0.1', 5000, debug=True)
