#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors
import hashlib
from datetime import datetime, timedelta

#Initialize the app from Flask
app = Flask(__name__)

#Configure MySQL
conn = pymysql.connect(host='localhost',
                       user='root',
                       password='',
                       db='project2',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)

#We came together to work on this. So everyone wrote the below code together basically. From now on, since we learned the basics together, we are planning to code individually, such that everyone will focus on one route and the template of that route, and so on.
@app.route('/', methods=['GET', 'POST'])
def hello():
	if 'depCity' in request.args: #just to check if the form with get method is submitted or not
		if request.args.get('action')=='oneWay': #submit buttons have names action with values to handle different buttons on the same page
			depCity=request.args.get('depCity')
			arrCity=request.args.get('arrCity')
			depDate=request.args.get('depDate')
			depDateEnd=datetime.strptime(depDate, "%Y-%m-%d") + timedelta(days=1)
			depDateEnd=depDateEnd.strftime("%Y-%m-%d 23:59:59")
			print(depDateEnd)
			cursor=conn.cursor()
			query= 'SELECT f.airline_name, f.flight_number, f.departure_date_time, f.arrival_date_time, f.base_price, dep.airport_name AS departure_airport, arr.airport_name AS arrival_airport FROM Flight AS f JOIN Airport AS dep ON f.departure_airport_code = dep.airport_code JOIN Airport AS arr ON f.arrival_airport_code = arr.airport_code WHERE dep.city = %s AND arr.city = %s AND f.departure_date_time >= %s AND f.departure_date_time < %s '
			cursor.execute(query, (depCity, arrCity, depDate, depDateEnd))
			result=cursor.fetchall()
			error=None
			if result:
				return render_template('index.html', onewayFlights=result)
			else:
				error='No flights are found'
				return render_template('index.html', error=error)

		elif request.args.get('action')=='return':
			depCity=request.args.get('depCity')
			arrCity=request.args.get('arrCity')
			depDate=request.args.get('depDate')
			depDateEnd=datetime.strptime(depDate, "%Y-%m-%d") + timedelta(days=1)
			depDateEnd=depDateEnd.strftime("%Y-%m-%d 23:59:59")
			retDate=request.args.get('retDate')
			retDateEnd=datetime.strptime(retDate, "%Y-%m-%d") + timedelta(days=1)
			retDateEnd=retDateEnd.strftime("%Y-%m-%d 23:59:59")
			cursor=conn.cursor()
			query='SELECT dep_flights.airline_name AS departure_airline_name, dep_flights.flight_number AS departure_flight_number, dep_flights.departure_date_time AS departure_date_time, dep_flights.arrival_date_time AS arrival_date_time, dep_flights.base_price AS departure_base_price, ret_flights.airline_name AS return_airline_name, ret_flights.flight_number AS return_flight_number, ret_flights.departure_date_time AS return_date_time , ret_flights.arrival_date_time AS return_arrival_date_time, ret_flights.base_price AS return_base_price FROM (SELECT f.* FROM Flight f JOIN Airport a ON f.departure_airport_code = a.airport_code WHERE a.city = %s AND f.departure_date_time >= %s AND f.departure_date_time<%s) AS dep_flights JOIN  (SELECT f.* FROM Flight f JOIN Airport a ON f.arrival_airport_code = a.airport_code WHERE a.city = %s AND f.departure_date_time >= %s AND f.departure_date_time<%s) AS ret_flights ON  dep_flights.arrival_airport_code = ret_flights.departure_airport_code WHERE dep_flights.departure_date_time < ret_flights.departure_date_time'
			cursor.execute(query, (depCity, depDate, depDateEnd, depCity, retDate, retDateEnd))
			result=cursor.fetchall()
			error=None
			if result:
				return render_template('index.html', returnFlights=result)
			else:
				error='No flights are found'
				return render_template('index.html', error=error)


	else:
		return render_template('index.html')

#Define route for login
@app.route('/login', methods=['GET', 'POST']) #only one route is enough to handle login
def login():
	if request.method == 'POST':
		if request.form['action']=='loginCustomer':
			email = request.form['username']
			password = request.form['password']
			hashed_password = hashlib.md5(password.encode()).hexdigest()
			cursor=conn.cursor()
			query = 'SELECT * FROM Customer WHERE email = %s and password_ = %s'
			cursor.execute(query, (email, hashed_password))
			result=cursor.fetchone()
			cursor.close()
			error=None
			if result:
				session['username']=email
				return redirect(url_for('customerProfile'))
			else:
				error = 'Invalid login or username'
				return render_template('login.html', error=error)

		elif request.form['action']=='loginAirlineStaff':
			username = request.form['username']
			password = request.form['password']
			hashed_password = hashlib.md5(password.encode()).hexdigest()
			cursor=conn.cursor()
			query = 'SELECT * FROM AirlineStaff WHERE username = %s and password_ = %s'
			cursor.execute(query, (username, hashed_password))
			result=cursor.fetchone()
			cursor.close()
			error=None
			if result:
				session['username']=username
				return redirect(url_for('airlineStaffProfile'))
			else:
				error = 'Invalid login or username'
				return render_template('login.html', error=error)

	else:
		return render_template('login.html')

#Define route for register
@app.route('/register', methods=['GET', 'POST'])
def register():
	if request.method=='POST':
		if request.form['action']=='registerCustomer':
			email = request.form['username']
			password = request.form['password']
			hashed_password = hashlib.md5(password.encode()).hexdigest()
			cursor=conn.cursor()
			query = 'SELECT * FROM Customer WHERE email = %s'
			cursor.execute(query, (email))
			result=cursor.fetchone()
			error = None
			if result:
				error = "This user already exists"
				return render_template('register.html', error = error)

			else:
				newCustomer='INSERT INTO Customer (email, password_) VALUES (%s, %s)'
				cursor.execute(query, (email, hashed_password))
				conn.commit()
				cursor.close()
				session['username']=email
				return redirect(url_for('customerProfile'))

		elif request.form['action']=='registerAirlineStaff':
			username = request.form['username']
			password = request.form['password']
			hashed_password = hashlib.md5(password.encode()).hexdigest()
			cursor=conn.cursor()
			query = 'SELECT * FROM AirlineStaff WHERE username = %s'
			cursor.execute(query, (username))
			result=cursor.fetchone()
			error = None
			if result:
				error = "This user already exists"
				return render_template('register.html', error = error)

			else:
				newAirlineStaff='INSERT INTO AirlineStaff (username, password_) VALUES (%s, %s)'
				cursor.execute(query, (username,hashed_password))
				conn.commit()
				cursor.close()
				session['username']=username
				return redirect(url_for('airlineStaffProfile'))
	else:
		return render_template('register.html')

@app.route('/myFlights', methods=['GET'])
def myFlights():
    # Ensure the user is logged in
    user = session.get('username')
    if not user:
        return redirect(url_for('login'))

    cursor = conn.cursor()

    # Fetch flights booked by the logged-in user
    query = '''
    SELECT * FROM Booking
    JOIN Flight ON Booking.flight_id = Flight.flight_id
    WHERE Booking.customer_email = %s AND Flight.departure_date_time > NOW()
    '''
    cursor.execute(query, (user,))
    flights = cursor.fetchall()
    cursor.close()

    return render_template('my_flights.html', flights=flights)


##@app.route('/customerProfile', methods=['GET', 'POST'])

##@app.route('/airlineStaffProfile', methods=['GET', 'POST'])

##and many other routes to come




		
app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
	app.run('127.0.0.1', 5000, debug = True)
