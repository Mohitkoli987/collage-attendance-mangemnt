from flask import Flask, render_template, request, redirect, url_for, flash,send_file, session,make_response
from flask_mysqldb import MySQL

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import openpyxl
import xlsxwriter
import io
import pandas as pd
from io import BytesIO
import os
import smtplib  # For sending emails
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.rest import Client





from werkzeug.utils import secure_filename

# Ensure you define the upload folder and allowed extensions


app = Flask(__name__)


UPLOAD_FOLDER = 'static/uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif','xls', 'xlsx'}



def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Configure MySQL
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '12345678'
app.config['MYSQL_DB'] = 'collage6'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['SECRET_KEY'] = 'your_secret_key'  # Set a strong secret key

# Initialize MySQL
mysql = MySQL(app)

# Home route
@app.route('/')
def home():
    try:
        return render_template('common/index.html',)
    except Exception as e:
        return str(e)

# About Us route
@app.route('/about')
def about_us():
    try:
        return render_template('common/aboutus.html')
    except Exception as e:
        return str(e)

# Contact Us route
@app.route('/contact', methods=['GET', 'POST'])
def contact_us():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        # Here you can implement logic to save or send the contact form data
        flash('Your message has been sent successfully!', 'success')
        return redirect(url_for('contact_us'))
    return render_template('common/contactus.html')


    
@app.route('/teacher/signup', methods=['GET', 'POST'])
def teacher_signup():
    if request.method == 'POST':
        name = request.form['name']
        short_name = request.form['short_name']
        email = request.form['email']
        contact = request.form['contact']
        department = request.form['department']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Check if passwords match
        if password != confirm_password:
            return "Passwords do not match", 400
        
        # Check if email already exists
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM teachers WHERE email = %s', (email,))
        existing_teacher = cursor.fetchone()
        if existing_teacher:
            return "Email already exists", 400
        
        # Insert new teacher into the database
        cursor.execute('INSERT INTO teachers (name, short_name, email, contact, department, password) VALUES (%s, %s, %s, %s, %s, %s)',
                       (name, short_name, email, contact, department, generate_password_hash(password)))
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('teacher_login'))
    
    return render_template('teacher/teacher_signup.html')

@app.route('/teacher/login', methods=['GET', 'POST'])
def teacher_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM teachers WHERE email = %s', (email,))
        teacher = cursor.fetchone()
        cursor.close()

        if teacher and check_password_hash(teacher['password'], password):
            session['teacher_id'] = teacher['id']
            session['teacher_photo'] = teacher['profile_photo']  # Store the profile photo in the session
            return redirect(url_for('teacher_dashboard'))
        else:
            return 'Invalid credentials'
    return render_template('teacher/teacher_login.html')

@app.route('/teacher/profile')
def teacher_profile():
    if 'teacher_id' not in session:
        flash('You need to be logged in to access this page.', 'danger')
        return redirect(url_for('teacher_login'))

    teacher_id = session['teacher_id']
    cursor = mysql.connection.cursor()
    
    # Fetch teacher details
    cursor.execute('SELECT * FROM teachers WHERE id = %s', (teacher_id,))
    teacher = cursor.fetchone()
    
    # Fetch courses taught by the teacher
    cursor.execute('SELECT * FROM courses WHERE teacher_id = %s', (teacher_id,))
    courses = cursor.fetchall()
    cursor.close()

    return render_template('teacher/teacher_profile.html', teacher=teacher, courses=courses)


@app.route('/teacher/my_courses')
def my_courses():
    if 'teacher_id' not in session:
        flash('You need to be logged in to access this page.', 'danger')
        return redirect(url_for('teacher_login'))

    teacher_id = session['teacher_id']
    cursor = mysql.connection.cursor()

    # Fetch teacher details
    cursor.execute('SELECT * FROM teachers WHERE id = %s', (teacher_id,))
    teacher = cursor.fetchone()

    # Fetch the teacher's courses from the database
    cursor.execute('SELECT * FROM courses WHERE teacher_id = %s', (teacher_id,))
    courses = cursor.fetchall()
    cursor.close()

    return render_template('teacher/my_courses.html', teacher=teacher, courses=courses)

@app.route('/edit_teacher_profile', methods=['GET', 'POST'])
def edit_teacher_profile():
    if 'teacher_id' not in session:
        return redirect(url_for('teacher_login'))

    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM teachers WHERE id = %s', (session['teacher_id'],))
    teacher = cursor.fetchone()

    if request.method == 'POST':
        name = request.form['name']
        short_name = request.form['short_name']  # Get short name from form
        email = request.form['email']
        contact = request.form['contact']
        department = request.form['department']
        profile_photo = teacher['profile_photo']  # Default to existing photo

        # Handle profile photo upload
        if 'profile_photo' in request.files:
            file = request.files['profile_photo']
            if file and file.filename != '':
                profile_photo = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], profile_photo))

        # Handle profile photo removal
        if 'remove_photo' in request.form:
            if profile_photo != 'nophoto.jpg':
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], profile_photo))
                profile_photo = 'nophoto.jpg'

        # Update teacher's profile in the database, including short name
        cursor.execute("""
            UPDATE teachers 
            SET name = %s, short_name = %s, email = %s, contact = %s, department = %s, profile_photo = %s 
            WHERE id = %s
        """, (name, short_name, email, contact, department, profile_photo, session['teacher_id']))
        mysql.connection.commit()
        cursor.close()

        # Update the session photo and short name immediately after upload or removal
        session['teacher_photo'] = profile_photo
        session['teacher_short_name'] = short_name

        return redirect(url_for('teacher_profile'))

    return render_template('teacher/edit_teacher_profile.html', teacher=teacher)


@app.route('/remove_teacher_photo')
def remove_teacher_photo():
    if 'teacher_id' not in session:
        flash('You need to be logged in to access this page.', 'danger')
        return redirect(url_for('teacher_login'))

    teacher_id = session['teacher_id']
    cursor = mysql.connection.cursor()

    # Set the profile photo to the default 'nophoto.jpg'
    cursor.execute("""
        UPDATE teachers
        SET profile_photo = 'nophoto.jpg'
        WHERE id = %s
    """, (teacher_id,))
    mysql.connection.commit()
    cursor.close()

    flash('Profile photo removed successfully.', 'success')
    return redirect(url_for('edit_teacher_profile'))


@app.route('/teacher_dashboard')
def teacher_dashboard():
    cursor = mysql.connection.cursor()

    # Query for counting today's present students
    cursor.execute("""
        SELECT COUNT(*) AS present_count
        FROM attendance
        WHERE present = 1 AND date = CURDATE()
    """)
    present_data = cursor.fetchone()
    present_count = present_data['present_count']

    # Query for counting today's absent students
    cursor.execute("""
        SELECT COUNT(*) AS absent_count
        FROM attendance
        WHERE present = 0 AND date = CURDATE()
    """)
    absent_data = cursor.fetchone()
    absent_count = absent_data['absent_count']

    # Query for counting yesterday's present students
    cursor.execute("""
        SELECT COUNT(*) AS present_count_yesterday
        FROM attendance
        WHERE present = 1 AND date = CURDATE() - INTERVAL 1 DAY
    """)
    present_yesterday_data = cursor.fetchone()
    present_count_yesterday = present_yesterday_data['present_count_yesterday']

    # Query for counting yesterday's absent students
    cursor.execute("""
        SELECT COUNT(*) AS absent_count_yesterday
        FROM attendance
        WHERE present = 0 AND date = CURDATE() - INTERVAL 1 DAY
    """)
    absent_yesterday_data = cursor.fetchone()
    absent_count_yesterday = absent_yesterday_data['absent_count_yesterday']

    # Calculate percentage increase for present and absent students
    if present_count_yesterday > 0:
        present_increase = ((present_count - present_count_yesterday) / present_count_yesterday) * 100
    else:
        present_increase = 0

    if absent_count_yesterday > 0:
        absent_increase = ((absent_count - absent_count_yesterday) / absent_count_yesterday) * 100
    else:
        absent_increase = 0

    # Render the template with real-time data
    return render_template('teacher/teacher_dashboard.html',
                           present_count=present_count,
                           absent_count=absent_count,
                           present_increase=present_increase,
                           absent_increase=absent_increase,
                           )

    
