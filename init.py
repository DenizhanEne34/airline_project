# Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors
import hashlib
from datetime import datetime, timedelta

# Initialize the app from Flask
app = Flask(__name__)

# Configure MySQL
conn = pymysql.connect(host='127.0.0.1',
                       port=3307,
                       user='root',
                       password='',
                       db='airlinesproject2',  # change !
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)


@app.route('/', methods=['GET', 'POST'])
def hello():
    if 'depCity' in request.args:  # just to check if the form with get method is submitted or not
        # submit buttons have names action with values to handle different buttons on the same page
        if request.args.get('action') == 'oneWay':
            depCity = request.args.get('depCity')
            arrCity = request.args.get('arrCity')
            depDate = request.args.get('depDate')
            depDateEnd = datetime.strptime(
                depDate, "%Y-%m-%d") + timedelta(days=1)
            depDateEnd = depDateEnd.strftime("%Y-%m-%d 23:59:59")
            cursor = conn.cursor()
            query1 = '''
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
            result = cursor.fetchall()
            cursor.close()
            error = None
            if result:
                return render_template('index.html', onewayFlights=result)
            else:
                error = 'No flights are found'
                return render_template('index.html', error=error)

        elif request.args.get('action') == 'return':
            depCity = request.args.get('depCity')
            arrCity = request.args.get('arrCity')
            depDate = request.args.get('depDate')
            depDateEnd = datetime.strptime(
                depDate, "%Y-%m-%d") + timedelta(days=1)
            depDateEnd = depDateEnd.strftime("%Y-%m-%d 23:59:59")
            retDate = request.args.get('retDate')
            retDateEnd = datetime.strptime(
                retDate, "%Y-%m-%d") + timedelta(days=1)
            retDateEnd = retDateEnd.strftime("%Y-%m-%d 23:59:59")
            cursor = conn.cursor()
            query1 = '''
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

            cursor.execute(query1, (depCity, depDate, depDateEnd,
                           depCity, retDate, retDateEnd))
            result = cursor.fetchall()
            cursor.close()
            error = None
            if result:
                return render_template('index.html', returnFlights=result)
            else:
                error = 'No flights are found'
                return render_template('index.html', error=error)

    else:
        return render_template('index.html')

# Define route for login


# only one route is enough to handle login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['action'] == 'loginCustomer':
            email = request.form['username']
            password = request.form['password']
            hashed_password = hashlib.md5(password.encode()).hexdigest()
            cursor = conn.cursor()
            query = 'SELECT * FROM Customer WHERE email = %s and password_ = %s'
            cursor.execute(query, (email, hashed_password))
            result = cursor.fetchone()
            cursor.close()
            error = None
            if result:
                session['username'] = email
                return redirect(url_for('customerProfile'))
            else:
                error = 'Invalid login or username'
                return render_template('login.html', error=error)

        elif request.form['action'] == 'loginAirlineStaff':
            username = request.form['username']
            password = request.form['password']
            hashed_password = hashlib.md5(password.encode()).hexdigest()
            cursor = conn.cursor()
            query = 'SELECT * FROM AirlineStaff WHERE username = %s and password_ = %s'
            cursor.execute(query, (username, hashed_password))
            result = cursor.fetchone()
            cursor.close()
            error = None
            if result:
                session['username'] = username
                return redirect(url_for('airlineStaffProfile'))
            else:
                error = 'Invalid login or username'
                return render_template('login.html', error=error)

    else:
        return render_template('login.html')

# Define route for register


@app.route('/registerCustomer', methods=['GET', 'POST'])
def registerCustomer():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        hashed_password = hashlib.md5(password.encode()).hexdigest()
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        building_no = request.form['building_no']
        street_name = request.form['street_name']
        apt_number = request.form['apt_number']
        city = request.form['city']
        state_ = request.form['state_']
        zip_code = request.form['zip_code']
        passport_number = request.form['passport_number']
        passport_expiration = request.form['passport_expiration']
        passport_country = request.form['passport_country']
        date_of_birth = request.form['date_of_birth']
        phone_numbers = request.form['phone_numbers']
        phone_numbers_list = phone_numbers.split(',')
        cursor = conn.cursor()
        query = 'SELECT * FROM Customer WHERE email = %s'
        cursor.execute(query, (email))
        result = cursor.fetchone()
        error = None
        if result:
            error = "This user already exists"
            return render_template('registerCustomer.html', error=error)

        else:
            newCustomer = 'INSERT INTO Customer (email, password_, first_name,last_name,building_no,street_name,apt_number,city,state_,zip_code,passport_number,passport_expiration,passport_country,date_of_birth ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,%s,%s,%s,%s,%s)'
            cursor.execute(newCustomer, (email, hashed_password, first_name, last_name, building_no, street_name,
                           apt_number, city, state_, zip_code, passport_number, passport_expiration, passport_country, date_of_birth))
            conn.commit()
            session['username'] = email
            for number in phone_numbers_list:
                newPhoneNumbers = 'INSERT INTO Cust_PNumber (email, phone_number) VALUES (%s, %s)'
                cursor.execute(newPhoneNumbers, (email, number))
            conn.commit()
            cursor.close()
            return redirect(url_for('customerProfile'))

    else:
        return render_template('registerCustomer.html')


