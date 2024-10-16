from flask import Flask, render_template, request, redirect, url_for, flash,send_file, session
from flask_mysqldb import MySQL

from werkzeug.security import generate_password_hash, check_password_hash
import openpyxl
import xlsxwriter
import io
import pandas as pd
from io import BytesIO
import os




from werkzeug.utils import secure_filename

# Ensure you define the upload folder and allowed extensions


app = Flask(__name__)


UPLOAD_FOLDER = 'static/uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Configure MySQL
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '12345678'
app.config['MYSQL_DB'] = 'collage'
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


# Admin login route
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'Mohit' and password == 'Mohit':
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')
    return render_template('adminlogin.html')

# Admin dashboard route
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin' not in session:
        flash('Please log in as admin to access the dashboard.', 'warning')
        return redirect(url_for('admin_login'))
    try:
        cur = mysql.connection.cursor()
        cur.execute('SELECT COUNT(*) AS count FROM teachers')
        total_teachers = cur.fetchone()['count']
        cur.execute('SELECT COUNT(*) AS count FROM students')
        total_students = cur.fetchone()['count']
        cur.execute('SELECT COUNT(*) AS count FROM subjects')
        total_subjects = cur.fetchone()['count']
        cur.close()
        return render_template('admin_dashboard.html', total_teachers=total_teachers, total_students=total_students, total_subjects=total_subjects)
    except Exception as e:
        return str(e)
    
    
@app.route('/teacher/signup', methods=['GET', 'POST'])
def teacher_signup():
    if request.method == 'POST':
        name = request.form['name']
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
        cursor.execute('INSERT INTO teachers (name, email, contact, department, password) VALUES (%s, %s, %s, %s, %s)',
                       (name, email, contact, department, generate_password_hash(password)))
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

        # Update teacher's profile in the database
        cursor.execute("""
            UPDATE teachers 
            SET name = %s, email = %s, contact = %s, department = %s, profile_photo = %s 
            WHERE id = %s
        """, (name, email, contact, department, profile_photo, session['teacher_id']))
        mysql.connection.commit()
        cursor.close()

        # Update the session photo immediately after upload or removal
        session['teacher_photo'] = profile_photo

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

    if request.method == 'POST':
        date = request.form['date']

        # Check if attendance already exists
        cursor.execute('SELECT COUNT(*) FROM attendance WHERE course_id = %s AND date = %s', (course_id, date))
        if cursor.fetchone()['COUNT(*)'] > 0:
            flash('Attendance for this date has already been recorded. Please use the update option if changes are needed.', 'warning')
            return redirect(url_for('teacher_take_attendance', course_id=course_id))

        students_present = request.form.getlist('students_present')

        # Mark all students as absent
        cursor.execute('SELECT student_id FROM enrollments WHERE course_id = %s', (course_id,))
        all_students = cursor.fetchall()
        for student in all_students:
            cursor.execute('INSERT INTO attendance (course_id, student_id, date, present) VALUES (%s, %s, %s, %s)', (course_id, student['student_id'], date, False))

        # Mark selected students as present
        for student_id in students_present:
            cursor.execute('UPDATE attendance SET present = %s WHERE course_id = %s AND student_id = %s AND date = %s', (True, course_id, student_id, date))

        mysql.connection.commit()
        cursor.close()
        flash('Attendance recorded successfully!', 'success')
        return redirect(url_for('teacher_dashboard'))

    cursor.execute('SELECT id, name, roll_no, photo FROM students WHERE id IN (SELECT student_id FROM enrollments WHERE course_id = %s)', (course_id,))
    students = cursor.fetchall()

    cursor.close()
    return render_template('teacher/teacher_take_attendance.html', students=students, course_id=course_id)