@app.route('/teacher/add_course', methods=['GET', 'POST'])
def add_course():
    if request.method == 'POST':
        # Check if teacher_id is in session
        teacher_id = session.get('teacher_id')
        if not teacher_id:
            flash('Please log in first.', 'error')
            return redirect(url_for('login'))

        # Retrieve form data
        name = request.form['name']
        year = request.form['year']
        branch = request.form['branch']
        section = request.form['section']
        slot = request.form['slot']
        days = request.form['days']  # Single day selected
        semester = request.form['semester']  # New semester field
        type = request.form['type']
        classroom_lab_id = request.form['classroom_lab_id']
        date = request.form['date']

        # Try to insert the data into the database
        try:
            cursor = mysql.connection.cursor()
            cursor.execute("""
                INSERT INTO courses (name, year, branch, section, slot, days, semester, type, classroom_lab_id, date, teacher_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (name, year, branch, section, slot, days, semester, type, classroom_lab_id, date, teacher_id))
            mysql.connection.commit()
            flash('Course added successfully!', 'success')
            return redirect(url_for('teacher_profile', teacher_id=teacher_id))
        except Exception as e:
            flash(f"An error occurred: {str(e)}", 'danger')
            return redirect(url_for('add_course'))
        finally:
            cursor.close()

    return render_template('teacher/add_course.html')

@app.route('/teacher/edit_course/<int:course_id>', methods=['GET', 'POST'])
def edit_course(course_id):
    # Check if teacher_id is in session
    teacher_id = session.get('teacher_id')
    if not teacher_id:
        flash('Please log in first.', 'error')
        return redirect(url_for('login'))

    # Get the course details from the database
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM courses WHERE id = %s AND teacher_id = %s", (course_id, teacher_id))
    course = cursor.fetchone()

    if course is None:
        flash('Course not found or you do not have permission to edit this course.', 'danger')
        return redirect(url_for('teacher_profile', teacher_id=teacher_id))

    if request.method == 'POST':
        # Retrieve form data
        name = request.form['name']
        year = request.form['year']
        branch = request.form['branch']
        section = request.form['section']
        slot = request.form['slot']
        days = request.form['days']  # Single day selected
        semester = request.form['semester']
        type = request.form['type']
        classroom_lab_id = request.form['classroom_lab_id']
        date = request.form['date']

        # Try to update the data in the database
        try:
            cursor.execute("""
                UPDATE courses 
                SET name = %s, year = %s, branch = %s, section = %s, slot = %s, 
                    days = %s, semester = %s, type = %s, classroom_lab_id = %s, date = %s
                WHERE id = %s AND teacher_id = %s
            """, (name, year, branch, section, slot, days, semester, type, classroom_lab_id, date, course_id, teacher_id))
            mysql.connection.commit()
            flash('Course updated successfully!', 'success')
            return redirect(url_for('teacher_profile', teacher_id=teacher_id))
        except Exception as e:
            flash(f"An error occurred: {str(e)}", 'danger')
            return redirect(url_for('edit_course', course_id=course_id))
        finally:
            cursor.close()

    # Render the edit course template with the course data
    return render_template('teacher/edit_course.html', course=course)

@app.route('/teacher/take_attendance/<int:course_id>', methods=['GET', 'POST'])
def teacher_take_attendance(course_id):
    if 'teacher_id' not in session:
        return redirect(url_for('teacher_login'))

    cursor = mysql.connection.cursor()

    # Fetch course details
    cursor.execute(
        'SELECT id, name, days, slot, branch, year, section FROM courses WHERE id = %s', (course_id,)
    )
    course = cursor.fetchone()

    if not course:
        flash('Course not found.', 'danger')
        return redirect(url_for('teacher_dashboard'))

    if request.method == 'POST':
        date = request.form['date']
        selected_day = datetime.strptime(date, '%Y-%m-%d').strftime('%A')

        # Validate the selected date matches the course day
        if selected_day.lower() not in course['days'].lower():
            flash(f'Error: Attendance can only be taken on the specified days: {course["days"]}.', 'danger')
            return redirect(url_for('teacher_take_attendance', course_id=course_id))

        # Check for duplicate attendance
        cursor.execute(
            'SELECT COUNT(*) AS count FROM attendance WHERE course_id = %s AND date = %s',
            (course_id, date)
        )
        result = cursor.fetchone()
        if result['count'] > 0:
            flash(f'Error: Attendance for {date} has already been recorded.', 'warning')
            return redirect(url_for('teacher_take_attendance', course_id=course_id))

        submit_type = request.form['submit_type']
        is_draft = submit_type == 'draft'
        students_present = request.form.getlist('students_present')

        # Insert attendance data
        cursor.execute('SELECT student_id FROM enrollments WHERE course_id = %s', (course_id,))
        all_students = cursor.fetchall()

        for student in all_students:
            cursor.execute(
                '''
                INSERT INTO attendance (course_id, student_id, date, present, is_draft)
                VALUES (%s, %s, %s, %s, %s)
                ''',
                (course_id, student['student_id'], date, False, is_draft)
            )

        # Update attendance for present students
        for student_id in students_present:
            cursor.execute(
                '''
                UPDATE attendance
                SET present = %s, is_draft = %s
                WHERE course_id = %s AND student_id = %s AND date = %s
                ''',
                (True, is_draft, course_id, student_id, date)
            )

        mysql.connection.commit()
        cursor.close()

        message = 'Attendance has been saved as a draft.' if is_draft else 'Attendance recorded successfully!'
        flash(message, 'info' if is_draft else 'success')
        return redirect(url_for('teacher_dashboard'))

    # Fetch students and course details for GET request
    cursor.execute(
        '''
        SELECT id, first_name, last_name, roll_no, photo
        FROM students
        WHERE id IN (SELECT student_id FROM enrollments WHERE course_id = %s)
        ''',
        (course_id,)
    )
    students = cursor.fetchall()
    cursor.close()

    return render_template(
        'teacher/teacher_take_attendance.html',
        students=students,
        course_id=course_id,
        course_name=course['name'],
        course_day=course['days'],
        course_time=course['slot'],
        course_branch=course['branch'],
        course_year=course['year'],
        course_section=course['section']
    )





@app.route('/teacher/update_attendance/<int:course_id>/<date>', methods=['GET', 'POST'])
def teacher_update_attendance(course_id, date):
    if 'teacher_id' not in session:
        return redirect(url_for('teacher_login'))

    cursor = mysql.connection.cursor()

    if request.method == 'POST':
        date = request.form['date']
        students_present = request.form.getlist('students_present')

        # Update attendance for the given date
        cursor.execute('SELECT student_id FROM attendance WHERE course_id = %s AND date = %s', (course_id, date))
        all_students = cursor.fetchall()

        # Mark all students as absent first
        for student in all_students:
            cursor.execute('UPDATE attendance SET present = %s WHERE course_id = %s AND student_id = %s AND date = %s', (False, course_id, student['student_id'], date))

        # Mark selected students as present
        for student_id in students_present:
            cursor.execute('UPDATE attendance SET present = %s WHERE course_id = %s AND student_id = %s AND date = %s', (True, course_id, student_id, date))

        mysql.connection.commit()
        cursor.close()
        flash('Attendance updated successfully!', 'success')
        return redirect(url_for('teacher_dashboard'))

    cursor.execute('''
        SELECT students.id, students.first_name,students.last_name, students.roll_no, students.photo, 
        IFNULL(attendance.present, False) AS present
        FROM students
        LEFT JOIN attendance ON students.id = attendance.student_id 
        AND attendance.course_id = %s AND attendance.date = %s
        WHERE students.id IN (SELECT student_id FROM enrollments WHERE course_id = %s)
    ''', (course_id, date, course_id))
    students = cursor.fetchall()

    cursor.close()
    return render_template('teacher/update_attendance.html', students=students, course_id=course_id, date=date)

@app.route('/teacher/view_attendance/<int:course_id>', methods=['GET', 'POST'])
def view_attendance(course_id):
    if 'teacher_id' not in session:
        return redirect(url_for('teacher_login'))

    cursor = mysql.connection.cursor()

    cursor.execute(
        'SELECT id, name, days, slot, branch, year, section FROM courses WHERE id = %s', (course_id,)
    )
    course = cursor.fetchone()

    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        branch = request.form.get('branch')
        section = request.form.get('section')

        # Log the form inputs for debugging
        print(f"Start Date: {start_date}, End Date: {end_date}, Branch: {branch}, Section: {section}")

        # Prepare query to filter attendance and get first_name, last_name
        query = '''
            SELECT students.first_name, students.last_name, students.roll_no, students.branch, students.section, 
                   attendance.date, attendance.present 
            FROM attendance 
            JOIN students ON attendance.student_id = students.id 
            WHERE attendance.course_id = %s AND attendance.date BETWEEN %s AND %s
        '''
        params = [course_id, start_date, end_date]

        if branch != 'All':
            query += ' AND students.branch = %s'
            params.append(branch)

        if section != 'All':
            query += ' AND students.section = %s'
            params.append(section)

        query += ' ORDER BY attendance.date'

        cursor.execute(query, tuple(params))
        attendance_records = cursor.fetchall()

        # Group attendance by date and calculate attendance percentage
        grouped_attendance = {}
        student_attendance = {}

        for record in attendance_records:
            date = record['date'].strftime('%Y-%m-%d')
            if date not in grouped_attendance:
                grouped_attendance[date] = []
            grouped_attendance[date].append(record)

            # Track individual student attendance for percentage calculation
            student = record['roll_no']
            if student not in student_attendance:
                student_attendance[student] = {'total': 0, 'present': 0}
            student_attendance[student]['total'] += 1
            if record['present']:
                student_attendance[student]['present'] += 1

        # Calculate attendance percentages per student
        attendance_percentages = {}
        for student, attendance in student_attendance.items():
            total = attendance['total']
            present = attendance['present']
            percentage = (present / total) * 100 if total > 0 else 0
            attendance_percentages[student] = round(percentage, 2)

        cursor.close()
        return render_template('teacher/teacher_view_attendance_page.html', 
                               grouped_attendance=grouped_attendance, 
                               course_id=course_id, 
                               attendance_percentages=attendance_percentages)

    # Fetch distinct branches and sections for filter options
    cursor.execute('SELECT DISTINCT branch FROM students')
    branches = cursor.fetchall()

    cursor.execute('SELECT DISTINCT section FROM students')
    sections = cursor.fetchall()

    cursor.close()
    return render_template('teacher/teacher_view_attendance_page.html', 
                           course_id=course_id, 
                           branches=branches, 
                           sections=sections,
                           course_name=course['name'],
                           course_day=course['days'],
                           course_time=course['slot'],
                           course_branch=course['branch'],
                           course_year=course['year'],
                           course_section=course['section'] 
                           )


   
@app.route('/teacher/notify_students/<int:course_id>', methods=['GET'])
def notify_students(course_id):
    if 'teacher_id' not in session:
        return redirect(url_for('teacher_login'))

    # Get filters from the query string
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    branch = request.args.get('branch')
    section = request.args.get('section')

    cursor = mysql.connection.cursor()

    # Prepare query to filter attendance
    query = '''
        SELECT students.name, students.email, students.roll_no, COUNT(attendance.id) AS total_lectures, 
               SUM(attendance.present) AS attended 
        FROM attendance 
        JOIN students ON attendance.student_id = students.id 
        WHERE attendance.course_id = %s AND attendance.date BETWEEN %s AND %s
    '''
    params = [course_id, start_date, end_date]

    if branch != 'All':
        query += ' AND students.branch = %s'
        params.append(branch)

    if section != 'All':
        query += ' AND students.section = %s'
        params.append(section)

    query += ' GROUP BY students.id'

    cursor.execute(query, tuple(params))
    attendance_data = cursor.fetchall()

    # Send email to students with less than 75% attendance
    sender_email = "mohitkoli9888@gmail.com"
    sender_password = "chch npag xuzl oosd"

    smtp_server = smtplib.SMTP('smtp.gmail.com', 587)
    smtp_server.starttls()
    smtp_server.login(sender_email, sender_password)

    for record in attendance_data:
        name = record['name']
        email = record['email']
        total_lectures = record['total_lectures']
        attended = record['attended']
        attendance_percentage = (attended / total_lectures) * 100 if total_lectures > 0 else 0

        if attendance_percentage < 75:
            # Prepare email
            subject = "Low Attendance Alert"
            body = f"""
            Dear {name},

            Your attendance percentage for the selected period ({start_date} to {end_date}) is {attendance_percentage:.2f}%.

            Please note that this is below the required 75%. Kindly take necessary steps to improve your attendance.

            Best regards,
            Course Team
            """
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            smtp_server.sendmail(sender_email, email, msg.as_string())

    smtp_server.quit()
    cursor.close()

    return redirect(url_for('view_attendance', course_id=course_id))                        


@app.route('/teacher/view_all_attendance', methods=['GET', 'POST'])
def view_all_attendance():
    if 'teacher_id' not in session:
        return redirect(url_for('teacher_login'))

    cursor = mysql.connection.cursor()

    if request.method == 'POST':
        year = request.form.get('year')
        branch = request.form.get('branch')
        slot = request.form.get('slot')
        section = request.form.get('section')
        start_date = request.form.get('start_date', None)
        end_date = request.form.get('end_date', None)

        query = """
            SELECT a.date, c.name as course_name, s.roll_no, s.name as student_name, a.present
            FROM attendance a
            JOIN courses c ON a.course_id = c.id
            JOIN students s ON a.student_id = s.id
            WHERE 1 = 1
        """
        params = []

        if year != 'ALL':
            query += " AND s.year = %s"
            params.append(year)
        if branch != 'ALL':
            query += " AND s.branch = %s"
            params.append(branch)
        if slot != 'ALL':
            query += " AND c.slot = %s"
            params.append(slot)
        if section != 'ALL':
            query += " AND s.section = %s"
            params.append(section)
        if start_date and end_date:
            query += " AND a.date BETWEEN %s AND %s"
            params.append(start_date)
            params.append(end_date)

        cursor.execute(query, tuple(params))
        attendance_data = cursor.fetchall()

        cursor.close()

        if 'download' in request.form:
            return download_attendance(attendance_data)

        return render_template('teacher/view_attendance_records.html', attendance_data=attendance_data)

    return render_template('teacher/view_attendance_records.html', attendance_data=None)



@app.route('/teacher/add_student_to_course/<int:course_id>', methods=['GET', 'POST'])
def add_student_to_course(course_id):
    cursor = mysql.connection.cursor()
    
    if request.method == 'POST':
        student_ids = request.form.getlist('student_ids')
        action = request.form['action']

        if student_ids:
            if action == 'add':
                # Add each selected student to the course
                for student_id in student_ids:
                    cursor.execute("INSERT IGNORE INTO enrollments (student_id, course_id) VALUES (%s, %s)", (student_id, course_id))
                flash(f'{len(student_ids)} student(s) added to the course successfully!', 'success')

        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('add_student_to_course', course_id=course_id))

    # Handling GET request (searching students)
    query = request.args.get('query', '')
    section = request.args.get('section', '')
    year = request.args.get('year', '')
    branch = request.args.get('branch', '')
    
    students = []
    if query or section or year or branch:
        sql_query = "SELECT id, first_name, last_name, roll_no, photo FROM students WHERE 1=1"
        sql_params = []

        # Search by name or roll number
        if query:
            sql_query += " AND (first_name LIKE %s OR last_name LIKE %s OR roll_no LIKE %s)"
            sql_params.extend([f"%{query}%", f"%{query}%", f"%{query}%"])

        # Filter by section
        if section:
            sql_query += " AND section = %s"
            sql_params.append(section)

        # Filter by year
        if year:
            sql_query += " AND year = %s"
            sql_params.append(year)

        # Filter by branch
        if branch:
            sql_query += " AND branch = %s"
            sql_params.append(branch)

        cursor.execute(sql_query, sql_params)
        students = cursor.fetchall()

        # Check enrollment status for each student
        for student in students:
            cursor.execute("SELECT * FROM enrollments WHERE student_id = %s AND course_id = %s", (student['id'], course_id))
            student['enrolled'] = cursor.fetchone() is not None

    cursor.close()
    return render_template('teacher/add_student_to_course.html', 
                           students=students, 
                           course_id=course_id, 
                           query=query, 
                           section=section, 
                           year=year, 
                           branch=branch)

@app.route('/teacher/view_students/<int:course_id>', methods=['GET', 'POST'])
def view_students(course_id):
    cursor = mysql.connection.cursor()

    # Fetch course details
    cursor.execute('SELECT * FROM courses WHERE id = %s', (course_id,))
    course = cursor.fetchone()

    # Fetch students enrolled in the course, including first_name and last_name
    cursor.execute("""
        SELECT s.id, s.first_name, s.last_name, s.roll_no, s.branch, s.year, s.section, s.photo
        FROM students s
        JOIN enrollments e ON s.id = e.student_id
        WHERE e.course_id = %s
    """, (course_id,))
    students = cursor.fetchall()

    cursor.close()

    return render_template('teacher/view_students.html', course=course, students=students)




@app.route('/delete_course/<int:course_id>')
def delete_course(course_id):
    if 'teacher_id' not in session:
        flash('You need to be logged in to access this page.', 'danger')
        return redirect(url_for('teacher_login'))

    cursor = mysql.connection.cursor()
    cursor.execute('DELETE FROM courses WHERE id = %s', (course_id,))
    mysql.connection.commit()
    cursor.close()

    flash('Course deleted successfully!', 'success')
    return redirect(url_for('teacher_profile'))


@app.route('/teacher/remove_student_from_course/<int:course_id>/<int:student_id>', methods=['POST'])
def remove_student_from_course(course_id, student_id):
    cursor = mysql.connection.cursor()
    
    # Remove the student from the enrollments table for the specific course
    cursor.execute('DELETE FROM enrollments WHERE student_id = %s AND course_id = %s', (student_id, course_id))
    mysql.connection.commit()

    cursor.close()
    
    flash('Student successfully removed from the course.', 'success')
    
    # Redirect back to the view_students page
    return redirect(url_for('view_students', course_id=course_id))
@app.route('/teacher/view_requests')
def view_requests():
    teacher_id = session.get('teacher_id')
    if not teacher_id:
        flash('You must be logged in as a teacher to view requests.', 'danger')
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute('''
        SELECT notifications.id, students.first_name, students.last_name, students.roll_no,
               notifications.message, notifications.sent_at, courses.name AS course_name, courses.id AS course_id
        FROM notifications
        JOIN students ON notifications.student_id = students.id
        JOIN courses ON notifications.course_id = courses.id
        WHERE notifications.teacher_id = %s
    ''', (teacher_id,))
    requests = cur.fetchall()

    # Update the course_requests field with the count of pending requests
    request_count = len(requests)
    cur.execute('''
        UPDATE teachers
        SET course_requests = %s
        WHERE id = %s
    ''', (f'{request_count} pending requests', teacher_id))

    mysql.connection.commit()
    cur.close()

    return render_template('teacher/view_requests.html', requests=requests)

@app.route('/teacher/handle_request/<int:request_id>/<action>', methods=['POST'])
def handle_request(request_id, action):
    teacher_id = session.get('teacher_id')
    if not teacher_id:
        flash('You must be logged in as a teacher to handle requests.', 'danger')
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()

    # Fetch student_id and course_id based on the notification
    cur.execute('''
        SELECT notifications.student_id, notifications.course_id, courses.name AS course_name
        FROM notifications
        JOIN courses ON notifications.course_id = courses.id
        WHERE notifications.id = %s
    ''', (request_id,))
    result = cur.fetchone()

    if result:
        if action == 'approve':
            # Approve request by enrolling the student in the specific course
            cur.execute('''
                INSERT INTO enrollments (student_id, course_id) VALUES (%s, %s)
            ''', (result['student_id'], result['course_id']))
            flash(f'Enrollment request for {result["course_name"]} approved.', 'success')
        elif action == 'reject':
            flash(f'Enrollment request for {result["course_name"]} rejected.', 'danger')

        # Delete the notification after handling
        cur.execute('DELETE FROM notifications WHERE id = %s', (request_id,))

        # Update the course_requests field with the new pending request count
        cur.execute('''
            SELECT COUNT(*) AS pending_requests
            FROM notifications
            WHERE teacher_id = %s
        ''', (teacher_id,))
        pending_requests = cur.fetchone()['pending_requests']

        cur.execute('''
            UPDATE teachers
            SET course_requests = %s
            WHERE id = %s
        ''', (f'{pending_requests} pending requests', teacher_id))

        mysql.connection.commit()

    cur.close()

    return redirect(url_for('view_requests'))



def calculate_attendance_percentage(student_id, course_id):
    cursor = mysql.connection.cursor()

    # Total classes for the course
    cursor.execute("SELECT COUNT(*) AS total_classes FROM attendance WHERE course_id = %s", (course_id,))
    total_classes = cursor.fetchone()['total_classes']

    # Classes attended by the student
    cursor.execute("""
        SELECT COUNT(*) AS classes_attended 
        FROM attendance 
        WHERE course_id = %s AND student_id = %s AND present = TRUE
    """, (course_id, student_id))
    classes_attended = cursor.fetchone()['classes_attended']

    cursor.close()

    if total_classes == 0:
        return 0

    return (classes_attended / total_classes) * 100



@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        roll_no = request.form['roll_no']
        password = request.form['password']
        
        # Check if roll_no exists in the database
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM students WHERE roll_no = %s', (roll_no,))
        student = cursor.fetchone()
        cursor.close()

        # If student exists, check the password
        if student and check_password_hash(student['password'], password):
            # Store first name, middle name, and last name in session
            session['student_id'] = student['id']
            session['first_name'] = student['first_name']
            session['middle_name'] = student['middle_name']  # Assuming the database has a 'middle_name' field
            session['last_name'] = student['last_name']
            session['student_photo'] = student['photo'] if student['photo'] else 'nophoto.jpg'

            # Redirect to student profile if login is successful
            return redirect(url_for('student_profile'))
        else:
            # Flash error message if credentials are incorrect
            flash('Invalid roll number or password.', 'danger')
            return redirect(url_for('student_login'))

    # Render the login page if method is GET
    return render_template('student/student_login.html')


@app.route('/student/signup', methods=['GET', 'POST'])
def student_signup():
    if request.method == 'POST':
        roll_no = request.form['roll_no']
        first_name = request.form['first_name']
        middle_name = request.form['middle_name']
        last_name = request.form['last_name']
        email = request.form['email']
        section = request.form['section']
        year = int(request.form['year'])
        branch = request.form['branch']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        photo = request.files['photo'] if 'photo' in request.files else None

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('student_signup'))

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM students WHERE roll_no = %s', (roll_no,))
        existing_student = cursor.fetchone()

        if existing_student:
            flash('Roll number already exists.', 'danger')
            return redirect(url_for('student_signup'))

        if photo and allowed_file(photo.filename):
            photo_filename = secure_filename(photo.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], photo_filename)
            app.logger.info(f"Saving file to {save_path}")
            photo.save(save_path)
        else:
            photo_filename = 'nophoto.jpg'  # Default image filename if no photo is uploaded

        cursor.execute('INSERT INTO students (roll_no, first_name, middle_name, last_name, email, section, year, branch, password, photo) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                       (roll_no, first_name, middle_name, last_name, email, section, year, branch, generate_password_hash(password), photo_filename))
        mysql.connection.commit()
        cursor.close()

        flash('Signup successful. Please login.', 'success')
        return redirect(url_for('student_login'))

    return render_template('student/student_signup.html')

@app.route('/student/profile')
def student_profile():
    student_id = session.get('student_id')
    
    if not student_id:
        flash('You need to log in first.', 'danger')
        return redirect(url_for('student_login'))
    
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM students WHERE id = %s', (student_id,))
    student = cursor.fetchone()
    cursor.close()

    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('student_login'))

    # Ensure session variables are set correctly
    session['student_photo'] = student['photo'] if student['photo'] else 'nophoto.jpg'
    session['student_first_name'] = student['first_name']
    session['student_middle_name'] = student.get('middle_name', '')  # Middle name can be None
    session['student_last_name'] = student['last_name']

    return render_template('student/student_profile.html', student=student)


@app.route('/student/profile/edit', methods=['GET', 'POST'])
def student_edit_profile():
    student_id = session.get('student_id')
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM students WHERE id = %s', (student_id,))
    student = cursor.fetchone()

    if request.method == 'POST':
        first_name = request.form['first_name']
        middle_name = request.form.get('middle_name', '')  # Optional field
        last_name = request.form['last_name']
        roll_no = request.form['roll_no']
        email = request.form['email']
        contact = request.form['contact']
        photo = request.files['photo'] if 'photo' in request.files else None
        remove_photo = 'remove_photo' in request.form

        if remove_photo:
            photo_filename = 'nophoto.jpg'
            cursor.execute('UPDATE students SET first_name = %s, middle_name = %s, last_name = %s, roll_no = %s, email = %s, contact = %s, photo = %s WHERE id = %s',
                           (first_name, middle_name, last_name, roll_no, email, contact, photo_filename, student_id))
            session['student_photo'] = photo_filename
        elif photo and allowed_file(photo.filename):
            photo_filename = secure_filename(photo.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], photo_filename)
            photo.save(save_path)
            cursor.execute('UPDATE students SET first_name = %s, middle_name = %s, last_name = %s, roll_no = %s, email = %s, contact = %s, photo = %s WHERE id = %s',
                           (first_name, middle_name, last_name, roll_no, email, contact, photo_filename, student_id))
            session['student_photo'] = photo_filename
        else:
            cursor.execute('UPDATE students SET first_name = %s, middle_name = %s, last_name = %s, roll_no = %s, email = %s, contact = %s WHERE id = %s',
                           (first_name, middle_name, last_name, roll_no, email, contact, student_id))

        mysql.connection.commit()
        cursor.close()

        flash('Profile updated successfully.', 'success')
        return redirect(url_for('student_profile'))

    return render_template('student/student_edit_profile.html', student=student)

# Student dashboard
# @app.route('/student/dashboard')
# def student_dashboard():
#     student_id = session.get('student_id')
#     if not student_id:
#         flash('You need to be logged in to access this page.', 'danger')
#         return redirect(url_for('student_login'))

#     cursor = mysql.connection.cursor()
#     # Get student details
#     cursor.execute('SELECT * FROM students WHERE id = %s', (student_id,))
#     student = cursor.fetchone()

#     # Get enrolled courses
#     cursor.execute('''
#         SELECT c.id, c.name
#         FROM courses c
#         JOIN enrollments e ON c.id = e.course_id
#         WHERE e.student_id = %s
#     ''', (student_id,))
#     enrolled_courses = cursor.fetchall()

#     # Get student's attendance percentage for each course
#     cursor.execute('''
#         SELECT c.id, c.name, 
#         (SELECT COUNT(*) FROM attendance a WHERE a.course_id = c.id AND a.student_id = %s AND a.present = TRUE) / 
#         (SELECT COUNT(*) FROM attendance a WHERE a.course_id = c.id AND a.student_id = %s) * 100 
#         AS attendance_percentage
#         FROM courses c
#         JOIN enrollments e ON c.id = e.course_id
#         WHERE e.student_id = %s
#     ''', (student_id, student_id, student_id))
#     attendance = cursor.fetchall()

#     # Check for low attendance notifications
#     attendance_notifications = [
#         f"Your attendance for {course['name']} is below 75%." for course in attendance if course['attendance_percentage'] < 75
#     ]

#     return render_template('student/student_dashboard.html', student=student, enrolled_courses=enrolled_courses, attendance_notifications=attendance_notifications)

# # View attendance (ask date)
# @app.route('/student/view_attendance/ask_date')
# def view_attendance_ask_date():
#     student_id = session.get('student_id')
#     if not student_id:
#         flash('You need to be logged in to access this page.', 'danger')
#         return redirect(url_for('student_login'))

#     cursor = mysql.connection.cursor()
#     # Get enrolled courses
#     cursor.execute('''
#         SELECT c.id, c.name
#         FROM courses c
#         JOIN enrollments e ON c.id = e.course_id
#         WHERE e.student_id = %s
#     ''', (student_id,))
#     courses = cursor.fetchall()

#     return render_template('student/student_view_attendance_ask_date.html', courses=courses)

# # View attendance records
# @app.route('/student/view_attendance', methods=['GET'])
# def view_attendance2():
#     student_id = session.get('student_id')
#     if not student_id:
#         flash('You need to be logged in to access this page.', 'danger')
#         return redirect(url_for('student_login'))

#     date = request.args.get('date')
#     course_id = request.args.get('course_id')

#     cursor = mysql.connection.cursor()
#     # Get course name
#     cursor.execute('SELECT name FROM courses WHERE id = %s', (course_id,))
#     course = cursor.fetchone()
#     course_name = course['name']

#     # Get attendance records for the specified date and course
#     cursor.execute('''
#         SELECT s.name AS student_name, a.present
#         FROM attendance a
#         JOIN students s ON a.student_id = s.id
#         WHERE a.course_id = %s AND a.date = %s
#     ''', (course_id, date))
#     attendance_records = cursor.fetchall()

#     return render_template('student/student_view_attendance_page.html', course_name=course_name, date=date, attendance_records=attendance_records)

# Join a course
@app.route('/student/join_course/<int:course_id>')
def join_course(course_id):
    student_id = session.get('student_id')
    if not student_id:
        flash('You need to be logged in to join a course.', 'danger')
        return redirect(url_for('student_login'))

    cursor = mysql.connection.cursor()
    # Check if the student is already enrolled in the course
    cursor.execute('SELECT * FROM enrollments WHERE student_id = %s AND course_id = %s', (student_id, course_id))
    enrollment = cursor.fetchone()

    if not enrollment:
        # Enroll student in the course
        cursor.execute('INSERT INTO enrollments (student_id, course_id) VALUES (%s, %s)', (student_id, course_id))
        mysql.connection.commit()
        flash('Successfully joined the course.', 'success')
    else:
        flash('You are already enrolled in this course.', 'info')

    return redirect(url_for('student_profile'))


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('home'))


@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '').strip()
    cursor = mysql.connection.cursor()

    # Search in students table
    cursor.execute(
        """
        SELECT * 
        FROM students 
        WHERE first_name LIKE %s 
           OR last_name LIKE %s 
           OR email LIKE %s
        """,
        (f"%{query}%", f"%{query}%", f"%{query}%")
    )
    students = cursor.fetchall()

    # Search in teachers table
    # Search in teachers table
    cursor.execute("SELECT id, name, short_name, email, profile_photo FROM teachers WHERE name LIKE %s OR email LIKE %s", (f"%{query}%", f"%{query}%"))


    teachers = cursor.fetchall()

    return render_template('common/search_results.html', students=students, teachers=teachers, query=query)



@app.route('/student/apply_absence', methods=['GET', 'POST'])
def apply_absence():
    if request.method == 'POST':
        student_id = session.get('student_id')  # Assuming student is logged in
        teacher_id = request.form['teacher_id']
        date_of_application = request.form['date_of_application']
        number_of_days = request.form['number_of_days']
        reason = request.form['reason']

        # Insert into database
        cur = mysql.connection.cursor()
        cur.execute('''
            INSERT INTO absence_applications (student_id, teacher_id, date_of_application, number_of_days, reason)
            VALUES (%s, %s, %s, %s, %s)
        ''', (student_id, teacher_id, date_of_application, number_of_days, reason))
        mysql.connection.commit()
        cur.close()

        flash('Application submitted successfully!')
        return redirect(url_for('apply_absence'))

    # Fetch teachers
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM teachers")
    teachers = cur.fetchall()
    cur.close()

    return render_template('student/apply_absence.html', teachers=teachers)

@app.route('/student/view_application_status')
def view_application_status():
    student_id = session.get('student_id')  # Assuming student is logged in
    cur = mysql.connection.cursor()
    cur.execute('''
        SELECT absence_applications.*, teachers.name AS teacher_name
        FROM absence_applications
        JOIN teachers ON absence_applications.teacher_id = teachers.id
        WHERE absence_applications.student_id = %s
    ''', (student_id,))
    applications = cur.fetchall()
    cur.close()

    return render_template('student/view_application_status.html', applications=applications)

@app.route('/teacher/view_student_applications')
def view_student_applications():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT aa.id, s.first_name, s.last_name, aa.date_of_application, 
               aa.number_of_days, aa.reason, aa.status
        FROM absence_applications aa
        JOIN students s ON aa.student_id = s.id
    """)
    applications = cur.fetchall()
    cur.close()
    return render_template('teacher/view_student_applications.html', applications=applications)