@app.route('/registerAirlineStaff', methods=['GET', 'POST'])
def registerAirlineStaff():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        date_of_birth = request.form['date_of_birth']
        airline_name = request.form['airline_name']
        emails = request.form['emails']
        phone_numbers = request.form['phone_numbers']
        emails_list = emails.split(',')
        phone_numbers_list = phone_numbers.split(',')
        hashed_password = hashlib.md5(password.encode()).hexdigest()
        cursor = conn.cursor()
        query = 'SELECT * FROM AirlineStaff WHERE username = %s'
        cursor.execute(query, (username))
        result = cursor.fetchone()
        error = None
        error1 = None
        if result:
            error = "This user already exists"
            return render_template('registerAirlineStaff.html', error=error)

        else:
            query1 = 'SELECT * FROM Airline WHERE airline_name = %s'
            cursor.execute(query1, (airline_name))
            result1 = cursor.fetchone()
            if result1:
                newAirlineStaff = 'INSERT INTO AirlineStaff (username, password_, first_name,last_name,date_of_birth,airline_name) VALUES (%s, %s, %s,%s,%s,%s)'
                cursor.execute(newAirlineStaff, (username, hashed_password,
                               first_name, last_name, date_of_birth, airline_name))
                conn.commit()
                for email in emails_list:
                    newEmails = 'INSERT INTO AirStaff_Email (username, email) VALUES (%s, %s)'
                    cursor.execute(newEmails, (username, email))
                conn.commit()
                for number in phone_numbers_list:
                    newNumber = 'INSERT INTO AirStaff_PNumber (username, phone_number) VALUES (%s, %s)'
                    cursor.execute(newNumber, (username, number))
                conn.commit()
                cursor.close()
                session['username'] = username
                return redirect(url_for('airlineStaffProfile'))
            else:
                error1 = 'Cannot register because your airline is not in our system. Our database foerign key constraints only allow for a staff that is working for an airline in our system to register'
                return render_template('registerAirlineStaff.html', error1=error1)

    else:
        return render_template('registerAirlineStaff.html')

# define route for checking flight status without logging in or registering


@app.route('/checkStatus', methods=['GET', 'POST'])
def checkStatus():
    if 'airlineName' in request.args:  # check if the form is already filled
        airlineName = request.args.get('airlineName')
        flightNumber = request.args.get('flightNumber')
        depDate = request.args.get('depDate')
        depDateEnd = datetime.strptime(depDate, "%Y-%m-%d") + timedelta(days=1)
        depDateEnd = depDateEnd.strftime("%Y-%m-%d 23:59:59")
        cursor = conn.cursor()
        query = '''
		SELECT
			airline_name, flight_number, departure_date_time, status_
		FROM 
			Flight
		WHERE
			airline_name= %s AND flight_number= %s AND departure_date_time>=%s AND departure_date_time<%s
		'''
        cursor.execute(query, (airlineName, flightNumber, depDate, depDateEnd))
        result = cursor.fetchone()
        error = None
        if result:
            return render_template('checkStatus.html', status=result)
        else:
            error = 'No flight is found based on what you searched.'
            return render_template('checkStatus.html', error=error)

    else:
        return render_template('checkStatus.html')


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


# @app.route('/customerProfile', methods=['GET', 'POST'])
# Check if the user is authorized as airline staff
def is_airline_staff(username):
    cursor = conn.cursor()
    query = "SELECT * FROM AirlineStaff WHERE username = %s"
    cursor.execute(query, (username,))
    staff = cursor.fetchone()
    return staff is not None

# Retrieve the logged-in staff member's airline name


def get_airline_name(username):
    cursor = conn.cursor()
    query = "SELECT airline_name FROM AirlineStaff WHERE username = %s"
    cursor.execute(query, (username,))
    airline_name = cursor.fetchone()
    return airline_name['airline_name']


