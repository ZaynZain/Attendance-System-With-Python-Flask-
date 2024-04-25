from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'y89unvwpq'  # Change this to a random secret key
def create_connection(host_name, user_name, user_password, db_name):
    connection = None
    try:
        connection = mysql.connector.connect(
            host=host_name,
            user=user_name,
            passwd=user_password,
            database=db_name
        )
        print("Connection to MySQL DB successful")
    except Error as e:
        print(f"The error '{e}' occurred")

    return connection

def execute_query(connection, query, data=None):
    cursor = connection.cursor()
    try:
        if data:
            cursor.execute(query, data)
        else:
            cursor.execute(query)
        connection.commit()
        print("Query executed successfully")
    except Error as e:
        print(f"The error '{e}' occurred")
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        try:
            connection = create_connection("localhost", "root", "", "attendance_system")
            cursor = connection.cursor()
            query = "INSERT INTO users (username, password) VALUES (%s, %s)"
            data = (username, hashed_password)
            execute_query(connection, query, data)
            # user_id = cursor.fetchone()[0]
            # print("the user id is :", user_id)
            # session['username'] = username  # Start session for the user
            # session['user_id'] = user_id
            flash('You have successfully registered!', 'success')
            return redirect(url_for('login'))
        except Error as e:
            print(e)
            flash('An error occurred while registering. Please try again.', 'danger')
        finally:
            if connection:
                connection.close()

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Check if the login is for the admin
        if username == 'adminzain' and password == 'adminzain123':
            session['username'] = username
            return redirect(url_for('admin'))

        try:
            connection = create_connection("localhost", "root", "", "attendance_system")
            print("connection establish")
            query = "SELECT * FROM users WHERE username = %s"
            data = (username,)
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, data)
            user = cursor.fetchone()
            print(user)
            if user and check_password_hash(user['password'] , password):
                session['user_id'] = user['user_id']
                # user_id = session['user_id']
                session['username'] = username

                flash('Login successful!', 'success')
                return redirect(url_for('user_panel'))

                flash('Invalid username or password. Please try again.', 'danger')
        except Error as e:
            print(e)
            flash('An error occurred while logging in. Please try again.', 'danger')
        finally:
            if connection:
                connection.close()

    return render_template('login.html')
@app.route('/logout')
def logout():
    session.pop('username', None)  # Clear the session
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))


@app.route('/user_panel', methods=['GET', 'POST'])
def user_panel():
    cursor = None
    connection = None

    if request.method == 'POST':
        mark_attendance_present = request.form.get('attendance_present')
        mark_attendance_absent = request.form.get('attendance_absent')
        print(mark_attendance_absent)
        try:
            if 'username' not in session:
                return redirect(url_for('login'))

            user_id = session['user_id']
            connection = create_connection("localhost", "root", "", "attendance_system")
            print("connection established")
            cursor = connection.cursor(dictionary=True)
            if mark_attendance_present == "present":
                cursor.execute("INSERT INTO attendance (user_id, attendance_date, status) VALUES (%s, %s, %s)",
                               (user_id, datetime.now().date(), "present"))
                flash('You Marked Your Attendance As a Present, Thanks')
            elif mark_attendance_absent == "absent":
                cursor.execute("INSERT INTO attendance (user_id, attendance_date, status) VALUES (%s, %s, %s)",
                               (user_id, datetime.now().date(), "absent"))
                flash('You Marked Your Attendance As a Absent ☹')

            else:
                # Handle case where neither attendance_present nor attendance_absent is set
                flash("Your Attendance is Not Marked Select one Option for Attendance")


            connection.commit()

        except mysql.connector.Error as e:
            print('error', e)
            flash('Your Attendance was not Marked due to a system problem. Please try again later.')
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    if 'username' in session:
        username = session['username']
        print(" dashboard username", username)
        return render_template('user_panel.html', user=username)
    else:
        flash("Please create your account first to get access")
        return redirect(url_for('register'))


@app.route('/profile')
def profile():
    try:
        if 'username' in session:
            username = session['username']
            connection = create_connection("localhost", "root", "", "attendance_system")
            print("connection establish")
            query = "SELECT * FROM users WHERE username = %s"
            data = (username,)
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, data)
            user_data = cursor.fetchone()
            return render_template('profile.html', user_data=user_data)
    except Exception as e:
        print('The error in gating data from database:', {e})
@app.route('/mark_attendance')
def mark_attendance():
    try:
        if 'username' in session:
            username = session['username']
            connection = create_connection("localhost", "root", "", "attendance_system")
            print("connection establish")
            query = "SELECT * FROM users WHERE username = %s"
            data = (username,)
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, data)
            user_data = cursor.fetchone()
            print('the data of the user: ', user_data)
            # Get the current date
            current_date = datetime.now().strftime('%Y-%m-%d')

        return render_template('mark_attendance.html', user_data= user_data, current_date=current_date)
    except Exception as e:
        return f"An error occurred: {str(e)}"