@app.route('/teacher/approve_application/<int:application_id>')
def approve_application(application_id):
    cur = mysql.connection.cursor()
    cur.execute('UPDATE absence_applications SET status = "Approved" WHERE id = %s', (application_id,))
    mysql.connection.commit()
    cur.close()
    flash('Application approved!')
    return redirect(url_for('view_student_applications'))

@app.route('/teacher/reject_application/<int:application_id>')
def reject_application(application_id):
    cur = mysql.connection.cursor()
    cur.execute('UPDATE absence_applications SET status = "Rejected" WHERE id = %s', (application_id,))
    mysql.connection.commit()
    cur.close()
    flash('Application rejected!')
    return redirect(url_for('view_student_applications'))

# Route to update the status of an application
@app.route('/teacher/update_application_status/<int:application_id>', methods=['POST'])
def update_application_status(application_id):
    # Get the selected status from the form (Approve/Reject)
    new_status = request.form.get('status')
    
    # Update the application status in the database
    cur = mysql.connection.cursor()
    cur.execute('UPDATE absence_applications SET status = %s WHERE id = %s', (new_status, application_id))
    mysql.connection.commit()
    cur.close()

    # Flash a message to inform the teacher
    if new_status == "Approved":
        flash('Application approved successfully!', 'success')
    elif new_status == "Rejected":
        flash('Application rejected successfully!', 'danger')

    # Redirect back to the view student applications page
    return redirect(url_for('view_student_applications'))