@app.route('/airlineStaffProfile', methods=['GET', 'POST'])
def airlineStaffProfile():
    # Ensure the user is logged in
    if 'username' not in session or not is_airline_staff(session['username']):
        return redirect(url_for('login'))  # Redirect unauthorized users

    username = session.get('username')
    airline_name = get_airline_name(username)

    return render_template('airlineStaffProfile.html', username=username, airline_name=airline_name)


# Retrieve future flights for the next 30 days
def get_future_flights(airline_name):
    cursor = conn.cursor()
    current_datetime = datetime.now()
    future_datetime = current_datetime + timedelta(days=30)

    query = """
    SELECT * FROM Flight
    WHERE airline_name = %s
    AND departure_date_time BETWEEN %s AND %s
    """
    cursor.execute(query, (airline_name, current_datetime, future_datetime))
    future_flights = cursor.fetchall()

    return future_flights

# Route for creating a new flight and displaying future flights


@app.route('/createFlight', methods=['GET', 'POST'])
def createFlight():
    if 'username' not in session or not is_airline_staff(session.get('username')):
        return redirect(url_for('login'))  # Redirect unauthorized users

    # Retrieve the airline name based on the staff member's username
    airline_name = get_airline_name(session['username'])

    if request.method == 'POST':
        flight_number = request.form['flightNumber']
        departure_date_time = request.form['departureDateTime']
        arrival_date_time = request.form['arrivalDateTime']
        departure_airport_code = request.form['departureAirportCode']
        arrival_airport_code = request.form['arrivalAirportCode']
        base_price = request.form['basePrice']

        cursor = conn.cursor()
        query = """
        INSERT INTO Flight (airline_name, flight_number, departure_date_time, arrival_date_time, 
                            departure_airport_code, arrival_airport_code, base_price)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (airline_name, flight_number, departure_date_time, arrival_date_time,
                               departure_airport_code, arrival_airport_code, base_price))
        conn.commit()

    # Display future flights for the next 30 days
    future_flights = get_future_flights(airline_name)
    return render_template('createFlight.html', futureFlights=future_flights)


@app.route('/changeFlightStatus', methods=['GET', 'POST'])
def changeFlightStatus():
    # Check if the user is logged in and authorized
    if 'username' not in session or not is_airline_staff(session['username']):
        return redirect(url_for('login'))  # Redirect unauthorized users

    if request.method == 'POST':
        airlineName = request.form.get('airlineName')
        flightNumber = request.form.get('flightNumber')
        depDate = request.form.get('depDate')
        depDateEnd = datetime.strptime(depDate, "%Y-%m-%d") + timedelta(days=1)
        depDateEnd = depDateEnd.strftime("%Y-%m-%d 23:59:59")
        newStatus = request.form.get('new_status')  # Updated to match the HTML
        # check if flight exists
        cursor = conn.cursor()
        query = '''
		SELECT
			airline_name, flight_number, departure_date_time, status_
		FROM 
			Flight
		WHERE
			airline_name= %s AND flight_number= %s AND departure_date_time>=%s AND departure_date_time<%s
		'''
        cursor.execute(query, (airlineName, flightNumber, depDate, depDateEnd))
        result = cursor.fetchone()
        error = None
        if not result:
            error = 'No flight is found based on what you searched.'
            return render_template('changeFlightStatus.html', error=error)
        # update flight if it exists
        query = '''
        UPDATE Flight
        SET status_ = %s
        WHERE airline_name = %s AND flight_number = %s AND departure_date_time>=%s AND departure_date_time<%s
        '''
        cursor.execute(query, (newStatus, airlineName,
                       flightNumber, depDate, depDateEnd))
        conn.commit()
        result = cursor.fetchone()
        error = None
        return render_template('changeFlightStatus.html', status=result)
    else:
        return render_template('changeFlightStatus.html')


def get_airplanes(airline_name):
    cursor = conn.cursor()
    query = "SELECT * FROM Airplane WHERE airline_name = %s"
    cursor.execute(query, (airline_name,))
    airplanes = cursor.fetchall()
    return airplanes


@app.route('/addAirplaneForm', methods=['GET', 'POST'])
def addAirplaneForm():
    # Check if the user is logged in and authorized
    if 'username' not in session or not is_airline_staff(session['username']):
        return redirect(url_for('login'))  # Redirect unauthorized users

    if request.method == 'POST':
        airline_name = get_airline_name(session.get('username'))
        airplane_id = request.form['airplaneId']
        number_of_seats = request.form['numberOfSeats']
        manu_company = request.form['manufacturerCompany']
        model_number = request.form['modelNumber']
        manu_date = request.form['manufactureDate']
        age = request.form['age']

        cursor = conn.cursor()
        query = """
        INSERT INTO Airplane (airline_name, airplane_id, number_of_seats, manu_company, model_number, manu_date, age)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (airline_name, airplane_id,
                       number_of_seats, manu_company, model_number, manu_date, age))
        conn.commit()

    return render_template('addAirplaneForm.html')

