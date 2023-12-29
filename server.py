
"""
Columbia's COMS W4111.001 Introduction to Databases
Example Webserver
To run locally:
    python3 server.py
Go to http://localhost:8111 in your browser.
A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""
import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from sqlalchemy.exc import SQLAlchemyError
from flask import Flask, flash, request, render_template, g, redirect, Response, url_for, session
import string
import random
import time
import copy
from datetime import datetime

import time

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
app.secret_key = os.urandom(32)

#DATABASEURI = "postgresql://postgres:prahlad@localhost:5432/postgres"
DATABASEURI = "postgresql://pk2743:411@34.75.94.195/proj1part2"

engine = create_engine(DATABASEURI)

@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request.

  The variable g is globally accessible.
  """
  try:
    g.conn = engine.connect()
  except:
    print("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't, the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass

@app.route('/')
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments, e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: https://flask.palletsprojects.com/en/2.0.x/api/?highlight=incoming%20request%20data

  """

  # DEBUG: this is debugging code to see what request looks like
  if session.get('user_id'):
    if session['isDriver']:
      if session['active']:
        return redirect('/driver/rides')
      else:
        return redirect('/driver/profile')
    else:
      return redirect('/get_quote')
  else:
    return render_template("index.html")
    
# LOGIN_AUTHENTICATION
@app.route('/login')
def login():
  if session.get('user_id'):
    if session['isDriver']:
      if session['active']:
        return redirect('/driver/rides')
      else:
        return redirect('/driver/profile')
    else:
      return redirect('/get_quote')
  else:
    return render_template('login.html')

@app.route('/login_validation', methods=['POST'])
def login_validation():
    try:
      user_id = request.form.get('user_id')
      passwd = request.form.get('passwd')
      isDriver = request.form.get('isDriver')
      if isDriver is None:
        cursor = g.conn.execute('SELECT count(*) as count \
          FROM pk2743.passengers p \
            WHERE p.user_id = %s and p.passwd = %s', user_id, passwd)
        cnt = 0
        for result in cursor:
          cnt = result['count']
        if cnt > 0:
          session['user_id'] = user_id
          session['isDriver'] = isDriver
          # move to get quote
          return redirect('/get_quote')
        else:
          flash('Invalid credentials. Please re-enter.', 'error')
          return redirect('/login')
      else:
        cursor = g.conn.execute('SELECT count(*) as count \
          FROM pk2743.drivers p \
            WHERE p.user_id = %s and p.passwd = %s', user_id, passwd)
        cnt = 0
        for result in cursor:
          cnt = result['count']
        if cnt > 0:
          session['user_id'] = user_id
          session['isDriver'] = isDriver
          # move to request viewing page
          # ONLY IF DRIVER DRIVES A VEHICLE
          cursor = g.conn.execute('SELECT *\
            FROM pk2743.drives\
              WHERE active=true AND user_id=%s', session['user_id'])
          session['active'] = False

          for drive in cursor:
            session['active'] = True

          if session['active']:
            return redirect('/driver/rides')
          else:
            return redirect('/driver/profile')
        else:
          flash('Invalid credentials!', 'error')
          return redirect('/login')

    except SQLAlchemyError as e:
      flash("ERROR: " + str(e.__dict__['orig']), "error")
      return redirect('/login')

    except Exception as e:
      return redirect('/login')
    
# PASSENGER_FLOW
@app.route('/signup')
def signup():
    return render_template('signup_passengers.html')

@app.route('/signup', methods=['POST'])
def signup_post():
    # code to validate and add user to database goes here
    try:
      user_id = request.form.get('user_id')
      full_name = request.form.get('full_name')
      passwd = request.form.get('passwd')
      confirm_passwd = request.form.get('confirm_passwd')
      if passwd != confirm_passwd:
          flash('ERROR, invalid input: Password and Confirm Password do not match. Please re-enter.', 'error')
          return redirect(url_for('signup'))
      gender = request.form.get('gender')
      phone = request.form.get('phone')
      wallet = request.form.get('wallet')
      default_car_type = request.form.get('default_car_type')
      default_passenger_count = request.form.get('default_passenger_count')
      default_baggage = request.form.get('default_baggage')
      default_special_needs = request.form.get('default_special_needs')
      home_location = request.form.get('home_location')
      work_location = request.form.get('work_location')

      if default_car_type=='':
        default_car_type = None
      
      if home_location=='':
        home_location = None
      
      if work_location=='':
        work_location = None

      # is the home location entry valid?
      if home_location:
          cursor = g.conn.execute('SELECT * \
          FROM pk2743.locations \
            WHERE pincode = %s', home_location)

          cnt =0
          for l in cursor:
            cnt+=1
          
          if cnt==0:
            flash('Home location does not exist!!')
            return redirect(url_for('signup'))

      # is the work location entry valid?
      if work_location:
          cursor = g.conn.execute('SELECT * \
          FROM pk2743.locations \
            WHERE pincode = %s', work_location)

          cnt =0
          for l in cursor:
            cnt+=1
          
          if cnt==0:
            flash('Work location does not exist!!')
            return redirect(url_for('signup'))

      try:
        g.conn.execute('INSERT INTO pk2743.passengers \
          (user_id, passwd, full_name, gender, phone, wallet, \
            default_car_type, default_passenger_count, default_baggage,\
              default_special_needs, home_location, work_location)\
              VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', user_id, passwd, full_name, gender, phone, wallet, \
                default_car_type, default_passenger_count, default_baggage, default_special_needs, home_location, work_location)
                
      except SQLAlchemyError as e:
        print(e)
        flash("ERROR, invalid input:  " + str(e.__dict__['orig']), 'error')
        return redirect(url_for('signup'))

      else:
        flash('Registration successful! Please login with your credentials.', 'info')
        return redirect(url_for('login'))

    except SQLAlchemyError as e:
        print(e)
        flash("ERROR:  " + str(e.__dict__['orig']), 'error')
        return redirect(url_for('login'))  

    except Exception as e:
      return redirect(url_for('login')) 

@app.route('/passenger/profile')
def profile_passengers():
  try:
    if not session.get('user_id') or session['user_id'] == '' or session['isDriver']:
      return redirect('/login')
    cursor = g.conn.execute("SELECT * from pk2743.passengers where user_id=%s",session['user_id'])
    context = {}
    for passenger in cursor:
      context['full_name'] = passenger['full_name']
      context['user_id'] = session['user_id']
      context['passwd'] = passenger['passwd']
      context['phone'] = passenger['phone']
      context['gender'] = passenger['gender']
      context['wallet'] = passenger['wallet']
      context['default_car_type'] = passenger['default_car_type']
      context['default_passenger_count'] = passenger['default_passenger_count']
      context['default_baggage'] = passenger['default_baggage']
      context['home_location'] = passenger['home_location']
      context['work_location'] = passenger['work_location']

      if context['default_car_type']==None:
        context['default_car_type'] = ''

      if context['home_location']==None:
        context['home_location'] = ''
      
      if context['work_location']==None:
        context['work_location'] = ''
      
      # is the home location entry valid?
      if context['home_location']:
          cursor = g.conn.execute('SELECT * \
          FROM pk2743.locations \
            WHERE pincode = %s', context['home_location'])

          cnt =0
          for l in cursor:
            cnt+=1
          
          if cnt==0:
            flash('Home location does not exist!!')
            return redirect('/passenger/profile')

      # is the work location entry valid?
      if context['work_location']:
          cursor = g.conn.execute('SELECT * \
          FROM pk2743.locations \
            WHERE pincode = %s', context['work_location'])

          cnt =0
          for l in cursor:
            cnt+=1
          
          if cnt==0:
            flash('Work location does not exist!!')
            return redirect('/passenger/profile')

      if passenger['default_special_needs']:
        context['default_special_needs'] = "Yes"
      else:
        context['default_special_needs'] = "No"
    return render_template('profile_passengers.html', **context)

  except SQLAlchemyError as e:
    print(e)
    flash("ERROR, invalid input:  " + str(e.__dict__['orig']), 'error')
    return redirect('/login')
  
  except Exception as e:
      return redirect(url_for('login')) 
  

@app.route('/passenger/profile/update', methods=['POST'])
def update_passenger_profile():
  try:
    if not session.get('user_id') or session['user_id'] == '' or session['isDriver']:
      return redirect('/login')

    full_name = request.form.get('full_name')
    passwd = request.form.get('passwd')
    gender = request.form.get('gender')
    phone = request.form.get('phone')
    wallet = request.form.get('wallet')
    default_car_type = request.form.get('default_car_type')
    default_passenger_count = request.form.get('default_passenger_count')
    default_baggage = request.form.get('default_baggage')
    default_special_needs = request.form.get('default_special_needs')
    home_location = request.form.get('home_location')
    work_location = request.form.get('work_location')

    if default_car_type=='':
      default_car_type=None

    if home_location=='':
      home_location=None
    
    if work_location=='':
      work_location=None
    
    # is the home location entry valid?
      if home_location:
          cursor = g.conn.execute('SELECT * \
          FROM pk2743.locations \
            WHERE pincode = %s', home_location)

          cnt =0
          for l in cursor:
            cnt+=1
          
          if cnt==0:
            flash('Home location does not exist!!')
            return redirect('/passenger/profile')

      # is the work location entry valid?
      if work_location:
          cursor = g.conn.execute('SELECT * \
          FROM pk2743.locations \
            WHERE pincode = %s', work_location)

          cnt =0
          for l in cursor:
            cnt+=1
          
          if cnt==0:
            flash('Work location does not exist!!')
            return redirect('/passenger/profile')

    try:
      g.conn.execute('UPDATE pk2743.passengers \
        SET full_name=%s, passwd=%s, gender=%s, phone=%s, wallet=%s, \
          default_car_type=%s, default_passenger_count=%s, default_baggage=%s, default_special_needs=%s,\
            home_location=%s, work_location=%s\
            WHERE user_id=%s', full_name, passwd, gender, phone, wallet, \
              default_car_type, default_passenger_count, default_baggage, default_special_needs, home_location, work_location, session['user_id'])
              
    except SQLAlchemyError as e:
      print(e)
      flash("ERROR, invalid update: " + str(e.__dict__['orig']), 'error')
    else:
      flash('MESSAGE: Update successful!', 'info')
    return redirect(url_for('profile_passengers'))
    
  except SQLAlchemyError as e:
    print(e)
    flash("ERROR, invalid input:  " + str(e.__dict__['orig']), 'error')
    return redirect('/login')
  
  except Exception as e:
      return redirect(url_for('login'))

@app.route('/get_quote')
def get_quote():
  try:
    if not session.get('user_id') or session['user_id'] == '' or session['isDriver']:
      return redirect('/login')
    
    cursor = g.conn.execute("SELECT r.request_status, r.ride_id \
      FROM pk2743.requests_converts_into r \
        WHERE r.user_id = %s and r.request_status != 'Completed' \
          and r.request_status != 'Failed'", session['user_id'])
    cnt = 0
    for result in cursor:
      request_status = result['request_status']
      ride_id = result['ride_id']
      cnt += 1
    if cnt == 0:
      if not session.get('error') or session['error']=="":
        error = ""
      else:
        error = session['error']
        flash(error, 'error')

      session['error'] = ""
      
      return render_template("passenger_request.html")
      
    elif request_status == 'Requested':
      return render_template("waiting.html")

    elif request_status == 'Approved':
      cursor = g.conn.execute("SELECT d.full_name, d.phone, r.vehicle_id \
        FROM pk2743.rides_travels r, pk2743.drivers d \
          WHERE r.ride_id = %s and r.user_id = d.user_id", ride_id)

      for result in cursor:
        driver_name = result['full_name']
        driver_phone = result['phone']
        car_no = result['vehicle_id']
      
      return render_template("approved.html", driver_phone=driver_phone, driver_name=driver_name, car_no=car_no)
    
    elif request_status == 'Accepted':
      cursor = g.conn.execute("SELECT d.full_name, d.phone, r.vehicle_id \
        FROM pk2743.rides_travels r, pk2743.drivers d \
          WHERE r.ride_id = %s and r.user_id = d.user_id", ride_id)
      
      for result in cursor:
        driver_name = result['full_name']
        driver_phone = result['phone']
        car_no = result['vehicle_id']

      return render_template('picked_up.html', driver_phone=driver_phone, driver_name=driver_name, car_no=car_no)
  
  except SQLAlchemyError as e:
    print(e)
    flash("ERROR, invalid input:  " + str(e.__dict__['orig']), 'error')
    return redirect('/login')
  
  except Exception as e:
      return redirect(url_for('login')) 

@app.route('/refresh', methods=['POST'])
def refresh():
  try:
    if not session.get('user_id') or session['user_id'] == '' or session['isDriver']:
      return redirect('/login')
    print(session['user_id'])
    cursor = g.conn.execute("SELECT r.request_id, r.request_status, r.time_requested \
      FROM pk2743.requests_converts_into r \
        WHERE r.user_id = %s and r.request_status != 'Completed' and r.request_status != 'Failed'", session['user_id'])
    
    cnt = 0
    for result in cursor:
      request_id = result['request_id']
      request_status = result['request_status']
      time_requested = result['time_requested']
      cnt+=1

    if cnt>0:
      duration = datetime.now() - time_requested
      duration_in_s = duration.total_seconds()

      if duration_in_s > 60 and request_status == 'Requested':
        g.conn.execute("UPDATE pk2743.requests_converts_into \
          SET request_status = 'Failed' \
            WHERE request_id = %s AND user_id = %s", request_id, session['user_id'])
    
    return redirect('/get_quote')

  except SQLAlchemyError as e:
    flash("ERROR: " + str(e.__dict__['orig']), "error")
    return redirect('/login')
  
  except Exception as e:
      return redirect(url_for('login')) 

@app.route('/cancel_request', methods=['POST'])
def cancel_request():
  try:
    if not session.get('user_id') or session['user_id'] == '' or session['isDriver']:
      return redirect('/login')
      
    cursor = g.conn.execute("SELECT r.request_id, r.request_status \
      FROM pk2743.requests_converts_into r \
        WHERE r.user_id = %s and r.request_status != 'Completed' and r.request_status != 'Failed'", session['user_id'])
    
    for result in cursor:
      request_id = result['request_id']
      request_status = result['request_status']
    
    if request_status == 'Requested':
      g.conn.execute("UPDATE pk2743.requests_converts_into \
        SET request_status = 'Failed' \
          WHERE request_id = %s AND user_id = %s", request_id, session['user_id'])

    return redirect('/get_quote')

  except SQLAlchemyError as e:
    print(e)
    flash("ERROR, invalid input:  " + str(e.__dict__['orig']), 'error')
    return redirect('/login')
  
  except Exception as e:
      return redirect(url_for('login')) 

@app.route('/get_quote_form', methods=['POST'])
def get_quote_form():
  try:
    if not session.get('user_id') or session['user_id'] == '' or session['isDriver']:
      return redirect('/login')
    session['start_location'] = int(request.form['start_location'])
    session['end_location'] = int(request.form['end_location'])
    session['car_type'] = request.form['car_type']
    session['passenger_count'] = int(request.form['passenger_count'])
    session['baggage'] = int(request.form['baggage'])
    session['special_needs'] = request.form['special_needs']
    
    # wait - had the user checked the use default checkbox?
    if request.form.get('fillDefault') is not None:
      cursor = g.conn.execute("SELECT p.default_car_type, p.default_passenger_count, p.default_baggage, p.default_special_needs\
        FROM pk2743.passengers p\
          WHERE p.user_id=%s", session['user_id'])
    
      for prefs in cursor:
        session['car_type'] = prefs['default_car_type']
        session['passenger_count'] = prefs['default_passenger_count']
        session['baggage'] = prefs['default_baggage']
        session['special_needs'] = prefs['default_special_needs']

    if session['car_type'] == '':
      session['car_type'] = None

    if session['special_needs'] == 'Yes':
      session['special_needs'] = "true"
    else:
      session['special_needs'] = "false"

    cursor = g.conn.execute('SELECT * \
      FROM pk2743.locations \
        WHERE pincode = %s', session['start_location'])

    cnt = 0
    for result in cursor:
      cnt += 1
    
    if (cnt == 0):
      session['error'] = "Pickup pincode doesn't exist!!"
      return redirect('/get_quote')

    cursor = g.conn.execute('SELECT * \
      FROM pk2743.locations \
        WHERE pincode = %s', session['end_location'])
    cnt = 0
    for result in cursor:
      cnt += 1
    
    if (cnt == 0):
      session['error'] = "Destination pincode doesn't exist!!"
      return redirect('/get_quote')

    ## BFS implementation
    cursor = g.conn.execute('SELECT * \
      FROM pk2743.locations')
    adj = {}
    visited = {}

    for result in cursor:
      adj[result['pincode']] = []
      visited[result['pincode']] = 0

    cursor = g.conn.execute('SELECT * \
    FROM pk2743.links')

    for result in cursor:
      adj[result['start_pin']].append(result['end_pin'])
      adj[result['end_pin']].append(result['start_pin'])

    bfs_queue = []

    bfs_queue.append(session['start_location'])
    visited[session['start_location']] = 1
    dist = 0

    while len(bfs_queue) > 0:
      n = len(bfs_queue)
      found = 0
      for i in range(1, n+1):
        pin = bfs_queue.pop(0)
        print(pin)
        if pin == session['end_location']:
          found = 1
          break

        for j in range(len(adj[pin])):
          if visited[adj[pin][j]] == 0:
            bfs_queue.append(adj[pin][j])
            visited[adj[pin][j]] = 1
      
      if found == 1:
        break
      dist += 1

    session['fare'] = (dist+1)*1.5*session['passenger_count']
    estimated_wait_time = random.choice([0, 1, 2, 3, 4, 5])
    return render_template('quote.html', estimated_wait_time=estimated_wait_time, max_fare = session['fare'])

  except SQLAlchemyError as e:
    print(e)
    flash("ERROR, invalid input:  " + str(e.__dict__['orig']), 'error')
    return redirect('/login')
  
  except Exception as e:
      return redirect(url_for('login')) 

@app.route('/place_request_form', methods=['POST'])
def place_request_form():
  try:
    if not session.get('user_id') or session['user_id'] == '' or session['isDriver']:
      return redirect('/login')

    request_status = 'Requested'

    # does the passenger's wallet have sufficient funds tho?
    cursor = g.conn.execute('SELECT wallet\
      FROM pk2743.passengers\
        WHERE user_id=%s', session['user_id'])
    
    for passenger in cursor:
      wallet = passenger['wallet']
    
    if wallet < session['fare']:
      flash('ERROR: Insufficient funds in your wallet to place this request. Please add sufficient funds to continue.')
      return redirect('/get_quote')
    
    # insert the new request
    g.conn.execute('INSERT INTO pk2743.requests_converts_into \
      (user_id, start_location, end_location, car_type, passenger_count, \
        baggage, special_needs, request_status, fare) \
          VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)', \
            session['user_id'], session['start_location'], session['end_location'], session['car_type'], session['passenger_count'], session['baggage'], session['special_needs'], request_status, session['fare'])
    
    session['fare'] = None
    return redirect('/get_quote')

  except SQLAlchemyError as e:
    print(e)
    flash("ERROR, invalid input:  " + str(e.__dict__['orig']), 'error')
    return redirect('/login')
  
  except Exception as e:
      return redirect(url_for('login')) 

@app.route('/accepted', methods=['POST'])
def accepted():
  try:
    if not session.get('user_id') or session['user_id'] == '':
      return redirect('/login')
    
    return redirect('/get_quote')

  except SQLAlchemyError as e:
    print(e)
    flash("ERROR, invalid input:  " + str(e.__dict__['orig']), 'error')
    return redirect('/login')
  
  except Exception as e:
      return redirect(url_for('login')) 

@app.route('/completed', methods=['POST'])
def completed():
  try:
    if not session.get('user_id') or session['user_id'] == '':
      return redirect('/login')
    
    return redirect('/get_quote')

  except SQLAlchemyError as e:
    print(e)
    flash("ERROR, invalid input:  " + str(e.__dict__['orig']), 'error')
    return redirect('/login')
  
  except Exception as e:
      return redirect(url_for('login')) 

@app.route('/feedback', methods=['POST'])
def feedback():
  try:
    if not session.get('user_id') or session['user_id'] == '':
      return redirect('/login')
    
    rating = request.form.get('rating')

    cursor = g.conn.execute("SELECT r.ride_id\
    FROM pk2743.requests_converts_into r \
      WHERE r.user_id = %s and r.request_status != 'Completed' and r.request_status != 'Failed'", session['user_id'])

    for result in cursor:
      ride_id = result['ride_id']
    
    # update the ride's rating from passenger's feedback
    g.conn.execute("UPDATE pk2743.rides_travels \
      SET ride_rating = 0.8*ride_rating + 0.2*%s where ride_id = %s", rating, ride_id)
    
    # get the updated ride rating
    cursor = g.conn.execute("SELECT user_id, ride_rating\
      FROM pk2743.rides_travels\
        WHERE ride_id=%s", ride_id)
    
    for ride in cursor:
      updated_ride_rating = ride['ride_rating']
      driver_id = ride['user_id']

    # update the driver's rating from the updated ride rating
    g.conn.execute("UPDATE pk2743.drivers \
    SET rating = 0.9*rating + 0.1*%s where user_id = %s", updated_ride_rating, driver_id)

    return redirect('/get_quote')
  
  except SQLAlchemyError as e:
    print(e)
    flash("ERROR, invalid input:  " + str(e.__dict__['orig']), 'error')
    return redirect('/login')
  
  except Exception as e:
      return redirect(url_for('login')) 

# DRIVER_FLOW
@app.route('/driver/profile')
def profile_drivers():
  try:
    if not session.get('user_id') or session['user_id'] == '' or not session['isDriver']:
      return redirect('/login')
    cursor = g.conn.execute("SELECT * from pk2743.drivers where user_id=%s",session['user_id'])
    context = {}
    for driver in cursor:
      context['full_name'] = driver['full_name']
      context['user_id'] = session['user_id']
      context['passwd'] = driver['passwd']
      context['phone'] = driver['phone']
      context['gender'] = driver['gender']
      context['wallet'] = driver['wallet']
      context['licence_id'] = driver['licence_id']
      context['rating'] = driver['rating']
      context['licence_expiry'] = driver['licence_expiry']
    
    return render_template('profile_drivers.html', **context)

  except SQLAlchemyError as e:
    print(e)
    flash("ERROR, invalid input:  " + str(e.__dict__['orig']), 'error')
    return redirect('/login')
  
  except Exception as e:
      return redirect(url_for('login')) 

@app.route('/driver/profile/update', methods=['POST'])
def update_driver_profile():
  try:
    if not session.get('user_id') or session['user_id'] == '' or not session['isDriver']:
      return redirect('/login')
    full_name = request.form.get('full_name')
    passwd = request.form.get('passwd')
    gender = request.form.get('gender')
    phone = request.form.get('phone')
    wallet = request.form.get('wallet')
    licence_id = request.form.get('licence_id')
    licence_expiry = request.form.get('licence_expiry')

    try:
      g.conn.execute('UPDATE pk2743.drivers \
        SET full_name=%s, passwd=%s, gender=%s, phone=%s, wallet=%s, \
          licence_id=%s, licence_expiry=%s\
            WHERE user_id=%s', full_name, passwd, gender, phone, wallet, \
              licence_id, licence_expiry, session['user_id'])
              
    except SQLAlchemyError as e:
      print(e)
      flash("ERROR, invalid update: " + str(e.__dict__['orig']), 'error')
    else:
      flash('MESSAGE: Update successful!', 'info')
    return redirect(url_for('profile_drivers'))

  except SQLAlchemyError as e:
    print(e)
    flash("ERROR, invalid input:  " + str(e.__dict__['orig']), 'error')
    return redirect('/login')
  
  except Exception as e:
      return redirect(url_for('login')) 

@app.route('/driver/rides')
def driver_rides():
  try:
    if not session.get('user_id') or session['user_id'] == '' or not session['isDriver']:
      return redirect('/login')
    
    if not session['active']:
      return redirect('/driver/profile')

    # update all expired requests to failed before showing them to the driver
    g.conn.execute("UPDATE pk2743.requests_converts_into\
      SET request_status='Failed'\
      WHERE EXTRACT(EPOCH FROM (now()::timestamp - time_requested)) > 60 and request_status='Requested'")

    cursor = g.conn.execute("SELECT P.full_name, R.start_location, R.end_location, R.passenger_count, R.baggage, R.time_requested, R.fare*0.7 AS fare, R.special_needs\
      FROM pk2743.rides_travels RI, pk2743.requests_converts_into R, pk2743.passengers P \
        WHERE RI.user_id = %s AND RI.ongoing = true AND R.request_status='Accepted' AND RI.ride_id = R.ride_id AND R.user_id = P.user_id",session['user_id'])

    seated_passengers = []
    for request in cursor:
      context = {}
      context['full_name'] = request['full_name']
      context['start_location'] = int(request['start_location'])
      context['end_location'] = int(request['end_location'])
      context['passenger_count'] = int(request['passenger_count'])
      context['baggage'] = int(request['baggage'])
      context['time_requested'] = request['time_requested'].strftime("%a, %d %b %Y %H:%M:%S")
      context['fare'] = float(request['fare'])
      context['special_needs'] = request['special_needs']

      seated_passengers.append(context)

    cursor = g.conn.execute("SELECT P.full_name, R.start_location, R.end_location, R.passenger_count, R.baggage, R.time_requested, R.fare*0.7 AS fare, R.special_needs\
      FROM pk2743.rides_travels RI, pk2743.requests_converts_into R, pk2743.passengers P \
        WHERE RI.user_id = %s AND RI.ongoing = true AND R.request_status='Approved' AND RI.ride_id = R.ride_id AND R.user_id = P.user_id",session['user_id'])

    pickup_passengers = []

    for request in cursor:
      context = {}
      context['full_name'] = request['full_name']
      context['start_location'] = int(request['start_location'])
      context['end_location'] = int(request['end_location'])
      context['passenger_count'] = int(request['passenger_count'])
      context['baggage'] = int(request['baggage'])
      context['time_requested'] = request['time_requested'].strftime("%a, %d %b %Y %H:%M:%S")
      context['fare'] = float(request['fare'])
      context['special_needs'] = request['special_needs']

      pickup_passengers.append(context)

    cursor = g.conn.execute("WITH N_Reqs AS (SELECT R.user_id, R.request_id, R.start_location, R.end_location, R.passenger_count, R.baggage, R.time_requested, R.car_type, R.special_needs, R.fare\
              FROM pk2743.links L, pk2743.is_in I, pk2743.requests_converts_into R \
              WHERE I.user_id = %s AND ((I.pincode=L.start_pin AND R.start_location=L.end_pin) OR (I.pincode=L.end_pin AND R.start_location=L.start_pin) OR (I.pincode=R.start_location))\
              AND R.request_status='Requested')\
                \
              SELECT P.user_id, P.full_name, R.start_location, R.end_location, R.passenger_count, R.baggage, R.time_requested, R.fare*0.7 AS fare, R.special_needs\
              FROM N_Reqs R, pk2743.rides_travels RT, pk2743.cars C, pk2743.passengers P\
              WHERE RT.user_id = %s AND RT.ongoing=true AND RT.vehicle_id=C.vehicle_id AND \
                      ((R.car_type IS NOT NULL AND R.car_type=C.car_type) OR R.car_type IS NULL) \
                      AND R.passenger_count <= RT.seats_available\
                      AND R.baggage <= RT.baggage_available\
                      AND R.user_id = P.user_id\
        UNION\
                \
        SELECT P.user_id, P.full_name, R.start_location, R.end_location, R.passenger_count, R.baggage, R.time_requested, R.fare*0.7 AS fare, R.special_needs\
              FROM N_Reqs R, pk2743.drives D, pk2743.cars C, pk2743.passengers P\
              WHERE %s NOT IN (SELECT RT1.user_id FROM pk2743.rides_travels RT1 WHERE RT1.ongoing=true)\
            AND D.user_id=%s AND D.vehicle_id=C.vehicle_id AND D.active=true AND\
                      ((R.car_type IS NOT NULL AND R.car_type=C.car_type) OR R.car_type IS NULL)\
                      AND R.passenger_count <= C.seats\
                      AND R.baggage <= C.baggage\
                      AND R.user_id = P.user_id", session['user_id'], session['user_id'], session['user_id'], session['user_id'])
      
    avail_passengers = []
    for request in cursor:
      context = {}
      context['user_id'] = request['user_id']
      context['full_name'] = request['full_name']
      context['start_location'] = int(request['start_location'])
      context['end_location'] = int(request['end_location'])
      context['passenger_count'] = int(request['passenger_count'])
      context['baggage'] = int(request['baggage'])
      context['time_requested'] = request['time_requested'].strftime("%a, %d %b %Y %H:%M:%S")
      context['fare'] = float(request['fare'])
      context['special_needs'] = request['special_needs']
      avail_passengers.append(context)

    # get the driver's current location
    cursor = g.conn.execute("SELECT pincode from pk2743.is_in where user_id=%s", session['user_id'])
    current_location = 0
    for location in cursor:
      current_location = int(location['pincode'])
    
    # also get the driver's car details
    cursor = g.conn.execute("SELECT C.seats, C.baggage, C.car_type, C.vehicle_id\
      FROM pk2743.drives D, pk2743.cars C\
        WHERE D.active=true and D.user_id=%s and D.vehicle_id=C.vehicle_id", session['user_id'])

    for car in cursor:
      seats_available = car['seats']
      baggage_available = car['baggage']
      car_type = car['car_type']
      vehicle_id = car['vehicle_id']

    # if the driver has an ongoing ride, get the updated seat and baggage availability
    cursor = g.conn.execute("SELECT *\
      FROM pk2743.rides_travels\
        WHERE ongoing=true and user_id=%s", session['user_id'])

    for ride in cursor:
      seats_available = ride['seats_available']
      baggage_available = ride['baggage_available']

    return render_template('driver_rides.html', current_location=current_location, seats_available=seats_available, \
      baggage_available=baggage_available, car_type=car_type, vehicle_id=vehicle_id,\
      seated_passengers=seated_passengers, pickup_passengers=pickup_passengers, avail_passengers=avail_passengers)
  
  except SQLAlchemyError as e:
    print(e)
    flash("ERROR, invalid input:  " + str(e.__dict__['orig']), 'error')
    return redirect('/login')
  
  except Exception as e:
      return redirect(url_for('login')) 

@app.route('/choose_request', methods=['POST'])
def choose_request():
  try:
    if not session.get('user_id') or session['user_id'] == '' or not session['isDriver']:
      return redirect('/login')
    
    if not session['active']:
      return redirect('/driver/profile')

    chosen_userid = request.form.get('user_id')

    if not chosen_userid:
      flash('No requests available to choose near you. Please try again.', 'error')
      return redirect(url_for("driver_rides"))

    # update all expired requests to failed before showing them to the driver
    g.conn.execute("UPDATE pk2743.requests_converts_into\
      SET request_status='Failed'\
      WHERE EXTRACT(EPOCH FROM (now()::timestamp - time_requested)) > 60 and request_status='Requested'")

    # check if the request is no longer valid
    cursor = g.conn.execute("SELECT request_id, passenger_count, baggage, fare \
      FROM pk2743.requests_converts_into\
        WHERE request_status='Requested' AND user_id=%s", chosen_userid)
    cnt=0
    for request_ in cursor:
      chosen_requestid = request_['request_id']
      passenger_count = request_['passenger_count']
      baggage = request_['baggage']
      fare = float(request_['fare'])
      cnt+=1
    
    if cnt==0:
      flash('This request has been expired or was approved by other drivers. Please choose another available request.', 'error')
      return redirect(url_for("driver_rides"))
    else:
      cursor = g.conn.execute('SELECT ride_id, start_time\
        FROM pk2743.rides_travels \
          WHERE ongoing=true AND user_id=%s', session['user_id'])

      cnt=0
      for ride in cursor:
        existing_rideid = ride['ride_id']
        ride_start_time = ride['start_time']
        cnt+=1
      
      if cnt==0:
        # no existing ride, create new one
        ongoing = True
        revenue = 0.3 * fare
        
        # get the driver's vehicle_id
        cursor = g.conn.execute("SELECT vehicle_id\
          from pk2743.drives \
            where active=true AND user_id=%s", session['user_id'])
        
        for vehicle in cursor:
          vehicle_id = vehicle['vehicle_id']
        
        # get the seat capacity of the car
        cursor = g.conn.execute("SELECT seats, baggage\
          FROM pk2743.cars \
          WHERE vehicle_id=%s", vehicle_id)
        
        for car in cursor:
          seats_available = car['seats']
          baggage_available = car['baggage']
        
        # get the driver's rating for ride's rating
        cursor = g.conn.execute("SELECT rating\
          FROM pk2743.drivers \
          WHERE user_id=%s", session['user_id'])
        
        for driver in cursor:
          rating = driver['rating']
        
        try:
          # create the new ride
          g.conn.execute("INSERT INTO pk2743.rides_travels\
            (ongoing, revenue, user_id, vehicle_id, seats_available, ride_rating, baggage_available)\
              VALUES (%s, %s, %s, %s, %s, %s, %s)", ongoing, revenue, session['user_id'], vehicle_id, seats_available, rating, baggage_available)
        
        except SQLAlchemyError as e:
          flash("ERROR: " + str(e), 'error')
          return redirect(url_for("driver_rides"))
        
        else:
          # get the newly created ride's ride_id
          cursor = g.conn.execute("SELECT ride_id\
            FROM pk2743.rides_travels\
              WHERE ongoing=true AND user_id=%s", session['user_id'])
            
          for ride in cursor:
            ride_id = ride['ride_id']
          
          # update the passenger's wallet: deduct the fare
          g.conn.execute("UPDATE pk2743.passengers\
            SET wallet=wallet-%s\
              WHERE user_id=%s", fare, chosen_userid)

          # update the driver's wallet: add their earnings
          g.conn.execute("UPDATE pk2743.drivers\
            SET wallet=wallet+%s\
              WHERE user_id=%s", 0.7*fare, session['user_id'])
          
          # update the ride's capacity info as new passenger(s) onboarded
          g.conn.execute("UPDATE pk2743.rides_travels\
            SET seats_available=seats_available-%s, baggage_available=baggage_available-%s\
              WHERE ride_id=%s", passenger_count, baggage, ride_id)
          
          # update the request_id with ride_id and make it Approved
          g.conn.execute("UPDATE pk2743.requests_converts_into\
            SET ride_id=%s, request_status='Approved'\
              WHERE request_id=%s and user_id=%s", ride_id, chosen_requestid, chosen_userid)
          
          return redirect(url_for("driver_rides"))
      else:
        # get the existing ride's ride_id

        # but - can the driver accept any requests for this ride?
        duration = datetime.now() - ride_start_time
        duration_in_s = duration.total_seconds()

        if duration_in_s > 14400:
          flash('This request can not be approved as the ride has been going on for more than 4 hours.', 'message')
          return redirect(url_for("driver_rides"))

        # update the passenger's wallet: deduct the fare
        g.conn.execute("UPDATE pk2743.passengers\
          SET wallet=wallet-%s\
            WHERE user_id=%s", fare, chosen_userid)

        # update the driver's wallet: add their earnings
        g.conn.execute("UPDATE pk2743.drivers\
          SET wallet=wallet+%s\
            WHERE user_id=%s", 0.7*fare, session['user_id'])
        
        # update the ride's capacity info as new passenger(s) onboarded
        g.conn.execute("UPDATE pk2743.rides_travels\
          SET seats_available=seats_available-%s, baggage_available=baggage_available-%s, revenue=revenue+0.3*%s\
            WHERE ride_id=%s", passenger_count, baggage, fare, existing_rideid)

        # update the request_id with ride_id and make it Approved
        g.conn.execute("UPDATE pk2743.requests_converts_into\
          SET ride_id=%s, request_status='Approved'\
            WHERE request_id=%s and user_id=%s", existing_rideid, chosen_requestid, chosen_userid)
        
        return redirect(url_for("driver_rides"))

  except SQLAlchemyError as e:
    print(e)
    flash("ERROR, invalid input:  " + str(e.__dict__['orig']), 'error')
    return redirect('/login')
  
  except Exception as e:
      return redirect(url_for('login')) 

@app.route('/move_graph', methods=['POST'])
def move_graph():
  try:
    if not session.get('user_id') or session['user_id'] == '' or not session['isDriver']:
        return redirect('/login')

    if not session['active']:
      return redirect('/driver/profile')

    # where is the driver?
    cursor = g.conn.execute("SELECT pincode from pk2743.is_in where user_id=%s", session['user_id'])
    current_location = 0
    for location in cursor:
      current_location = int(location['pincode'])

    # does this driver have an ongoing ride?
    cursor = g.conn.execute("SELECT *\
      FROM pk2743.rides_travels\
        WHERE user_id=%s AND ongoing=true", session['user_id'])
    
    cnt=0
    for count in cursor:
      cnt+=1
    
    if cnt==0:
      cursor = g.conn.execute("SELECT start_pin, end_pin\
        FROM pk2743.links\
          WHERE start_pin=%s or end_pin=%s", current_location, current_location)
      
      neighbours = []
      # the driver may choose to stay, instead of moving at all
      neighbours.append(current_location)
      for link in cursor:
        start = int(link['start_pin'])
        end = int(link['end_pin'])

        if start==current_location:
          neighbours.append(end)
        else:
          neighbours.append(start)

      next_location = random.choice(neighbours)
      # move the driver into next_location from current_location
      g.conn.execute("UPDATE pk2743.is_in\
      SET pincode=%s\
        WHERE pincode=%s", next_location, current_location)

      print('NO REQUESTS! GOING RANDOMLY')
      return redirect(url_for("driver_rides"))
    else: 
      # first, prioritize picking up passengers
      cursor = g.conn.execute("SELECT R.start_location\
        FROM pk2743.rides_travels RT, pk2743.requests_converts_into R\
          WHERE RT.ride_id = R.ride_id AND RT.user_id = %s AND RT.ongoing=true AND R.request_status='Approved' \
            ORDER BY R.time_requested ASC LIMIT 1", session['user_id'])
      
      cnt=0
      for location in cursor:
        pickup_location = int(location['start_location'])
        cnt+=1
      
      if cnt>0:
        # PICKING UP TRAVEL
        # do BFS to find the next location
        cursor = g.conn.execute('SELECT * \
          FROM pk2743.locations')

        adj = {}
        visited = {}

        for result in cursor:
          adj[result['pincode']] = []
          visited[result['pincode']] = 0

        cursor = g.conn.execute('SELECT * \
        FROM pk2743.links')

        for result in cursor:
          adj[result['start_pin']].append(result['end_pin'])
          adj[result['end_pin']].append(result['start_pin'])

        bfs_queue = []
        before = {}

        bfs_queue.append(current_location)
        visited[current_location] = 1
        before[current_location] = -1
        dist = 0

        while len(bfs_queue) > 0:
          n = len(bfs_queue)
          found = 0
          for i in range(1, n+1):
            pin = bfs_queue.pop(0)
            if pin == pickup_location:
              found = 1
              break

            for j in range(len(adj[pin])):
              if visited[adj[pin][j]] == 0:
                bfs_queue.append(adj[pin][j])
                before[adj[pin][j]] = pin
                visited[adj[pin][j]] = 1
          
          if found == 1:
            break
          dist += 1

        temp_location = pickup_location
        while before[temp_location]!=current_location and before[temp_location]!=-1:
          temp_location = before[temp_location]

        next_location = temp_location

      else:
        # DROPPING OFF TRAVEL
        cursor = g.conn.execute("SELECT R.end_location\
        FROM pk2743.rides_travels RT, pk2743.requests_converts_into R\
          WHERE RT.ride_id = R.ride_id AND RT.user_id = %s AND RT.ongoing=true AND R.request_status='Accepted' \
            ORDER BY R.time_requested ASC LIMIT 1", session['user_id'])
        
        for location in cursor:
          dropoff_location = int(location['end_location'])
        
        # do BFS to find the next location
        cursor = g.conn.execute('SELECT * \
          FROM pk2743.locations')

        adj = {}
        visited = {}

        for result in cursor:
          adj[result['pincode']] = []
          visited[result['pincode']] = 0

        cursor = g.conn.execute('SELECT * \
        FROM pk2743.links')

        for result in cursor:
          adj[result['start_pin']].append(result['end_pin'])
          adj[result['end_pin']].append(result['start_pin'])

        bfs_queue = []
        before = {}

        bfs_queue.append(current_location)
        visited[current_location] = 1
        before[current_location] = -1
        dist = 0

        while len(bfs_queue) > 0:
          n = len(bfs_queue)
          found = 0
          for i in range(1, n+1):
            pin = bfs_queue.pop(0)
            if pin == dropoff_location:
              found = 1
              break

            for j in range(len(adj[pin])):
              if visited[adj[pin][j]] == 0:
                bfs_queue.append(adj[pin][j])
                before[adj[pin][j]] = pin
                visited[adj[pin][j]] = 1
          
          if found == 1:
            break
          dist += 1

        temp_location = dropoff_location
        while before[temp_location]!=current_location and before[temp_location]!=-1:
          temp_location = before[temp_location]

        next_location = temp_location

      # move the driver into next_location from current_location
      g.conn.execute("UPDATE pk2743.is_in\
        SET pincode=%s\
          WHERE pincode=%s", next_location, current_location)

      # On the way, pick up + accept passengers as needed 
      pickup_cursor = g.conn.execute("SELECT R.user_id, R.request_id\
        FROM pk2743.rides_travels RT, pk2743.requests_converts_into R\
          WHERE RT.ride_id = R.ride_id AND RT.user_id = %s AND RT.ongoing=true AND R.request_status='Approved' AND R.start_location=%s", session['user_id'], next_location)
      
      for pickup_request in pickup_cursor:
        pickup_userid = pickup_request['user_id']
        pickup_requestid = pickup_request['request_id']

        g.conn.execute("UPDATE pk2743.requests_converts_into\
          SET request_status='Accepted'\
            WHERE user_id=%s AND request_id=%s", pickup_userid, pickup_requestid)

      # On the way, also drop off + complete passengers as needed 
      dropoff_cursor = g.conn.execute("SELECT R.user_id, R.request_id, R.ride_id\
        FROM pk2743.rides_travels RT, pk2743.requests_converts_into R\
          WHERE RT.ride_id = R.ride_id AND RT.user_id = %s AND RT.ongoing=true AND R.request_status='Accepted' AND R.end_location=%s", session['user_id'], next_location)
      
      for dropoff_request in dropoff_cursor:
        dropoff_userid = dropoff_request['user_id']
        dropoff_rideid = dropoff_request['ride_id']
        dropoff_requestid = dropoff_request['request_id']

        g.conn.execute("UPDATE pk2743.requests_converts_into\
          SET request_status='Completed'\
            WHERE user_id=%s AND request_id=%s", dropoff_userid, dropoff_requestid)
        
        c = g.conn.execute("SELECT passenger_count, baggage\
          FROM pk2743.requests_converts_into\
            WHERE user_id=%s AND request_id=%s", dropoff_userid, dropoff_requestid)

        for prefs in c:
          passenger_count = prefs['passenger_count']
          baggage = prefs['baggage']

        # update the ride's capacity info as passenger(s) dropped off
        g.conn.execute("UPDATE pk2743.rides_travels\
          SET seats_available=seats_available+%s, baggage_available=baggage_available+%s\
            WHERE ride_id=%s", passenger_count, baggage, dropoff_rideid)
      
      # Have you dropped off all passengers?
      cursor = g.conn.execute("SELECT COUNT((R.user_id, R.request_id)) AS incomplete_count\
        FROM pk2743.rides_travels RT, pk2743.requests_converts_into R\
          WHERE RT.ride_id = R.ride_id AND RT.user_id = %s AND RT.ongoing=true AND R.request_status!='Completed'", session['user_id'])
      
      for incomplete in cursor:
        incomplete_count = int(incomplete['incomplete_count'])
      
      if incomplete_count == 0:
        # Done with this ride, complete it
        g.conn.execute("UPDATE pk2743.rides_travels \
        SET ongoing=false where user_id=%s and ongoing=true", session['user_id'])

      return redirect(url_for("driver_rides"))

  except SQLAlchemyError as e:
    print(e)
    flash("ERROR, invalid input:  " + str(e.__dict__['orig']), 'error')
    return redirect('/login')
  
  except Exception as e:
      return redirect(url_for('login')) 

@app.route('/logout')
def logout():
  try:
    if not session.get('user_id') or session['user_id'] == '':
      return redirect('/login')

    session['user_id'] = None
    return redirect(url_for('index'))

  except SQLAlchemyError as e:
    print(e)
    flash("ERROR, invalid input:  " + str(e.__dict__['orig']), 'error')
    return redirect('/login')
  
  except Exception as e:
      return redirect(url_for('login')) 

# MAIN FUNCTION
if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using:

        python3 server.py

    Show the help text using:

        python3 server.py --help

    """

    HOST, PORT = host, port
    print("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

  run()