@app.route('/student/courses', methods=['GET', 'POST'])
def student_courses():
    student_id = session.get('student_id')  # Assuming student is logged in
    if not student_id:
        flash('You must be logged in to view courses.', 'danger')
        return redirect(url_for('login'))

    branch = request.args.get('branch')
    year = request.args.get('year')
    section = request.args.get('section')

    # Query to filter courses based on branch, year, and section
    query = '''
        SELECT courses.*, teachers.name AS teacher_name
        FROM courses
        JOIN teachers ON courses.teacher_id = teachers.id
        WHERE 1 = 1
    '''
    filters = []
    if branch:
        query += ' AND branch = %s'
        filters.append(branch)
    if year:
        query += ' AND year = %s'
        filters.append(year)
    if section:
        query += ' AND section = %s'
        filters.append(section)

    cur = mysql.connection.cursor()
    cur.execute(query, filters)
    available_courses = cur.fetchall()

    # Fetch enrolled courses for the student
    cur.execute('''
        SELECT course_id FROM enrollments WHERE student_id = %s
    ''', (student_id,))
    enrolled_courses = [row['course_id'] for row in cur.fetchall()]

    # Fetch requested courses for the student
    cur.execute('''
        SELECT course_id FROM notifications WHERE student_id = %s
    ''', (student_id,))
    requested_courses = [row['course_id'] for row in cur.fetchall()]

    cur.close()

    return render_template('student/courses.html', available_courses=available_courses,
                           enrolled_courses=enrolled_courses, requested_courses=requested_courses)

