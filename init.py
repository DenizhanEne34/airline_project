#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors
import hashlib
from datetime import datetime, timedelta

#Initialize the app from Flask
app = Flask(__name__)

#Configure MySQL
conn = pymysql.connect(host='localhost',
					   port = 8889,
                       user='deniz',
                       password='1289',
                       db='project',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)


@app.route('/', methods=['GET', 'POST'])
def index():
	if 'depCity' in request.args: #just to check if the form with get method is submitted or not
		if request.args.get('action')=='oneWay': #submit buttons have names action with values to handle different buttons on the same page
			depCity=request.args.get('depCity')
			arrCity=request.args.get('arrCity')
			depDate=request.args.get('depDate')
			depDateEnd=datetime.strptime(depDate, "%Y-%m-%d") + timedelta(days=1)
			depDateEnd=depDateEnd.strftime("%Y-%m-%d 23:59:59")
			cursor=conn.cursor()
			query1= '''
			SELECT 
			    f.airline_name, 
			    f.flight_number, 
			    f.departure_date_time, 
			    f.arrival_date_time, 
			    f.base_price, 
			    CASE 
			        WHEN COUNT(t.ticket_id) >= 0.8 * a.number_of_seats THEN f.base_price * 1.25
			        ELSE f.base_price
			    END AS calculated_price,
			    dep.airport_name AS departure_airport, 
			    arr.airport_name AS arrival_airport 
			FROM 
			    Flight AS f
			JOIN 
			    Airport AS dep ON f.departure_airport_code = dep.airport_code
			JOIN 
			    Airport AS arr ON f.arrival_airport_code = arr.airport_code
			JOIN 
			    Airplane AS a ON f.airplane_id = a.airplane_id
			LEFT JOIN 
			    Ticket AS t ON f.flight_number = t.flight_number AND f.airline_name = t.airline_name AND f.departure_date_time=t.departure_date_time
			WHERE 
			    dep.city = %s AND arr.city = %s AND f.departure_date_time >= %s AND f.departure_date_time < %s
			GROUP BY 
			    f.flight_number, f.airline_name, f.departure_date_time, f.arrival_date_time, f.base_price, a.number_of_seats, dep.airport_name, arr.airport_name


						'''
			
			cursor.execute(query1, (depCity, arrCity, depDate, depDateEnd))
			result=cursor.fetchall()
			cursor.close()
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
			query1= '''
			SELECT 
			    dep_flights.airline_name AS departure_airline_name, 
			    dep_flights.flight_number AS departure_flight_number, 
			    dep_flights.departure_date_time AS departure_date_time, 
			    dep_flights.arrival_date_time AS arrival_date_time, 
			    CASE 
			        WHEN dep_flights.ticket_count >= 0.8 * dep_flights.number_of_seats THEN dep_flights.base_price * 1.25
			        ELSE dep_flights.base_price
			    END AS departure_calculated_price,
			    ret_flights.airline_name AS return_airline_name, 
			    ret_flights.flight_number AS return_flight_number, 
			    ret_flights.departure_date_time AS return_date_time,
			    ret_flights.arrival_date_time AS return_arrival_date_time,
			    CASE 
			        WHEN ret_flights.ticket_count >= 0.8 * ret_flights.number_of_seats THEN ret_flights.base_price * 1.25
			        ELSE ret_flights.base_price
			    END AS return_calculated_price
			FROM 
			    (SELECT f.*, a.number_of_seats, COUNT(t.ticket_id) as ticket_count FROM Flight f
			     JOIN Airport dep ON f.departure_airport_code = dep.airport_code
			     JOIN Airplane a ON f.airplane_id = a.airplane_id
			     LEFT JOIN Ticket t ON f.flight_number = t.flight_number AND f.airline_name = t.airline_name AND f.departure_date_time=t.departure_date_time
			     WHERE dep.city = %s AND f.departure_date_time >= %s AND f.departure_date_time < %s
			     GROUP BY f.flight_number, f.airline_name, a.number_of_seats, f.base_price, f.departure_date_time, f.arrival_date_time, dep.airport_code) AS dep_flights
			JOIN 
			    (SELECT f.*, a.number_of_seats, COUNT(t.ticket_id) as ticket_count FROM Flight f
			     JOIN Airport arr ON f.arrival_airport_code = arr.airport_code
			     JOIN Airplane a ON f.airplane_id = a.airplane_id
			     LEFT JOIN Ticket t ON f.flight_number = t.flight_number AND f.airline_name = t.airline_name AND f.departure_date_time=t.departure_date_time
			     WHERE arr.city = %s AND f.departure_date_time >= %s AND f.departure_date_time < %s
			     GROUP BY f.flight_number, f.airline_name, a.number_of_seats, f.base_price, f.departure_date_time, f.arrival_date_time, arr.airport_code) AS ret_flights
			ON 
			    dep_flights.arrival_airport_code = ret_flights.departure_airport_code
			WHERE 
			    dep_flights.departure_date_time < ret_flights.departure_date_time


						'''

			cursor.execute(query1, (depCity, depDate, depDateEnd, depCity, retDate, retDateEnd))
			result=cursor.fetchall()
			cursor.close()
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
@app.route('/registerCustomer', methods=['GET', 'POST'])
def registerCustomer():
	if request.method=='POST':
		email = request.form['email']
		password = request.form['password']
		hashed_password = hashlib.md5(password.encode()).hexdigest()
		first_name=request.form['first_name']
		last_name= request.form['last_name']
		building_no= request.form['building_no']
		street_name=request.form['street_name']
		apt_number=request.form['apt_number']
		city=request.form['city']
		state_= request.form['state_']
		zip_code=request.form['zip_code']
		passport_number=request.form['passport_number']
		passport_expiration=request.form['passport_expiration']
		passport_country=request.form['passport_country']
		date_of_birth=request.form['date_of_birth']
		phone_numbers=request.form['phone_numbers']
		phone_numbers_list=phone_numbers.split(',')
		cursor=conn.cursor()
		query = 'SELECT * FROM Customer WHERE email = %s'
		cursor.execute(query, (email))
		result=cursor.fetchone()
		error = None
		if result:
			error = "This user already exists"
			return render_template('registerCustomer.html', error = error)

		else:
			newCustomer='INSERT INTO Customer (email, password_, first_name,last_name,building_no,street_name,apt_number,city,state_,zip_code,passport_number,passport_expiration,passport_country,date_of_birth ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,%s,%s,%s,%s,%s)'
			cursor.execute(newCustomer, (email, hashed_password, first_name,last_name,building_no,street_name,apt_number,city,state_,zip_code,passport_number,passport_expiration,passport_country,date_of_birth))
			conn.commit()
			session['username']=email
			for number in phone_numbers_list:
				newPhoneNumbers= 'INSERT INTO Cust_PNumber (email, phone_number) VALUES (%s, %s)'
				cursor.execute(newPhoneNumbers, (email,number))
			conn.commit()
			cursor.close()
			return redirect(url_for('customerProfile'))
	
	else:
		return render_template('registerCustomer.html')