# Function to check if an airport already exists


def airport_exists(airport_code):
    cursor = conn.cursor()
    query = "SELECT * FROM Airport WHERE airport_code = %s"
    cursor.execute(query, (airport_code,))
    return cursor.fetchone() is not None

# Route for adding a new airport


@app.route('/addAirportForm', methods=['GET', 'POST'])
def addAirportForm():
    # Check if the user is logged in and authorized
    if 'username' not in session or not is_airline_staff(session['username']):
        return redirect(url_for('login'))  # Redirect unauthorized users

    if request.method == 'POST':
        airport_code = request.form['airportCode']
        airport_name = request.form['airportName']
        city = request.form['city']
        country = request.form['country']
        num_of_terminals = request.form['numOfTerminals']
        airport_type = request.form['airportType']

        # Check if the record already exists
        if airport_exists(airport_code):
            error = f"Airport with code '{airport_code}' already exists."
            return render_template('addAirportForm.html', error=error)

        cursor = conn.cursor()
        query = """
        INSERT INTO Airport (airport_code, airport_name, city, country, num_of_terminals, type_)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (airport_code, airport_name, city,
                       country, num_of_terminals, airport_type))
        conn.commit()

    return render_template('addAirportForm.html')


@app.route('/viewFlightRatingsForm', methods=['GET', 'POST'])
def viewFlightRatingsForm():
    # Check if the user is logged in and authorized
    if 'username' not in session or not is_airline_staff(session['username']):
        return redirect(url_for('login'))  # Redirect unauthorized users
    if 'airlineName' in request.args:
        print('test 1')
        airline_name = request.args['airlineName']
        flight_number = request.args['flightNumber']
        depDate = request.args.get('depDate')
        depDateEnd = datetime.strptime(depDate, "%Y-%m-%d") + timedelta(days=1)
        depDateEnd = depDateEnd.strftime("%Y-%m-%d 23:59:59")

        cursor = conn.cursor()
        query = """
        SELECT AVG(rating) as average_rating, email, rating, comments
        FROM Evaluations
        WHERE airline_name = %s AND flight_number = %s AND departure_date_time>=%s AND departure_date_time<%s
        GROUP BY email, rating, comments
        """
        cursor.execute(
            query, (airline_name, flight_number, depDate, depDateEnd))
        result = cursor.fetchall()

        if result:
            print('test 2')
            average_rating = result[0]['average_rating']
            ratings = [{'email': row['email'], 'rating': row['rating'],
                        'comments': row['comments']} for row in result]
            flight_rating = {
                'average_rating': average_rating, 'ratings': ratings}

        result = cursor.fetchone()
        error = None
        print(result,'111111111111111')
        if result:
            return render_template('viewFlightRatingsForm.html', flight_rating=result)
        else:
            print('test 3')
            error = 'No flight is found based on what you searched.'
            return render_template('viewFlightRatingsForm.html', error=error)

    else:
        print(request.args)
        return render_template('viewFlightRatingsForm.html')


@app.route('/scheduleMaintenanceForm', methods=['GET','POST'])
def scheduleMaintenanceForm():
    # Check if the user is logged in and authorized
    if 'username' not in session or not is_airline_staff(session['username']):
        return redirect(url_for('login'))  # Redirect unauthorized users

    if request.method == 'POST':
        airline_name = request.form['airlineName']
        airplane_id = request.form['airplaneId']
        start_date_time = request.form['startDate']
        end_date_time = request.form['endDate']

		# Check if the airplane exists
        cursor = conn.cursor()
        query_check_airplane = """
        SELECT *
        FROM Airplane
        WHERE airline_name = %s AND airplane_id = %s
        """
        cursor.execute(query_check_airplane, (airline_name, airplane_id))
        existing_airplane = cursor.fetchone()

        if not existing_airplane:
            error = 'The specified airplane does not exist.'
            return render_template('scheduleMaintenanceForm.html', error=error)

        # Validate start and end date times
        start_datetime = datetime.strptime(start_date_time, "%Y-%m-%dT%H:%M")
        end_datetime = datetime.strptime(end_date_time, "%Y-%m-%dT%H:%M")

        if start_datetime >= end_datetime:
            error = 'End date and time must be later than start date and time.'
            return render_template('scheduleMaintenanceForm.html', error=error)

        # Check if the airplane is available for maintenance during the specified period
        cursor = conn.cursor()
        query_check_availability = """
        SELECT *
        FROM Maintenance
        WHERE airline_name = %s
          AND airplane_id = %s
          AND NOT (end_date_time <= %s OR start_date_time >= %s)
        """
        cursor.execute(query_check_availability, (airline_name, airplane_id, start_date_time, end_date_time))
        conflicting_maintenance = cursor.fetchone()

        if conflicting_maintenance:
            error = 'The airplane is not available for maintenance during the specified period.'
            return render_template('scheduleMaintenanceForm.html', error=error)

        # Schedule maintenance for the airplane
        query_schedule_maintenance = """
        INSERT INTO Maintenance (airline_name, airplane_id, start_date_time, end_date_time)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query_schedule_maintenance, (airline_name, airplane_id, start_date_time, end_date_time))
        conn.commit()

        return render_template('scheduleMaintenanceForm.html', success=True)

    return render_template('scheduleMaintenanceForm.html')