@app.route('/student/request_enroll_course/<int:course_id>', methods=['POST'])
def request_enroll_course(course_id):
    student_id = session.get('student_id')
    if not student_id:
        flash('You must be logged in to request enrollment.', 'danger')
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()

    # Fetch course and teacher info for the course being requested
    cur.execute('''
        SELECT teacher_id, name FROM courses WHERE id = %s
    ''', (course_id,))
    course = cur.fetchone()

    if not course:
        flash('Course not found.', 'danger')
        cur.close()
        return redirect(url_for('student_courses'))

    teacher_id = course['teacher_id']
    course_name = course['name']

    # Check if the student has already requested this course
    cur.execute('''
        SELECT 1 FROM notifications WHERE student_id = %s AND course_id = %s
    ''', (student_id, course_id))
    if cur.fetchone():
        flash('You have already requested to join this course.', 'info')
        cur.close()
        return redirect(url_for('student_courses'))

    # Insert the request into the notifications table
    message = f'Request to join your course: {course_name}'
    cur.execute('''
        INSERT INTO notifications (student_id, teacher_id, message, course_id)
        VALUES (%s, %s, %s, %s)
    ''', (student_id, teacher_id, message, course_id))

    # Update the course_requests field in the teachers table
    cur.execute('''
        SELECT COUNT(*) AS pending_requests
        FROM notifications
        WHERE teacher_id = %s
    ''', (teacher_id,))
    pending_requests = cur.fetchone()['pending_requests']

    cur.execute('''
        UPDATE teachers
        SET course_requests = %s
        WHERE id = %s
    ''', (f'{pending_requests} pending requests', teacher_id))

    mysql.connection.commit()
    cur.close()

    flash('Your request has been sent to the course teacher.', 'success')
    return redirect(url_for('student_courses'))



@app.route('/student/cancel_request/<int:course_id>', methods=['POST'])
def cancel_request_course(course_id):
    student_id = session.get('student_id')
    if not student_id:
        flash('You must be logged in to cancel a request.', 'danger')
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()

    # Fetch teacher_id for the selected course
    cur.execute('''
        SELECT teacher_id FROM courses WHERE id = %s
    ''', (course_id,))
    course = cur.fetchone()

    if not course:
        flash('Course not found.', 'danger')
        cur.close()
        return redirect(url_for('student_courses'))

    teacher_id = course['teacher_id']

    # Remove the request from the notifications table
    cur.execute('''
        DELETE FROM notifications WHERE student_id = %s AND course_id = %s
    ''', (student_id, course_id))

    # Update the course_requests field in the teachers table
    cur.execute('''
        SELECT COUNT(*) AS pending_requests
        FROM notifications
        WHERE teacher_id = %s
    ''', (teacher_id,))
    pending_requests = cur.fetchone()['pending_requests']

    cur.execute('''
        UPDATE teachers
        SET course_requests = %s
        WHERE id = %s
    ''', (f'{pending_requests} pending requests', teacher_id))

    mysql.connection.commit()
    cur.close()

    flash('Your request has been cancelled.', 'success')
    return redirect(url_for('student_courses'))




@app.route('/student/enroll/<int:course_id>', methods=['POST'])
def enroll_course(course_id):
    student_id = session.get('student_id')
    
    # Check if the student is already enrolled
    cur = mysql.connection.cursor()
    cur.execute('''
        SELECT * FROM enrollments WHERE student_id = %s AND course_id = %s
    ''', (student_id, course_id))
    
    if cur.fetchone() is None:
        # Enroll the student in the course
        cur.execute('''
            INSERT INTO enrollments (student_id, course_id) VALUES (%s, %s)
        ''', (student_id, course_id))
        mysql.connection.commit()
        flash('Successfully enrolled in the course!', 'success')
    else:
        flash('You are already enrolled in this course.', 'warning')

    cur.close()
    return redirect(url_for('student_courses'))

@app.route('/student/unenroll/<int:course_id>', methods=['POST'])
def unenroll_course(course_id):
    student_id = session.get('student_id')
    
    cur = mysql.connection.cursor()
    cur.execute('''
        DELETE FROM enrollments WHERE student_id = %s AND course_id = %s
    ''', (student_id, course_id))
    mysql.connection.commit()
    cur.close()

    flash('You have been unenrolled from the course.', 'success')
    return redirect(url_for('view_enrolled_courses'))

@app.route('/student/enrolled_courses')
def view_enrolled_courses():
    student_id = session.get('student_id')

    cur = mysql.connection.cursor()
    cur.execute('''
        SELECT DISTINCT courses.*, teachers.name AS teacher_name
        FROM enrollments
        JOIN courses ON enrollments.course_id = courses.id
        JOIN teachers ON courses.teacher_id = teachers.id
        WHERE enrollments.student_id = %s
    ''', (student_id,))
    enrolled_courses = cur.fetchall()
    cur.close()

    return render_template('student/enrolled_courses.html', enrolled_courses=enrolled_courses)


@app.route('/view/student/<int:student_id>')
def view_student_profile(student_id):
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM students WHERE id = %s', (student_id,))
    student = cursor.fetchone()
    cursor.close()

    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('home'))  # Redirect to home or a fallback page

    return render_template('student/view_student_profile.html', student=student)

@app.route('/view/teacher/<int:teacher_id>')
def view_teacher_profile(teacher_id):
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM teachers WHERE id = %s', (teacher_id,))
    teacher = cursor.fetchone()
    
    cursor.execute('SELECT * FROM courses WHERE teacher_id = %s', (teacher_id,))
    courses = cursor.fetchall()
    cursor.close()

    if not teacher:
        flash('Teacher not found.', 'danger')
        return redirect(url_for('home'))  # Redirect to home or a fallback page

    return render_template('teacher/view_teacher_profile.html', teacher=teacher, courses=courses)

@app.route('/admin/upload_students', methods=['GET', 'POST'])
def upload_students():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)

        file = request.files['file']

        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)

        # Save and read the Excel file
        if allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Process the Excel file using pandas
            try:
                import pandas as pd
                data = pd.read_excel(file_path)

                # Check if mandatory columns are present
                mandatory_columns = ['Roll No', 'First Name', 'Last Name', 'Password']
                if not all(col in data.columns for col in mandatory_columns):
                    flash(f'Excel file is missing mandatory columns: {mandatory_columns}', 'danger')
                    return redirect(request.url)

                # Set default values for optional columns if they are missing
                data['Branch'] = data.get('Branch', 'Unknown')  # Default to 'Unknown' if not provided
                data['Year'] = data.get('Year', 1)  # Default to 1st year if not provided
                data['Section'] = data.get('Section', 'A')  # Default section if not provided
                data['Email'] = data.get('Email', '')  # Optional, default to empty if not provided

                # Insert students into the database
                cursor = mysql.connection.cursor()
                total_students = len(data)
                added_students = 0
                skipped_students = 0

                for index, row in data.iterrows():
                    roll_no = row['Roll No']
                    first_name = row['First Name']
                    last_name = row['Last Name']
                    branch = row['Branch']
                    year = int(row['Year'])
                    email = row['Email']
                    section = row['Section']
                    password = row['Password']

                    # Check if student already exists
                    cursor.execute('SELECT * FROM students WHERE roll_no = %s', (roll_no,))
                    existing_student = cursor.fetchone()

                    if existing_student:
                        skipped_students += 1
                        flash(f"Student with Roll No {roll_no} already exists.", 'warning')
                        continue

                    # Insert the student into the database
                    cursor.execute(
                        'INSERT INTO students (roll_no, first_name, last_name, email, branch, year, section, password) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
                        (roll_no, first_name, last_name, email, branch, year, section, generate_password_hash(password))
                    )
                    added_students += 1

                mysql.connection.commit()
                cursor.close()

                flash(f'Students registered successfully: {added_students}/{total_students} added, {skipped_students} skipped.', 'success')
            except Exception as e:
                mysql.connection.rollback()  # Rollback on error
                flash(f"Error processing file: {str(e)}", 'danger')

        else:
            flash('Invalid file type. Only Excel files are allowed.', 'danger')
        
        return redirect(url_for('upload_students'))

    return render_template('admin/upload_students.html') 