@app.route('/teacher/take_attendance', methods=['GET', 'POST'])
def teacher_take_attendance_initial():
    if 'teacher_id' not in session:
        return redirect(url_for('teacher_login'))

    cursor = mysql.connection.cursor()

    if request.method == 'POST':
        course_id = request.form['course_id']
        date = request.form['date']

        # Check if attendance already exists for this course on this date
        cursor.execute('SELECT COUNT(*) FROM attendance WHERE course_id = %s AND date = %s', (course_id, date))
        if cursor.fetchone()['COUNT(*)'] > 0:
            flash('Attendance for this date has already been recorded. Please use the update option if changes are needed.', 'warning')
            return redirect(url_for('teacher_take_attendance_initial'))

        # Redirect to the take attendance page with course_id and date
        return redirect(url_for('teacher_take_attendance', course_id=course_id, date=date))

    # Fetch all courses taught by the teacher
    cursor.execute('SELECT * FROM courses WHERE teacher_id = %s', (session['teacher_id'],))
    courses = cursor.fetchall()

    cursor.close()
    return render_template('teacher/take_attandance.html', courses=courses)


@app.route('/teacher/manage_attendance', methods=['GET', 'POST'])
def manage_attendance():
    if request.method == 'POST':
        year = request.form['year']
        branch = request.form['branch']
        slot = request.form['slot']
        section = request.form['section']
        classroom_lab_id = request.form['classroom_lab_id']
        
        teacher_id = session.get('teacher_id')

        cursor = mysql.connection.cursor()
        query = "SELECT * FROM courses WHERE teacher_id = %s"
        params = [teacher_id]

        if year != "ALL":
            query += " AND year = %s"
            params.append(year)

        if branch != "ALL":
            query += " AND branch = %s"
            params.append(branch)

        if slot != "ALL":
            query += " AND slot = %s"
            params.append(slot)

        if section != "ALL":
            query += " AND section = %s"
            params.append(section)

        if classroom_lab_id:
            query += " AND classroom_lab_id = %s"
            params.append(classroom_lab_id)

        cursor.execute(query, params)
        courses = cursor.fetchall()
        cursor.close()

        return render_template('teacher/manage_attendance.html', courses=courses)

    return render_template('teacher/manage_attendance.html', courses=None)

@app.route('/teacher/start_attendance/<int:course_id>', methods=['GET', 'POST'])
def start_attendance(course_id):
    cursor = mysql.connection.cursor()

    if request.method == 'POST':
        date = request.form['date']
        students = request.form.getlist('students')

        cursor.execute("SELECT * FROM attendance WHERE course_id = %s AND date = %s", (course_id, date))
        existing_attendance = cursor.fetchone()

        if existing_attendance:
            flash('Attendance already taken for this course on the selected date.', 'danger')
            return redirect(url_for('manage_attendance'))

        for student_id in students:
            present = request.form.get(f'present_{student_id}', 'absent') == 'present'
            cursor.execute(
                "INSERT INTO attendance (course_id, student_id, date, present) VALUES (%s, %s, %s, %s)",
                (course_id, student_id, date, 1 if present else 0)
            )
        
        mysql.connection.commit()
        cursor.close()
        flash('Attendance successfully recorded.', 'success')
        return redirect(url_for('manage_attendance'))
    
    cursor.execute("SELECT * FROM courses WHERE id = %s", (course_id,))
    course = cursor.fetchone()

    cursor.execute("SELECT students.id, students.name, students.roll_no FROM students INNER JOIN enrollments ON students.id = enrollments.student_id WHERE enrollments.course_id = %s", (course_id,))
    students = cursor.fetchall()

    cursor.close()

    return render_template('teacher/start_attendance.html', course=course, students=students)


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

    cursor.execute('SELECT students.id, students.name, students.roll_no, students.photo, IFNULL(attendance.present, False) AS present FROM students LEFT JOIN attendance ON students.id = attendance.student_id AND attendance.course_id = %s AND attendance.date = %s WHERE students.id IN (SELECT student_id FROM enrollments WHERE course_id = %s)', (course_id, date, course_id))
    students = cursor.fetchall()

    cursor.close()
    return render_template('teacher/update_attendance.html', students=students, course_id=course_id, date=date)