@app.route('/fetch_attendance', methods=['GET'])
def fetch_attendance():
    try:
        if 'username' not in session:
            return "User not logged in", 403  # Return forbidden status if user is not logged in
        username = session['username']
        connection = create_connection("localhost", "root", "", "attendance_system")
        print("connection established")
        query = "SELECT * FROM attendance WHERE user_id = (SELECT user_id FROM users WHERE username = %s)"
        data = (username,)
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, data)
        attendance_data = cursor.fetchall()
        return render_template('view_attendance.html', attendance_data=attendance_data)
    except Exception as e:
        print('Error fetching attendance:', e)
        flash("Error fetching attendance")
        return redirect(url_for('user_panel'))
    finally:
        if connection:
            connection.close()

# Route to render the leave request form
@app.route('/leave')
def leave():
    return render_template('leave.html')
# Route to handle leave request submission
@app.route('/submit_leave', methods=['POST'])
def submit_leave():
    if request.method == 'POST':
        subject = request.form['subject']
        reason = request.form['reason']

        # Retrieve the logged-in user's ID from the session
        user_id = session.get('user_id')

        if user_id is None:
            flash('You must be logged in to submit a leave request.', 'danger')
            return redirect(url_for('login'))  # Redirect to login page if user is not logged in

        try:
            connection = create_connection("localhost", "root", "", "attendance_system")
            cursor = connection.cursor()
            query = "INSERT INTO attendance (user_id, status, attendance_date, subject, reason) VALUES (%s, %s, %s, %s, %s)"
            data = (user_id, 'leave', datetime.now().date(), subject, reason)  # Assuming 'leave' status for leave requests
            cursor.execute(query, data)
            connection.commit()

            flash('Leave request submitted successfully!', 'success')
        except Error as e:
            print(f"The error '{e}' occurred")
            flash('An error occurred while submitting leave request.', 'danger')
        finally:
            if connection:
                connection.close()

    return redirect(url_for('index'))# Backend function to fetch user records and attendance data from the database
def get_user_records():
    connection = None
    try:
        connection = create_connection("localhost", "root", "", "attendance_system")
        if connection is not None and connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
               SELECT u.user_id, u.username, GROUP_CONCAT(a.status) AS statuses,GROUP_CONCAT(a.attendance_date) AS dates
                FROM users u
                LEFT JOIN attendance a ON u.user_id = a.user_id
                GROUP BY u.user_id
            """)
            user_records = cursor.fetchall()
            return user_records
    except mysql.connector.Error as e:
        print("Error reading data from MySQL table:", e)
    finally:
        if connection is not None and connection.is_connected():
            connection.close()

# Admin panel route to display user records
# Modify the admin_user_records route to include authentication check
@app.route('/admin')
def admin():
    if 'username' in session:
        # Check if the user is authenticated as an admin
        if session['username'] == 'adminzain':  # Change this to your admin username
            user_records = get_user_records()
            return render_template('admin.html', user_records=user_records)
        else:

            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('user_panel'))
    else:
        flash('You must be logged in to access this page.', 'danger')
        return redirect(url_for('login'))


# Route to handle report generation
@app.route('/generate_report', methods=['POST'])
def generate_report():
    if request.method == 'POST':
        from_date = request.form['from_date']
        to_date = request.form['to_date']

        try:
            connection = create_connection("localhost", "root", "", "attendance_system")
            cursor = connection.cursor(dictionary=True)
            query = "SELECT u.username, a.status, a.attendance_date FROM users u LEFT JOIN attendance a ON u.user_id = a.user_id WHERE a.attendance_date BETWEEN %s AND %s"
            data = (from_date, to_date)
            cursor.execute(query, data)
            report_data = cursor.fetchall()

            return render_template('report.html', report_data=report_data, from_date=from_date, to_date=to_date)
        except Error as e:
            print(f"The error '{e}' occurred")
            flash('An error occurred while generating the report.', 'danger')
        finally:
            if connection:
                connection.close()

    return render_template('generate_report.html')




# Backend code to handle attendance editing
@app.route('/edit_attendance', methods=['GET', 'POST'])
def edit_attendance():
    if request.method == 'POST':
        user_id = request.form['user_id']
        new_status = request.form['new_status']
        attendance_date = request.form['attendance_date']

        try:
            connection = create_connection("localhost", "root", "", "attendance_system")
            cursor = connection.cursor()
            query = "UPDATE attendance SET status = %s WHERE user_id = %s AND attendance_date = %s"
            data = (new_status, user_id, attendance_date)
            cursor.execute(query, data)
            connection.commit()

            flash('Attendance updated successfully!', 'success')
        except Error as e:
            print(f"The error '{e}' occurred")
            flash('An error occurred while updating attendance.', 'danger')
        finally:
            if connection:
                connection.close()

    return redirect(url_for('admin'))  # Redirect back to admin panel after editing attendance



if __name__ == '__main__':
    app.run(debug=True,port=8000)