# Admin Login Route

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM admins WHERE username = %s', [username])
        admin = cursor.fetchone()
        cursor.close()

        if admin and check_password_hash(admin['password'], password):
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password.')

    return render_template('admin/login.html')


@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))

    return render_template('admin/dashboard.html')

def setup_admin():
    with app.app_context():
        try:
            cursor = mysql.connection.cursor()
        except MySQLdb.OperationalError as e:
            mysql.connection.ping(True)
            cursor = mysql.connection.cursor()

        # Ensure table exists
        cursor.execute('CREATE TABLE IF NOT EXISTS admins (id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(255) UNIQUE NOT NULL, password VARCHAR(255) NOT NULL)')
        
        # Check if admin already exists
        cursor.execute('SELECT * FROM admins WHERE username = %s', ['admin'])
        admin = cursor.fetchone()

        if not admin:
            hashed_password = generate_password_hash('admin', method='pbkdf2:sha256')
            cursor.execute('INSERT INTO admins (username, password) VALUES (%s, %s)', ('admin', hashed_password))
            mysql.connection.commit()
        
        cursor.close()

# Setup admin
with app.app_context():
    setup_admin()
@app.route('/admin/generate_report', methods=['GET', 'POST'])
def generate_report():
    if request.method == 'POST':
        year = request.form.get('year') if request.form.get('year') else None
        branch = request.form.get('branch') if request.form.get('branch') else None
        semester = request.form.get('semester') if request.form.get('semester') else None
        date = request.form.get('date') if request.form.get('date') else None

        if not date:
            flash("Please select a date.", "warning")
            return redirect(url_for('generate_report'))

        # Convert date to day of the week
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        day_of_week = date_obj.strftime('%A')  # Get the day of the week

        # SQL query to fetch report data
        query = '''
        SELECT 
            courses.semester,
            courses.section AS division,
            COUNT(DISTINCT enrollments.student_id) AS total_strength,
            courses.name AS subject,
            courses.slot AS timing,
            teachers.name AS professor,
            courses.classroom_lab_id AS classroom,
            IFNULL(SUM(CASE WHEN attendance.present = 1 THEN 1 ELSE 0 END), 0) AS present_students,
            IFNULL(MAX(attendance.lecture_capture), 'N') AS lecture_capture,
            IFNULL(MAX(attendance.pdf_uploaded), 'N') AS pdf_uploaded,
            IFNULL(MAX(attendance.assignments_collected), '0') AS assignments_collected,
            IFNULL(MAX(attendance.assignments_given), '0') AS assignments_given,
            IFNULL(MAX(attendance.assignments_graded), '0') AS assignments_graded
        FROM courses
        JOIN teachers ON courses.teacher_id = teachers.id
        LEFT JOIN enrollments ON courses.id = enrollments.course_id
        LEFT JOIN attendance ON enrollments.student_id = attendance.student_id 
                             AND courses.id = attendance.course_id
                             AND attendance.date = %s
        WHERE courses.days LIKE %s
        AND (%s IS NULL OR courses.year = %s)
        AND (%s IS NULL OR %s = 'All' OR courses.branch = %s)
        AND (%s IS NULL OR courses.semester = %s)
        GROUP BY courses.id, teachers.name, courses.semester, courses.section
        '''
        cursor = mysql.connection.cursor()
        cursor.execute(query, (date, f"%{day_of_week}%", year, year, branch, branch, branch, semester, semester))
        report = cursor.fetchall()
        cursor.close()

        if not report:
            flash("No data found for the selected criteria.", "warning")
            return redirect(url_for('generate_report'))

        # Store report data for the download function
        session['report_data'] = [dict(row) for row in report]

        # Render the report template with day_of_week
        return render_template('admin/generate_report.html', report=report, date=date, day_of_week=day_of_week)

    return render_template('admin/generate_report.html', report=None, date=None, day_of_week=None)

