
--aftter  changes




-- Create tables

CREATE TABLE students (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    contact VARCHAR(15),
    class VARCHAR(50),
    password VARCHAR(255) NOT NULL,
    roll_no VARCHAR(20) NOT NULL,
    section VARCHAR(1) NOT NULL,
    year INT NOT NULL,
    branch VARCHAR(10) NOT NULL,
    photo VARCHAR(255) DEFAULT 'nophoto.jpg'
);

CREATE TABLE teachers (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    contact VARCHAR(15),
    department VARCHAR(50),
    password VARCHAR(255) NOT NULL,
    profile_photo VARCHAR(255) DEFAULT 'nophoto.jpg'
);

CREATE TABLE courses (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    teacher_id INT,
    year VARCHAR(50),
    date DATE,
    time TIME,
    branch VARCHAR(10) NOT NULL,
    section VARCHAR(1) NOT NULL,
    slot VARCHAR(20) NOT NULL,
    type VARCHAR(10) NOT NULL,
    classroom_lab_id VARCHAR(20) NOT NULL,
    FOREIGN KEY (teacher_id) REFERENCES teachers(id)
);

CREATE TABLE enrollments (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    student_id INT,
    course_id INT,
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (course_id) REFERENCES courses(id)
);

CREATE TABLE attendance (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    course_id INT,
    student_id INT,
    date DATE,
    present TINYINT(1),
    time TIME,
    FOREIGN KEY (course_id) REFERENCES courses(id),
    FOREIGN KEY (student_id) REFERENCES students(id)
);

ALTER TABLE attendance
ADD COLUMN lecture_capture CHAR(1) DEFAULT 'N', -- Y/N for lecture capture
ADD COLUMN pdf_uploaded CHAR(1) DEFAULT 'N', -- Y/N for smart board PDF uploaded
ADD COLUMN assignments_collected VARCHAR(255), -- Collected assignments (last week)
ADD COLUMN assignments_given VARCHAR(255), -- Given assignments (coming week)
ADD COLUMN assignments_graded VARCHAR(255); -- Graded and distributed assignments (previous week)


CREATE TABLE notifications (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    student_id INT,
    teacher_id INT,
    message VARCHAR(255) NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (teacher_id) REFERENCES teachers(id)
);

-- Create absence_applications table
CREATE TABLE absence_applications (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    teacher_id INT NOT NULL,
    date_of_application DATE NOT NULL,
    number_of_days INT NOT NULL,
    reason TEXT NOT NULL,
    status ENUM('In Progress', 'Approved', 'Rejected') DEFAULT 'In Progress',
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (teacher_id) REFERENCES teachers(id)
);

CREATE TABLE admin (
    id INT NOT NULL AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    PRIMARY KEY (id)
);




-- Insert sample data

ALTER TABLE absence_applications
DROP FOREIGN KEY absence_applications_ibfk_2;

ALTER TABLE absence_applications
ADD CONSTRAINT absence_applications_ibfk_2
FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE;


ALTER TABLE courses
ADD CONSTRAINT fk_teacher
FOREIGN KEY (teacher_id) REFERENCES teachers(id)
ON DELETE CASCADE;


ALTER TABLE attendance
ADD CONSTRAINT fk_course
FOREIGN KEY (course_id) REFERENCES courses(id)
ON DELETE CASCADE;







CREATE TABLE students (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    contact VARCHAR(15),
    class VARCHAR(50),
    password VARCHAR(255) NOT NULL,
    roll_no VARCHAR(20) NOT NULL,
    section VARCHAR(1) NOT NULL,
    year INT NOT NULL,
    branch VARCHAR(10) NOT NULL,
    photo VARCHAR(255) DEFAULT 'nophoto.jpg'
);

CREATE TABLE teachers (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    contact VARCHAR(15),
    department VARCHAR(50),
    password VARCHAR(255) NOT NULL,
    profile_photo VARCHAR(255) DEFAULT 'nophoto.jpg'
);


CREATE TABLE courses (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    teacher_id INT,
    year VARCHAR(50),
    date DATE,
    time TIME,
    branch VARCHAR(10) NOT NULL,
    section VARCHAR(1) NOT NULL,
    slot VARCHAR(20) NOT NULL,
    type VARCHAR(10) NOT NULL,
    classroom_lab_id VARCHAR(20) NOT NULL,
    days VARCHAR(10),  -- Added field to store days of the week
    semester VARCHAR(10),  -- Added field for the semester
    FOREIGN KEY (teacher_id) REFERENCES teachers(id)
);


CREATE TABLE enrollments (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    student_id INT,
    course_id INT,
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (course_id) REFERENCES courses(id)
);


CREATE TABLE attendance (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    course_id INT,
    student_id INT,
    date DATE,
    present TINYINT(1),
    time TIME,
    lecture_capture CHAR(1) DEFAULT 'N',
    pdf_uploaded CHAR(1) DEFAULT 'N',
    assignments_collected VARCHAR(255),
    assignments_given VARCHAR(255),
    assignments_graded VARCHAR(255),
    FOREIGN KEY (course_id) REFERENCES courses(id),
    FOREIGN KEY (student_id) REFERENCES students(id)
);


CREATE TABLE notifications (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    student_id INT,
    teacher_id INT,
    message VARCHAR(255) NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (teacher_id) REFERENCES teachers(id)
);


CREATE TABLE absence_applications (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    teacher_id INT NOT NULL,
    date_of_application DATE NOT NULL,
    number_of_days INT NOT NULL,
    reason TEXT NOT NULL,
    status ENUM('In Progress', 'Approved', 'Rejected') DEFAULT 'In Progress',
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (teacher_id) REFERENCES teachers(id)
);


CREATE TABLE admin (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
);



ALTER TABLE students
ADD COLUMN first_name VARCHAR(100) NOT NULL,
ADD COLUMN middle_name VARCHAR(100),  -- Optional
ADD COLUMN last_name VARCHAR(100) NOT NULL;

-- Dropping the old 'name' column after splitting it
ALTER TABLE students
DROP COLUMN name;


-- Altering the teachers table to add the 'short_name' column
ALTER TABLE teachers
ADD COLUMN short_name VARCHAR(50);  -- Short form of the teacher's name

-- Add unique constraint on short_name column to ensure no two teachers can have the same short name
ALTER TABLE teachers
ADD CONSTRAINT unique_short_name UNIQUE (short_name);



ALTER TABLE students MODIFY email VARCHAR(255) NULL;
ALTER TABLE students ADD UNIQUE (email);


ALTER TABLE attendance ADD COLUMN is_draft BOOLEAN DEFAULT FALSE;

ALTER TABLE teachers
ADD course_requests VARCHAR(255) DEFAULT NULL;


ALTER TABLE notifications
ADD COLUMN course_id INT,
ADD FOREIGN KEY (course_id) REFERENCES courses(id);