@app.route('/teacher/view_attendance/<int:course_id>', methods=['GET', 'POST'])
def view_attendance(course_id):
    if 'teacher_id' not in session:
        return redirect(url_for('teacher_login'))

    cursor = mysql.connection.cursor()

    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        branch = request.form.get('branch')
        section = request.form.get('section')

        # Log the form inputs for debugging
        print(f"Start Date: {start_date}, End Date: {end_date}, Branch: {branch}, Section: {section}")

        # Prepare query to filter attendance
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
                           sections=sections)


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
        sql_query = "SELECT * FROM students WHERE 1=1"
        sql_params = []

        # Search by name or roll number
        if query:
            sql_query += " AND (name LIKE %s OR roll_no LIKE %s)"
            sql_params.extend([f"%{query}%", f"%{query}%"])

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

    # Fetch students enrolled in the course
    cursor.execute("""
        SELECT s.id, s.name, s.roll_no, s.branch, s.year, s.section, s.photo
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




@app.route('/teacher/notify_students/<int:course_id>')
def notify_students(course_id):
    cursor = mysql.connection.cursor()

    # Fetch all students in the course
    cursor.execute("""
        SELECT s.id, s.name, s.email 
        FROM students s 
        JOIN enrollments e ON s.id = e.student_id 
        WHERE e.course_id = %s
    """, (course_id,))
    students = cursor.fetchall()

    for student in students:
        percentage = calculate_attendance_percentage(student['id'], course_id)
        if percentage < 75:
            # Send notification (for example, via email)
            flash(f"Student {student['name']} ({student['email']}) has low attendance: {percentage:.2f}%", 'warning')

    cursor.close()

    return redirect(url_for('teacher_profile', teacher_id=session['teacher_id']))


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
            session['student_id'] = student['id']
            session['student_name'] = student['name']
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
        name = request.form['name']
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

        cursor.execute('INSERT INTO students (roll_no, name, email, section, year, branch, password, photo) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
                       (roll_no, name, email, section, year, branch, generate_password_hash(password), photo_filename))
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
    session['student_name'] = student['name']

    return render_template('student/student_profile.html', student=student)


@app.route('/student/profile/edit', methods=['GET', 'POST'])
def student_edit_profile():
    student_id = session.get('student_id')
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM students WHERE id = %s', (student_id,))
    student = cursor.fetchone()

    if request.method == 'POST':
        name = request.form['name']
        roll_no = request.form['roll_no']
        email = request.form['email']
        contact = request.form['contact']
        photo = request.files['photo'] if 'photo' in request.files else None
        remove_photo = 'remove_photo' in request.form

        if remove_photo:
            photo_filename = 'nophoto.jpg'
            cursor.execute('UPDATE students SET name = %s, roll_no = %s, email = %s, contact = %s, photo = %s WHERE id = %s',
                           (name, roll_no, email, contact, photo_filename, student_id))
            session['student_photo'] = photo_filename
        elif photo and allowed_file(photo.filename):
            photo_filename = secure_filename(photo.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], photo_filename)
            photo.save(save_path)
            cursor.execute('UPDATE students SET name = %s, roll_no = %s, email = %s, contact = %s, photo = %s WHERE id = %s',
                           (name, roll_no, email, contact, photo_filename, student_id))
            session['student_photo'] = photo_filename
        else:
            cursor.execute('UPDATE students SET name = %s, roll_no = %s, email = %s, contact = %s WHERE id = %s',
                           (name, roll_no, email, contact, student_id))

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
    query = request.args.get('query', '')
    cursor = mysql.connection.cursor()

    # Search in students table
    cursor.execute("SELECT * FROM students WHERE name LIKE %s OR email LIKE %s", (f"%{query}%", f"%{query}%"))
    students = cursor.fetchall()

    # Search in teachers table
    cursor.execute("SELECT * FROM teachers WHERE name LIKE %s OR email LIKE %s", (f"%{query}%", f"%{query}%"))
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
    teacher_id = session.get('teacher_id')  # Assuming teacher is logged in
    cur = mysql.connection.cursor()
    cur.execute('''
        SELECT absence_applications.*, students.name AS student_name
        FROM absence_applications
        JOIN students ON absence_applications.student_id = students.id
        WHERE absence_applications.teacher_id = %s
    ''', (teacher_id,))
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
    cur.close()

    return render_template('student/courses.html', available_courses=available_courses, enrolled_courses=enrolled_courses)

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


if __name__ == '__main__':
    app.run(debug=True)