@app.route('/admin/download_excel', methods=['POST'])
def download_excel():
    report_data = session.get('report_data', [])
    
    # Check if there is data to export
    if not report_data:
        flash("No data available to download.", "warning")
        return redirect(url_for('generate_report'))
    
    # Define the column order
    columns_order = [
        "semester", "division", "total_strength", "subject", "timing", 
        "professor", "classroom", "present_students", "lecture_capture", 
        "pdf_uploaded", "assignments_collected", "assignments_given", "assignments_graded"
    ]
    
    # Create a DataFrame with columns in the specified order
    df = pd.DataFrame(report_data, columns=columns_order)
    
    # Create an Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Report")
    output.seek(0)
    
    # Send the file as a downloadable attachment
    response = make_response(output.read())
    response.headers["Content-Disposition"] = "attachment; filename=report.xlsx"
    response.headers["Content-Type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return response


@app.route('/admin/admin_take_attendance', methods=['GET', 'POST'])
def admin_take_attendance():
    cursor = mysql.connection.cursor()

    if request.method == 'POST':
        if 'take_attendance' in request.form:
            date = request.form['date']
            course_id = request.form['course_id']

            # Fetch course details to validate the day
            cursor.execute('SELECT id, name, days FROM courses WHERE id = %s', (course_id,))
            selected_course = cursor.fetchone()

            if selected_course:
                selected_date = datetime.strptime(date, '%Y-%m-%d').date()
                course_day = selected_course['days'].lower()  # Days column stores valid days (e.g., 'Monday')
                valid_days = {
                    'monday': 0, 'tuesday': 1, 'wednesday': 2,
                    'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6
                }

                # Validate course day
                if course_day not in valid_days:
                    flash(f"Invalid course day in database for course ID {course_id}.", 'danger')
                    return redirect(url_for('admin_take_attendance'))

                if valid_days[course_day] != selected_date.weekday():
                    flash(f"You can't take attendance on {selected_date.strftime('%A')}. The course day is {course_day.capitalize()}.", 'danger')
                    return redirect(url_for('admin_take_attendance'))

                # Check if attendance is already taken
                cursor.execute('SELECT COUNT(*) AS count FROM attendance WHERE course_id = %s AND date = %s', (course_id, date))
                attendance_count = cursor.fetchone()['count']
                if attendance_count > 0:
                    flash('Attendance for this course and date has already been taken!', 'danger')
                    return redirect(url_for('admin_take_attendance'))

            # Fetch students enrolled in the course
            cursor.execute('''
                SELECT s.id, s.first_name, s.last_name, s.roll_no, s.photo 
                FROM students s 
                JOIN enrollments e ON s.id = e.student_id 
                WHERE e.course_id = %s
            ''', (course_id,))
            students = cursor.fetchall()

            # Fetch all courses for the dropdown
            cursor.execute('''
                SELECT c.id, c.name, t.name AS teacher_name, c.branch, c.year, c.classroom_lab_id, c.days AS days
                FROM courses c
                JOIN teachers t ON c.teacher_id = t.id
            ''')
            courses = cursor.fetchall()

            cursor.close()
            return render_template('admin/admin_take_attendance.html', students=students, selected_course=selected_course, date=date, courses=courses)

        elif 'submit_attendance' in request.form:
            course_id = request.form['course_id']
            date = request.form['date']
            students_present = request.form.getlist('students_present')

            if not students_present:
                flash('No students were selected for attendance!', 'danger')
                return redirect(url_for('admin_take_attendance'))

            # Store attendance in the database
            for student_id in students_present:
                cursor.execute('INSERT INTO attendance (course_id, student_id, date, present) VALUES (%s, %s, %s, %s)', (course_id, student_id, date, True))

            mysql.connection.commit()
            cursor.close()

            flash('Attendance successfully submitted!', 'success')
            return redirect(url_for('admin_take_attendance'))

    # Fetch all courses for the dropdown
    cursor.execute('''
        SELECT c.id, c.name, t.name AS teacher_name, c.branch, c.year, c.classroom_lab_id, c.days AS days
        FROM courses c
        JOIN teachers t ON c.teacher_id = t.id
    ''')
    courses = cursor.fetchall()

    cursor.close()
    return render_template('admin/admin_take_attendance.html', courses=courses)



@app.route('/admin/admin_view_attendance', methods=['GET', 'POST'])
def admin_view_attendance():
    cursor = mysql.connection.cursor()

    # Fetch all necessary course data (including teacher_name, branch, year, and teacher_id)
    cursor.execute("""
        SELECT c.id, c.name, c.branch, c.year, t.name as teacher_name, t.id as teacher_id
        FROM courses c
        JOIN teachers t ON c.teacher_id = t.id
    """)
    courses = cursor.fetchall()

    if request.method == 'POST':
        course_id = request.form['course_id']
        start_date = request.form['start_date']
        end_date = request.form['end_date']

        # Fetch attendance records for the selected course and date range
        cursor.execute("""
            SELECT s.first_name, s.last_name, s.roll_no, s.branch, s.section, a.date, a.present
            FROM attendance a
            JOIN students s ON a.student_id = s.id
            WHERE a.course_id = %s AND a.date BETWEEN %s AND %s
            ORDER BY a.date, s.roll_no
        """, (course_id, start_date, end_date))
        attendance_records = cursor.fetchall()

        # Calculate attendance percentage for each student
        cursor.execute("""
            SELECT student_id, COUNT(*) as total_classes, 
            SUM(present) as classes_attended 
            FROM attendance 
            WHERE course_id = %s AND date BETWEEN %s AND %s 
            GROUP BY student_id
        """, (course_id, start_date, end_date))
        attendance_summary = cursor.fetchall()

        # Prepare data for rendering
        grouped_attendance = {}
        attendance_percentages = {}

        for record in attendance_records:
            date = record['date']
            if date not in grouped_attendance:
                grouped_attendance[date] = []
            grouped_attendance[date].append(record)

        for summary in attendance_summary:
            student_id = summary['student_id']
            total_classes = summary['total_classes']
            classes_attended = summary['classes_attended']
            percentage = (classes_attended / total_classes) * 100 if total_classes else 0
            attendance_percentages[student_id] = round(percentage, 2)

        # Find teacher_id for the selected course
        teacher_id = next(course['teacher_id'] for course in courses if course['id'] == int(course_id))

        cursor.close()

        return render_template(
            'admin/admin_view_attendance.html',
            grouped_attendance=grouped_attendance,
            attendance_percentages=attendance_percentages,
            courses=courses,
            course_id=course_id,
            start_date=start_date,
            end_date=end_date,
            teacher_id=teacher_id  # Pass teacher_id to the template
        )
    
    # GET request: Display the form to select course and date range
    cursor.close()
    return render_template('admin/admin_view_attendance.html', courses=courses)




@app.route('/teacher/view_attendance/<int:course_id>/download', methods=['GET', 'POST'])
def download_attendance(course_id):
    if 'teacher_id' not in session:
        return redirect(url_for('teacher_login'))

    # Fetch filtered attendance records (same as in view_attendance function)
    cursor = mysql.connection.cursor()

    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    branch = request.args.get('branch', 'All')
    section = request.args.get('section', 'All')

    query = '''
        SELECT CONCAT(students.first_name, ' ', students.last_name) AS name, 
               students.roll_no, students.branch, students.section, 
               attendance.date, attendance.present 
        FROM attendance 
        JOIN students ON attendance.student_id = students.id 
        WHERE attendance.course_id = %s AND attendance.date BETWEEN %s AND %s
    '''
    params = [course_id, start_date, end_date]

    if branch != 'All':
        query += ' AND students.branch = %s'
        params.append(branch)

    if section != 'All':
        query += ' AND students.section = %s'
        params.append(section)

    query += ' ORDER BY attendance.date'
    
    cursor.execute(query, tuple(params))
    attendance_records = cursor.fetchall()

    # Group attendance by date and student
    student_attendance = {}
    all_dates = set()

    for record in attendance_records:
        student = record['roll_no']
        date = record['date'].strftime('%Y-%m-%d')
        all_dates.add(date)
        
        if student not in student_attendance:
            student_attendance[student] = {
                'name': record['name'],
                'roll_no': record['roll_no'],
                'branch': record['branch'],
                'section': record['section'],
                'attendance': {}
            }
        student_attendance[student]['attendance'][date] = 'Yes' if record['present'] else 'No'

    # Sort dates
    all_dates = sorted(all_dates)

    # Calculate attendance percentage for each student
    for student in student_attendance:
        total_lectures = len(all_dates)
        present_count = sum(1 for date in all_dates if student_attendance[student]['attendance'].get(date) == 'Yes')
        percentage = (present_count / total_lectures) * 100 if total_lectures > 0 else 0
        student_attendance[student]['percentage'] = round(percentage, 2)
        student_attendance[student]['out_of'] = total_lectures
        student_attendance[student]['present_count'] = present_count

    # Create the Excel file
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet()

    # Define cell formats
    percentage_format = workbook.add_format({'num_format': '0.00%', 'align': 'center'})
    red_percentage_format = workbook.add_format({'num_format': '0.00%', 'align': 'center', 'font_color': 'red'})
    
    # Write the header
    headers = ['Sr.No.', 'Roll No.', 'Name of the Student', 'Branch', 'Section'] + all_dates + ['Present Count', 'Out of', 'Final Attendance Percentage']
    for col_num, header in enumerate(headers):
        worksheet.write(0, col_num, header)

    # Write attendance data with Sr. No
    for row_num, (student, data) in enumerate(student_attendance.items(), 1):
        worksheet.write(row_num, 0, row_num)  # Sr. No
        worksheet.write(row_num, 1, data['roll_no'])  # Roll No
        worksheet.write(row_num, 2, data['name'])  # Name
        worksheet.write(row_num, 3, data['branch'])  # Branch
        worksheet.write(row_num, 4, data['section'])  # Section

        # Add attendance data for each date
        for col_num, date in enumerate(all_dates, 5):
            attendance_status = data['attendance'].get(date, 'No')
            worksheet.write(row_num, col_num, attendance_status)

        # Add Present Count, Out of, and Percentage columns
        worksheet.write(row_num, len(all_dates) + 5, data['present_count'])  # Present Count
        worksheet.write(row_num, len(all_dates) + 6, data['out_of'])         # Out of
        
        percentage = data['percentage'] / 100
        if percentage < 0.75:
            worksheet.write(row_num, len(all_dates) + 7, percentage, red_percentage_format)
        else:
            worksheet.write(row_num, len(all_dates) + 7, percentage, percentage_format)

    workbook.close()
    output.seek(0)

    # Return the Excel file as a download
    return send_file(output, download_name='attendance.xlsx', as_attachment=True)


@app.route('/admin/admin_view_attendance/<int:course_id>/download', methods=['GET', 'POST'])
def admin_download_attendance(course_id):
  

    # Fetch filtered attendance records (same as in view_attendance function)
    cursor = mysql.connection.cursor()

    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    branch = request.args.get('branch', 'All')
    section = request.args.get('section', 'All')

    query = '''
        SELECT students.name, students.roll_no, students.branch, students.section, 
               attendance.date, attendance.present 
        FROM attendance 
        JOIN students ON attendance.student_id = students.id 
        WHERE attendance.course_id = %s AND attendance.date BETWEEN %s AND %s
    '''
    params = [course_id, start_date, end_date]

    if branch != 'All':
        query += ' AND students.branch = %s'
        params.append(branch)

    if section != 'All':
        query += ' AND students.section = %s'
        params.append(section)

    query += ' ORDER BY attendance.date'
    
    cursor.execute(query, tuple(params))
    attendance_records = cursor.fetchall()

    # Group attendance by date and student
    student_attendance = {}
    all_dates = set()

    for record in attendance_records:
        student = record['roll_no']
        date = record['date'].strftime('%Y-%m-%d')
        all_dates.add(date)
        
        if student not in student_attendance:
            student_attendance[student] = {
                'name': record['name'],
                'roll_no': record['roll_no'],
                'branch': record['branch'],
                'section': record['section'],
                'attendance': {}
            }
        student_attendance[student]['attendance'][date] = 'Yes' if record['present'] else 'No'

    # Sort dates
    all_dates = sorted(all_dates)

    # Calculate attendance percentage for each student
    for student in student_attendance:
        total_lectures = len(all_dates)
        present_count = sum(1 for date in all_dates if student_attendance[student]['attendance'].get(date) == 'Yes')
        percentage = (present_count / total_lectures) * 100 if total_lectures > 0 else 0
        student_attendance[student]['percentage'] = round(percentage, 2)
        student_attendance[student]['out_of'] = total_lectures
        student_attendance[student]['present_count'] = present_count

    # Create the Excel file
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet()

    # Define cell formats
    percentage_format = workbook.add_format({'num_format': '0.00%', 'align': 'center'})
    red_percentage_format = workbook.add_format({'num_format': '0.00%', 'align': 'center', 'font_color': 'red'})
    
    # Write the header
    headers = ['Sr.No.', 'Roll No.', 'Name of the Student', 'Branch', 'Section'] + all_dates + ['Present Count', 'Out of', 'Final Attendance Percentage']
    for col_num, header in enumerate(headers):
        worksheet.write(0, col_num, header)

    # Write attendance data with Sr. No
    for row_num, (student, data) in enumerate(student_attendance.items(), 1):
        worksheet.write(row_num, 0, row_num)  # Sr. No
        worksheet.write(row_num, 1, data['roll_no'])  # Roll No
        worksheet.write(row_num, 2, data['name'])  # Name
        worksheet.write(row_num, 3, data['branch'])  # Branch
        worksheet.write(row_num, 4, data['section'])  # Section

        # Add attendance data for each date
        for col_num, date in enumerate(all_dates, 5):
            attendance_status = data['attendance'].get(date, 'No')
            worksheet.write(row_num, col_num, attendance_status)

        # Add Present Count, Out of, and Percentage columns
        worksheet.write(row_num, len(all_dates) + 5, data['present_count'])  # Present Count
        worksheet.write(row_num, len(all_dates) + 6, data['out_of'])         # Out of
        
        percentage = data['percentage'] / 100
        if percentage < 0.75:
            worksheet.write(row_num, len(all_dates) + 7, percentage, red_percentage_format)
        else:
            worksheet.write(row_num, len(all_dates) + 7, percentage, percentage_format)

    workbook.close()
    output.seek(0)

    # Return the Excel file as a download
    return send_file(output, download_name='attendance.xlsx', as_attachment=True)

@app.route('/admin/admin_update_attendance/<int:course_id>/<date>', methods=['GET', 'POST'])
def admin_update_attendance(course_id, date):
    cursor = mysql.connection.cursor()

    if request.method == 'POST':
        date = request.form['date']
        students_present = request.form.getlist('students_present')  # List of students marked as present

        # Fetch the attendance status of all enrolled students for the given course and date
        cursor.execute('''
            SELECT student_id, present 
            FROM attendance 
            WHERE course_id = %s AND date = %s
        ''', (course_id, date))
        attendance_records = {record['student_id']: record['present'] for record in cursor.fetchall()}

        # Loop through all students in the attendance record
        for student_id, is_present in attendance_records.items():
            if str(student_id) in students_present:  # If student is marked as present in the form
                if not is_present:  # Only update if they were previously absent
                    cursor.execute('''
                        UPDATE attendance 
                        SET present = %s 
                        WHERE course_id = %s AND student_id = %s AND date = %s
                    ''', (True, course_id, student_id, date))  # Mark as present
            else:  # If student is not marked as present (i.e., absent)
                if is_present:  # Only update if they were previously present
                    cursor.execute('''
                        UPDATE attendance 
                        SET present = %s 
                        WHERE course_id = %s AND student_id = %s AND date = %s
                    ''', (False, course_id, student_id, date))  # Mark as absent

        # Commit changes and close the connection
        mysql.connection.commit()
        cursor.close()
        flash('Attendance updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))

    # Fetch the current attendance state for display in the form
    cursor.execute('''
        SELECT students.id, students.first_name,students.last_name, students.roll_no, students.photo, 
               IFNULL(attendance.present, False) AS present 
        FROM students 
        LEFT JOIN attendance 
        ON students.id = attendance.student_id 
           AND attendance.course_id = %s 
           AND attendance.date = %s 
        WHERE students.id IN (SELECT student_id FROM enrollments WHERE course_id = %s)
    ''', (course_id, date, course_id))
    
    students = cursor.fetchall()
    cursor.close()

    return render_template('admin/admin_update_attendance.html', students=students, course_id=course_id, date=date)


@app.route('/admin/admin_delete_attendance/<int:course_id>/<string:date>', methods=['GET'])
def admin_delete_attendance(course_id, date):
    cursor = mysql.connection.cursor()

    # Delete attendance records for the selected course and date
    cursor.execute("""
        DELETE FROM attendance
        WHERE course_id = %s AND date = %s
    """, (course_id, date))

    mysql.connection.commit()
    cursor.close()

    # Redirect back to the view attendance page after deletion
    flash('Attendance records for the selected date have been deleted successfully.', 'success')
    return redirect(url_for('admin_view_attendance'))





@app.route('/admin/teachers')
def admin_view_teachers():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM teachers")
    teachers = cur.fetchall()
    cur.close()
    return render_template('admin/admin_view_teachers.html', teachers=teachers)






# View all courses

@app.route('/admin/courses', methods=['GET'])
def admin_view_courses():
    # Fetch filters from the request
    department = request.args.get('department', default=None)
    year = request.args.get('year', default=None)
    section = request.args.get('section', default=None)
    semester = request.args.get('semester', default=None)
    teacher_name = request.args.get('teacher_name', default=None)
    course_year = request.args.get('course_year', default=None)

    # Fetch teacher list for the dropdown
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, name FROM teachers")
    teachers = cur.fetchall()

    # Build the query dynamically
    query = """
        SELECT c.*, t.name AS teacher_name
        FROM courses c
        JOIN teachers t ON c.teacher_id = t.id
        WHERE 1=1
    """
    params = []

    if department:
        query += " AND c.branch = %s"
        params.append(department)
    if year:
        query += " AND c.year = %s"
        params.append(year)
    if section:
        query += " AND c.section = %s"
        params.append(section)
    if semester:
        query += " AND c.semester = %s"
        params.append(semester)
    if teacher_name:
        query += " AND c.teacher_id = %s"
        params.append(teacher_name)
    if course_year:
        query += " AND YEAR(c.date) = %s"
        params.append(course_year)

    # Execute the query
    cur.execute(query, params)
    courses = cur.fetchall()

    # Format data for timetable
    timetable = {}
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    for day in days:
        timetable[day] = { 
            "8:00am to 9:00am": [],
            "9:00am to 11:00am": [],
            "11:15am to 1:15pm": [],
            "1:45pm to 3:45pm": [],
            "3:45pm to 5:45pm": []
        }

    for course in courses:
        slots = course['slot'].split(",")  # Ensure slots and days are comma-separated
        days_list = course['days'].split(",")
        for day in days_list:
            if day in timetable:
                for slot in slots:
                    if slot in timetable[day]:
                        timetable[day][slot].append({
                            "teacher_name": course['teacher_name'],  # Now using teacher's name
                            "course_name": course['name'],
                            "room_id": course['classroom_lab_id']
                        })

    cur.close()

    # Render the template
    return render_template('admin/admin_view_courses.html', courses=courses, teachers=teachers, timetable=timetable)


@app.route('/admin/add_course', methods=['GET', 'POST'])
def admin_add_course():
    if request.method == 'GET':
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, name FROM teachers")  # Fetch teacher list
        teachers = cur.fetchall()
        cur.close()
        return render_template('admin/admin_add_course.html', teachers=teachers)
    
    if request.method == 'POST':
        # Extract form data
        name = request.form['name']
        teacher_id = request.form['teacher_id']
        year = request.form['year']
        branch = request.form['branch']
        section = request.form['section']
        semester = request.form['semester']
        slot = request.form['slot']
        course_type = request.form['type']
        days = request.form['days']
        classroom_lab_id = request.form['classroom_lab_id']
        date = request.form['date']
        
        # Insert into the database
        cur = mysql.connection.cursor()
        query = """
            INSERT INTO courses 
            (name, teacher_id, year, branch, section, semester, slot, type, days, classroom_lab_id, date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (name, teacher_id, year, branch, section, semester, slot, course_type, days, classroom_lab_id, date)
        cur.execute(query, values)
        mysql.connection.commit()
        cur.close()
        return "Course Added Successfully!"

@app.route('/admin/student_report', methods=['GET', 'POST'])
def student_report():
    cursor = mysql.connection.cursor()

    if request.method == 'POST':
        student_id = request.form['student_id']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        course_id = request.form.get('course_id', None)

        # Query to fetch attendance report based on filters
        query = """
        SELECT 
            courses.name AS course_name, 
            courses.slot, 
            courses.year AS course_year, 
            courses.branch, 
            courses.section,
            teachers.name AS teacher_name,
            SUM(attendance.present) AS attended_classes,
            COUNT(attendance.date) AS total_classes,
            (SUM(attendance.present) / COUNT(attendance.date)) * 100 AS attendance_percentage
        FROM 
            attendance 
        JOIN 
            courses ON attendance.course_id = courses.id 
        JOIN 
            teachers ON courses.teacher_id = teachers.id 
        WHERE 
            attendance.student_id = %s 
            AND attendance.date BETWEEN %s AND %s
        """

        params = [student_id, start_date, end_date]
        if course_id:
            query += " AND attendance.course_id = %s"
            params.append(course_id)

        # Group by course details to avoid duplicates
        query += " GROUP BY courses.id, teachers.name"

        cursor.execute(query, params)
        report_data = cursor.fetchall()

        # Calculate total attendance percentage for the selected date range
        cursor.execute("""
        SELECT 
            COUNT(*) AS total_classes, 
            SUM(attendance.present) AS attended_classes 
        FROM 
            attendance 
        WHERE 
            student_id = %s 
            AND date BETWEEN %s AND %s
        """, [student_id, start_date, end_date])
        attendance_stats = cursor.fetchone()

        total_classes = attendance_stats['total_classes']
        attended_classes = attendance_stats['attended_classes']
        attendance_percentage = (attended_classes / total_classes) * 100 if total_classes > 0 else 0

        # Calculate remarks for each course based on attendance percentage
        for course in report_data:
            course_attendance_percentage = (course['attended_classes'] / course['total_classes']) * 100 if course['total_classes'] > 0 else 0
            
            if course_attendance_percentage < 30:
                course['remark'] = "Very Bad"
            elif 30 <= course_attendance_percentage < 60:
                course['remark'] = "Bad"
            elif 60 <= course_attendance_percentage < 80:
                course['remark'] = "Good"
            elif 80 <= course_attendance_percentage < 100:
                course['remark'] = "Very Good"
            else:
                course['remark'] = "Excellent"

        return render_template('admin/student_report.html', 
                               report_data=report_data, 
                               overall_attendance_percentage=attendance_percentage)

    # Populate form with students and courses
    cursor.execute("SELECT first_name, last_name, id, roll_no FROM students")
    students = cursor.fetchall()

    cursor.execute("SELECT * FROM courses")
    courses = cursor.fetchall()

    return render_template('admin/student_report.html', students=students, courses=courses)

@app.route('/teacher/generate_student_report', methods=['GET', 'POST'])
def generate_student_report():
    teacher_id = session.get('teacher_id')
    
    # Fetch all students and courses assigned to this teacher
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, first_name, last_name, roll_no FROM students")  # Fetch first_name and last_name
    students = cursor.fetchall()
    
    cursor.execute("SELECT id, name, slot FROM courses WHERE teacher_id = %s", (teacher_id,))
    courses = cursor.fetchall()

    report_data = []
    
    if request.method == 'POST':
        student_id = request.form['student_id']
        course_id = request.form.get('course_id')  # course_id can be None if not selected
        start_date = request.form['start_date']
        end_date = request.form['end_date']

        # Build query based on whether a specific course is selected
        if course_id:
            query = """
                SELECT 
                    courses.name AS course_name, 
                    courses.slot, 
                    courses.year AS course_year,
                    courses.branch, 
                    courses.section, 
                    teachers.name AS teacher_name,
                    COUNT(attendance.id) AS attended_classes,
                    (SELECT COUNT(DISTINCT date) FROM attendance 
                     WHERE attendance.course_id = %s 
                     AND attendance.date BETWEEN %s AND %s) AS total_classes,
                    (COUNT(attendance.id) / NULLIF((SELECT COUNT(DISTINCT date) FROM attendance 
                     WHERE attendance.course_id = %s 
                     AND attendance.date BETWEEN %s AND %s), 0) * 100) AS attendance_percentage
                FROM attendance
                JOIN courses ON attendance.course_id = courses.id
                JOIN teachers ON courses.teacher_id = teachers.id
                WHERE attendance.student_id = %s AND attendance.course_id = %s
                AND attendance.date BETWEEN %s AND %s
                GROUP BY courses.id
            """
            params = (course_id, start_date, end_date, course_id, start_date, end_date, student_id, course_id, start_date, end_date)
        else:
            query = """
                SELECT 
                    courses.name AS course_name, 
                    courses.slot, 
                    courses.year AS course_year,
                    courses.branch, 
                    courses.section, 
                    teachers.name AS teacher_name,
                    COUNT(attendance.id) AS attended_classes,
                    (SELECT COUNT(DISTINCT date) FROM attendance 
                     WHERE attendance.course_id IN (SELECT id FROM courses WHERE teacher_id = %s) 
                     AND attendance.date BETWEEN %s AND %s) AS total_classes,
                    (COUNT(attendance.id) / NULLIF((SELECT COUNT(DISTINCT date) FROM attendance 
                     WHERE attendance.course_id IN (SELECT id FROM courses WHERE teacher_id = %s) 
                     AND attendance.date BETWEEN %s AND %s), 0) * 100) AS attendance_percentage
                FROM attendance
                JOIN courses ON attendance.course_id = courses.id
                JOIN teachers ON courses.teacher_id = teachers.id
                WHERE attendance.student_id = %s AND courses.teacher_id = %s
                AND attendance.date BETWEEN %s AND %s
                GROUP BY courses.id
            """
            params = (teacher_id, start_date, end_date, teacher_id, start_date, end_date, student_id, teacher_id, start_date, end_date)

        # Execute the query and fetch results
        cursor.execute(query, params)
        report_data = cursor.fetchall()

        # Calculate remarks based on attendance percentage
        for course in report_data:
            percentage = course['attendance_percentage']
            if percentage == 100:
                course['remark'] = 'Excellent'
            elif percentage > 80:
                course['remark'] = 'Very Good'
            elif percentage > 60:
                course['remark'] = 'Good'
            elif percentage > 30:
                course['remark'] = 'Bad'
            else:
                course['remark'] = 'Very Bad'

    # Close cursor after processing
    cursor.close()

    return render_template('teacher/generate_student_report.html', students=students, courses=courses, report_data=report_data)


if __name__ == '__main__':
    app.run(debug=True)