@app.route('/registerAirlineStaff', methods=['GET', 'POST'])
def registerAirlineStaff():
	if request.method=='POST':
		username = request.form['username']
		password = request.form['password']
		first_name=request.form['first_name']
		last_name=request.form['last_name']
		date_of_birth=request.form['date_of_birth']
		airline_name=request.form['airline_name']
		emails=request.form['emails']
		phone_numbers=request.form['phone_numbers']
		emails_list=emails.split(',')
		phone_numbers_list=phone_numbers.split(',')
		hashed_password = hashlib.md5(password.encode()).hexdigest()
		cursor=conn.cursor()
		query = 'SELECT * FROM AirlineStaff WHERE username = %s'
		cursor.execute(query, (username))
		result=cursor.fetchone()
		error =None
		error1=None
		if result:
			error = "This user already exists"
			return render_template('registerAirlineStaff.html', error = error)

		else:
			query1='SELECT * FROM Airline WHERE airline_name = %s'
			cursor.execute(query1, (airline_name))
			result1=cursor.fetchone()
			if result1:
				newAirlineStaff='INSERT INTO AirlineStaff (username, password_, first_name,last_name,date_of_birth,airline_name) VALUES (%s, %s, %s,%s,%s,%s)'
				cursor.execute(newAirlineStaff, (username,hashed_password, first_name, last_name, date_of_birth, airline_name))
				conn.commit()
				for email in emails_list:
					newEmails= 'INSERT INTO AirStaff_Email (username, email) VALUES (%s, %s)'
					cursor.execute(newEmails, (username, email))
				conn.commit()
				for number in phone_numbers_list:
					newNumber= 'INSERT INTO AirStaff_PNumber (username, phone_number) VALUES (%s, %s)'
					cursor.execute(newNumber, (username, number))
				conn.commit()
				cursor.close()
				session['username']=username
				return redirect(url_for('airlineStaffProfile'))
			else: 
				error1='Cannot register because your airline is not in our system. Our database foerign key constraints only allow for a staff that is working for an airline in our system to register'
				return render_template('registerAirlineStaff.html', error1 = error1)

	else:
		return render_template('registerAirlineStaff.html')


