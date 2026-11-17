# 🎓 Examination Management Portal

A role-based web application developed using **Flask** for managing examination activities in educational institutions. The application allows **Admins**, **Examiners**, and **Students** to manage courses, examinations, examiner assignments, examination slots, bookings, and evaluation records through separate dashboards.

This project was developed as part of the **Modern Application Development-I (MAD-I)** course under the **IIT Madras BS Degree Programme**.

---

## 🚀 Features

### 👨‍💼 Admin
- Secure Login
- Dashboard with examination statistics
- Add, Edit and Delete Courses
- Create and Manage Examinations
- Create and Manage Examination Rubrics
- Approve and Deactivate Examiners
- Assign Examiners to Examinations
- Configure Examination Timelines
- Open and Close Slot Creation and Student Booking
- View Students, Examiners, Examinations and Slots
- View and Manage Examination Bookings
- Search Students, Examiners, Examinations and Bookings
- Reschedule Examination Bookings
- Manage Examination Results

### 👨‍🏫 Examiner
- Register and Login
- Admin Approval Required
- Update Examiner Profile
- View Assigned Examinations
- Create Examination Slots
- Update and Delete Slots Before Booking Starts
- View Students Booked for Assigned Slots
- Evaluate Students Using Examination Rubrics
- Submit Marks and Remarks
- View Evaluation Status

### 🎓 Student
- Register and Login
- Update Student Profile
- View Available Examinations
- Search and Browse Examinations
- View Available Examination Slots
- Book Examination Slots
- Cancel Bookings Before the Deadline
- View Booking Status
- View Upcoming Examination Schedule
- View Booking History
- View Published Results and Feedback

---

## 🔒 Security Features

- Password Hashing
- Flask-Login Authentication
- Role-Based Access Control
- Session Management
- Admin, Examiner and Student Route Protection
- Examiner Approval Workflow
- Backend Form Validation
- CSRF Protection
- Duplicate Examination Booking Prevention
- Slot Capacity Validation
- Examiner Ownership Validation During Evaluation
- Access Restrictions for Deactivated Users

---

## 🛠️ Tech Stack

- Python
- Flask
- Flask-SQLAlchemy
- Flask-Login
- SQLite
- Jinja2
- HTML5
- CSS3
- Bootstrap 5
- Chart.js

---

## 📂 Project Structure

```text
Examination-Management-App/
│
├── app.py
├── config.py
├── extensions.py
├── requirements.txt
├── README.md
├── create_admin.py
├── seed.py
├── seed_admin.py
├── test_api.py
│
├── models/
│   ├── __init__.py
│   ├── user.py
│   └── examination.py
│
├── routes/
│   ├── admin/
│   ├── examiner/
│   ├── student/
│   └── api/
│
├── services/
│   ├── booking_service.py
│   ├── evaluation_service.py
│   └── slot_service.py
│
├── templates/
│   ├── admin/
│   ├── examiner/
│   ├── student/
│   ├── auth/
│   ├── base.html
│   └── index.html
│
├── static/
│   └── css/
│       └── style.css
│
├── utils/
│   └── decorators.py
│
└── instance/
    └── examination.db
```

---

## ⚙️ Installation

### Clone the repository

```bash
git clone https://github.com/24f2003494/Examination-Management-App
```

### Move into the project directory

```bash
cd Examination-Management-App
```

### Create a virtual environment

```bash
python -m venv venv
```

### Activate the virtual environment

Windows:

```bash
venv\Scripts\activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run the application

```bash
python app.py
```

Open your browser and visit:

```text
http://127.0.0.1:5000
```

The SQLite database and its tables are created programmatically by the application.

---

## 👤 Default Admin Account

The administrator account is created programmatically using the admin creation script. Admin registration is not available through the application.

Run the following command if the admin account has not yet been created:

```bash
python create_admin.py
```

Use the credentials configured in the project to log in as Admin.
email: admin123@gmail.com
password:admin@123

---

## 🗄️ Database

The application uses **SQLite** for data storage and **Flask-SQLAlchemy** for database operations.

The database includes models and records for:

- User
- Course
- Examination
- Examination Rubric
- Examiner Profile
- Examination Slot
- Booking
- Evaluation
- System Timeline
- Examiner Assignment
- Rubric Evaluation

The database tables are created programmatically through the Flask application.

---

## 🌐 REST API

The project includes JSON API resources for managing examination-related data.

### Available API Resources

| Resource | Endpoint | Supported Methods |
|---|---|---|
| Examinations | `/api/examinations/` | GET, POST |
| Examination Details | `/api/examinations/<id>` | GET, PUT, DELETE |
| Examiners | `/api/examiners/` | GET, POST |
| Examiner Details | `/api/examiners/<id>` | GET, PUT, DELETE |
| Students | `/api/students/` | GET, POST |
| Student Details | `/api/students/<id>` | GET, PUT, DELETE |
| Examination Slots | `/api/slots/` | GET, POST |
| Slot Details | `/api/slots/<id>` | GET, PUT, DELETE |
| Bookings | `/api/bookings/` | GET, POST |
| Booking Details | `/api/bookings/<id>` | GET, PUT, DELETE |

API responses are returned in JSON format. Access to protected resources depends on authentication and user roles.

---

## 📊 Additional Features

- Separate Dashboards for Admin, Examiner and Student
- Dashboard Statistics and Charts
- Examination Timeline Management
- Slot Capacity Management
- Automatic Slot Closure When Capacity Is Reached
- Booking History and Status Tracking
- Rubric-Based Student Evaluation
- Result Publication
- Examination Search and Filtering
- Responsive Bootstrap Interface
- Modular Flask Application Using Blueprints
- Flash Messages
- API Integration Tests

---

## 👩‍💻 Developer

Gazal
BS Degree in Data Science and Applications

Indian Institute of Technology Madras

---

## 📖 Course

**Modern Application Development – I (MAD-I)**

IIT Madras BS Degree Programme

---

## 🎥 Project Demonstration

Demo Video: **https://drive.google.com/file/d/1xZP_pameTm8GLPq6MW4Ow8stcoTXM40V/view?usp=sharing**

