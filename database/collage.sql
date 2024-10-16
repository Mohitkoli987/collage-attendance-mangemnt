-- Create Teachers Table
CREATE TABLE teachers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    contact VARCHAR(15),
    department VARCHAR(50),
    password VARCHAR(255) NOT NULL
);

-- Create Students Table
CREATE TABLE students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    contact VARCHAR(15),
    password VARCHAR(255) NOT NULL
);

-- Create Courses Table
CREATE TABLE courses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    teacher_id INT,
    FOREIGN KEY (teacher_id) REFERENCES teachers(id)
);

-- Create Attendance Table
CREATE TABLE attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT,
    student_id INT,
    date DATE,
    present BOOLEAN,
    FOREIGN KEY (course_id) REFERENCES courses(id),
    FOREIGN KEY (student_id) REFERENCES students(id)
);

CREATE TABLE notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT,
    teacher_id INT,
    message VARCHAR(255) NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE
);


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

-- Insert sample data

INSERT INTO students (name, email, contact, class, password, roll_no, section, year, branch, photo) VALUES
('mohit', 'mohitkoli9888@gmail.com', '9326747269', 'intft B', 'scrypt:32768:8:1$VLFd4skTcrgcMmkM$fd2212ca7b4a4f020d5e482b07598fe18247a2fcf8085233a41f02eb752f0f7cd3bdb67956ef80c449f32146d58f2b70cf54a51a29d05775b89a477faa419fe2', '22101B0001', '', 0, '', NULL),
('om', 'om@gmail.com', '12345678', '3rd year', 'scrypt:32768:8:1$UgKCS0szxWlMjddV$f2c4b6584f94822aa19addc88b2999a510782016ed80b279ffb2d390dc25a050041b4005e903095e3db13e21dd769b8aa5678f7f511be294c1ba4f1ba97dd5e5', '22101B0002', '', 0, '', NULL),
('sahil', 'sahil@gmail.com', '12345678', '3rd', 'scrypt:32768:8:1$h4pG9mpEqmaWs99Z$3d586ec0c94131504ea1f98bda4b4178bb443a2950ecee25cd00749677671ff511f31bbdb19f8a35fbcf4bafc523ccd12705f342619aa8fe3f289236e2497c18', '22101B0003', '', 0, '', NULL),
('sachin', 'sachin@gmail.com', '123456789', '1st', 'scrypt:32768:8:1$kxBCeC4cGvFAEcNT$407483f3d6b8031fd67acade88e8c7d7eedce136d68cee0eec002533c3203b64295f0286553545cd5d0e3cb731c52e50139c9a76a47df4e279541ceb4c040d12', '22101B0004', '', 0, '', NULL),
('Mohit koli', 'kolimohit2002@gmail.com', '9326747269', 'None', 'scrypt:32768:8:1$X0Q2RYBkkUSNGncR$409f2959277a3bc9131087d71b3972ac1b4ccdbfec7da65bf9c84a37560605e85fecc65e7cadf15c19097915f7a2797553a1e2af479151f820af4aee0afc07a9', '22101B0022', 'B', 3, 'INFT', NULL),
('om singh', 'omsingh@gmail.com', 'None', 'None', 'scrypt:32768:8:1$RkUNoWYzoxPbjSEb$5c1fd95a4dd328b521e56d9e556e65e52d265013aeb8e4efa69213c27fa91481f79cb2f4cbbda40919cbe3293aa94894fcff41efe74048d032199df79c458074', '22101B0049', 'B', 3, 'INFT', 'shopping-9.jpeg');

INSERT INTO teachers (name, email, contact, department, password, profile_photo) VALUES
('abc', 'abc@gmail.com', '12345678', 'IT', 'scrypt:32768:8:1$z38zNRfrq7TQZMlW$a0d003ab4e3f2db6e0853623566c66cb756a6a59ee1c39d69bc05600378a66eb8668a952147c9beaefb078d8c5d79c82e803f69b8c3fa46e159d6f66ed899ce1', 'nophoto.jpg'),
('abcd', 'abcd@gmail.com', '12345678', 'CS', 'scrypt:32768:8:1$vq5wGjk4zoTPyiof$8818e989893c87809d4d364767027d39f0a89ef6b418267bce935319080f7564ed15a6117739086d6983155407819867d6584a8b4aadc0355f9f36f15895614f', 'nophoto.jpg'),
('prof bhanu tekwani', 'bhanu@gmail.com', '12345678', 'Information Technology', 'scrypt:32768:8:1$dgxAzkiWu0iP2QQu$2a60589c899fd49f10186e6e7dc468c00efc9297a063eacc9701049005b162d18bc40d0d88d33287cfcf7ea5cd0ebd3bf50811134c1e9a6557327ad23fee174a', 'nophoto.jpg');

INSERT INTO courses (name, teacher_id, year, date, time, branch, section, slot, type, classroom_lab_id) VALUES
('math 2', 2, '1st', '2024-07-27', '12:30:00', '', '', '', '', ''),
('math3', 2, '2nd', '2024-07-31', '09:00:00', '', '', '', '', ''),
('math1', 2, '1st', '2024-07-15', '01:00:00', '', '', '', '', ''),
('advance java', 2, '1', '2024-08-21', NULL, 'INFT', 'A', '9:00am to 11:00am', 'Lecture', 'm101');

INSERT INTO enrollments (student_id, course_id) VALUES
(1, 3),
(2, 2),
(3, 3),
(4, 4),
(3, 2),
(1, 2),
(6, 2),
(6, 5),
(6, 3);

INSERT INTO attendance (course_id, student_id, date, present, time) VALUES
(1, 1, '2024-08-12', 1, '09:00:00'),
(2, 2, '2024-08-13', 0, '09:00:00'),
(3, 3, '2024-08-14', 1, '10:00:00'),
(4, 4, '2024-08-15', 1, '11:00:00'),
(5, 5, '2024-08-16', 0, '12:00:00'),
(6, 6, '2024-08-17', 1, '01:00:00');

INSERT INTO notifications (student_id, teacher_id, message, sent_at) VALUES
(1, 1, 'Assignment due next week', '2024-08-12 09:00:00'),
(2, 2, 'Class canceled', '2024-08-13 10:00:00'),
(3, 3, 'New lecture materials available', '2024-08-14 11:00:00');