#define route for checking flight status without logging in or registering
@app.route('/checkStatus', methods=['GET', 'POST'])
def checkStatus():
	if 'airlineName' in request.args:  #check if the form is already filled
		airlineName=request.args.get('airlineName')
		flightNumber=request.args.get('flightNumber')
		depDate=request.args.get('depDate')
		depDateEnd=datetime.strptime(depDate, "%Y-%m-%d") + timedelta(days=1)
		depDateEnd=depDateEnd.strftime("%Y-%m-%d 23:59:59")
		cursor=conn.cursor()
		query= '''
		SELECT
			airline_name, flight_number, departure_date_time, status_
		FROM 
			Flight
		WHERE
			airline_name= %s AND flight_number= %s AND departure_date_time>=%s AND departure_date_time<%s
		'''
		cursor.execute(query, (airlineName, flightNumber, depDate, depDateEnd))
		result=cursor.fetchone()
		error=None
		if result:
			return render_template('checkStatus.html', status=result)
		else:
			error='No flight is found based on what you searched.'
			return render_template('checkStatus.html', error=error)

	else:
		return render_template('checkStatus.html')

@app.route('/purchaseTicket', methods=['GET', 'POST'])
def purchaseTicket():
    flight_number = request.args.get('flight_number')
    departure_date_time = request.args.get('departure_date_time')
    
    # Ensure the user is logged in
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Process the form data and purchase the ticket
        # Extract data from the form
        # Implement the logic to store ticket information in the database
        pass
    else:
        # Display the ticket purchase form
        return render_template('purchase_ticket.html', flight_number=flight_number, departure_date_time=departure_date_time)



@app.route('/myFlights', methods=['GET'])
def myFlights():
    # Ensure the user is logged in
    user = session.get('username')
    if not user:
        return redirect(url_for('login'))

    message = request.args.get('message')
    error = request.args.get('error')
    
    cursor = conn.cursor()

    # Fetch flights booked by the logged-in user that are in the future
    query = '''
    SELECT Ticket.ticket_id, Flight.flight_number, Flight.departure_date_time, Flight.arrival_date_time, ...
    FROM Ticket
    JOIN Flight ON Ticket.flight_number = Flight.flight_number AND Ticket.airline_name = Flight.airline_name
    WHERE Ticket.customer_email = %s AND Flight.departure_date_time > NOW()
    '''
    cursor.execute(query, (user,))
    flights = cursor.fetchall()
    cursor.close()

    # Pass the current time to the template for comparison
    current_time = datetime.now()

    return render_template('my_flights.html', flights=flights, current_time=current_time, message=message, error=error)