@app.route('/viewEarnedRevenueForm', methods=['GET','POST'])
def viewEarnedRevenueForm():
    # Check if the user is logged in and authorized
    if 'username' not in session or not is_airline_staff(session['username']):
        return redirect(url_for('login'))  # Redirect unauthorized users

    revenue = None

    # Calculate total revenue for the last month and last year
    cursor = conn.cursor()

    # Total revenue last month
    query_last_month = """
    SELECT COALESCE(SUM(calculated_price), 0) as total_last_month
    FROM Ticket
    WHERE purchase_date_time >= CURDATE() - INTERVAL 1 MONTH
    """
    cursor.execute(query_last_month)
    result_last_month = cursor.fetchone()
    total_last_month = result_last_month['total_last_month']

    # Total revenue last year
    query_last_year = """
    SELECT COALESCE(SUM(calculated_price), 0) as total_last_year
    FROM Ticket
    WHERE purchase_date_time >= CURDATE() - INTERVAL 1 YEAR
    """
    cursor.execute(query_last_year)
    result_last_year = cursor.fetchone()
    total_last_year = result_last_year['total_last_year']

    # Combine results into a dictionary
    revenue = {
        'last_month': total_last_month,
        'last_year': total_last_year
    }

    return render_template('viewEarnedRevenueForm.html', revenue=revenue)


@app.route('/viewFrequentCustomersForm', methods=['GET','POST'])
def viewFrequentCustomersForm():
    # Check if the user is logged in and authorized
    if 'username' not in session or not is_airline_staff(session['username']):
        return redirect(url_for('login'))  # Redirect unauthorized users

    customer_details = None

    if 'customerEmail' in request.args:
        customer_email = request.form['customerEmail']
        airline_name = get_airline_name(session['username'])

        # Get the most frequent customer within the last year
        cursor = conn.cursor()
        query_most_frequent_customer = """
        SELECT email, COUNT(*) as total_flights
        FROM Ticket
        WHERE purchase_date_time >= NOW() - INTERVAL 1 YEAR
          AND email = %s
        GROUP BY email
        ORDER BY total_flights DESC
        LIMIT 1
        """
        cursor.execute(query_most_frequent_customer, (customer_email,))
        result_most_frequent_customer = cursor.fetchone()

        most_frequent_customer = {
            'email': result_most_frequent_customer['email'],
            'total_flights': result_most_frequent_customer['total_flights']
        } if result_most_frequent_customer else None

        # Get the customer's flights on the airline
        query_customer_flights = """
        SELECT f.airline_name, f.flight_number, f.departure_date_time, f.arrival_date_time, f.base_price
        FROM Flight f
        JOIN Ticket t ON f.airline_name = t.airline_name
                     AND f.flight_number = t.flight_number
                     AND f.departure_date_time = t.departure_date_time
        WHERE t.email = %s
          AND f.airline_name = %s
        """
        cursor.execute(query_customer_flights, (customer_email, airline_name))
        result_customer_flights = cursor.fetchall()

        customer_flights = [{
            'airline_name': flight['airline_name'],
            'flight_number': flight['flight_number'],
            'departure_date_time': flight['departure_date_time'],
            'arrival_date_time': flight['arrival_date_time'],
            'base_price': flight['base_price'],
        } for flight in result_customer_flights]

        customer_details = {
            'most_frequent_customer': most_frequent_customer,
            'airline_name': airline_name,
            'flights': customer_flights
        }

    return render_template('viewFrequentCustomersForm.html', customer_details=customer_details)


# logout function
@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')


app.secret_key = 'some key that you will never guess'
# Run the app on localhost port 5000
# debug = True -> you don't have to restart flask
# for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug=True)