@app.route('/cancelTicket', methods=['POST'])
def cancelTicket():
    # Ensure the user is logged in
    if 'username' not in session:
        return redirect(url_for('login'))

    user = session['username']
    ticket_id = request.form['ticket_id']

    cursor = conn.cursor()

    # Check if the flight is more than 24 hours ahead
    check_flight_time_query = '''
        SELECT departure_date_time FROM Flight
        JOIN Ticket ON Ticket.flight_number = Flight.flight_number
        WHERE Ticket.ticket_id = %s AND Flight.departure_date_time > NOW() + INTERVAL 24 HOUR
    '''
    cursor.execute(check_flight_time_query, (ticket_id,))
    flight_time = cursor.fetchone()

    if flight_time:
        # Flight is more than 24 hours ahead, proceed with cancellation
        cancel_ticket_query = '''
            DELETE FROM Ticket WHERE ticket_id = %s AND customer_email = %s
        '''
        cursor.execute(cancel_ticket_query, (ticket_id, user))
        conn.commit()
        cursor.close()
        # Redirect to the my flights page with a success message
        return redirect(url_for('myFlights', message='Your ticket has been successfully cancelled.'))
    else:
        cursor.close()
        # Redirect with an error message if the flight is less than 24 hours ahead
        return redirect(url_for('myFlights', error='Cancellation failed. Flights within 24 hours cannot be cancelled.'))

@app.route('/rateFlights', methods=['GET', 'POST'])
def rateFlights():
    # Ensure the user is logged in
    if 'username' not in session:
        return redirect(url_for('login'))
    
    user = session['username']
    cursor = conn.cursor()

    # Fetch past completed flights for the logged-in user
    query = '''
    SELECT Flight.flight_number, Flight.departure_date_time, Flight.arrival_date_time, ...
    FROM Ticket
    JOIN Flight ON Ticket.flight_number = Flight.flight_number AND Ticket.airline_name = Flight.airline_name
    WHERE Ticket.customer_email = %s AND Flight.arrival_date_time < NOW()
    '''
    cursor.execute(query, (user,))
    past_flights = cursor.fetchall()
    cursor.close()

    return render_template('rate_flights.html', past_flights=past_flights)

@app.route('/customerProfile')
def customerProfile():
    if 'username' not in session:
        return redirect(url_for('login'))

    user = session['username']
    cursor = conn.cursor()

    # Fetch customer information from the database
    query = 'SELECT * FROM Customer WHERE email = %s'
    cursor.execute(query, (user,))
    customer_info = cursor.fetchone()
    cursor.close()

    return render_template('customer_profile.html', customer_info=customer_info)

@app.route('/submitRating', methods=['POST'])
def submitRating():
    # Ensure the user is logged in
    if 'username' not in session:
        return redirect(url_for('login'))

    user = session['username']
    flight_number = request.form['flight_number']
    departure_date_time = request.form['departure_date_time']
    rating = request.form['rating']
    comment = request.form['comment']

    cursor = conn.cursor()

    # Insert or update the rating and comment for the flight
    rating_query = '''
    INSERT INTO Ratings (customer_email, flight_number, departure_date_time, rating, comment)
    VALUES (%s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE rating=%s, comment=%s
    '''
    cursor.execute(rating_query, (user, flight_number, departure_date_time, rating, comment, rating, comment))
    conn.commit()
    cursor.close()

    return redirect(url_for('rateFlights', message='Your feedback has been submitted.'))

@app.route('/logout')
def logout():
    # Clear the user session
    session.clear()
    return redirect(url_for('login'))

##@app.route('/customerProfile', methods=['GET', 'POST'])

##@app.route('/airlineStaffProfile', methods=['GET', 'POST'])

##and many other routes to come




		
app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
	app.run('127.0.0.1', 5000, debug = True)
