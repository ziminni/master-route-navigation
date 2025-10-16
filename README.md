# CISC Virtual Hub (V-Hub)

**College of Information Sciences and Computing Virtual Hub System**  
ITSD81 Desktop Application Development Project  
Information Technology Department  
Central Mindanao University  
1st Semester, S.Y. 2025 - 2026

## Introduction

The College of Information Sciences and Computing (CISC) lacks a centralized student information and communication platform. Students and faculty often rely on social media for updates, leading to inconsistent information and distractions. The CISC Virtual Hub (V-Hub) is designed to provide a comprehensive digital hub for students and faculty, enhancing connectivity and interactivity within the college.

V-Hub aims to centralize academic schedules, organization events, house activities, and communication, supporting student progress tracking, bulletin publishing, project showcasing, and more. This project is developed by ITSD81 students as a semester-long laboratory project.

## Objectives

- Establish a centralized student information platform for CISC faculty and students.
- Facilitate collaborative, modular desktop application development.
- Enable faculty to distribute classroom content and monitor academic records internally.
- Centralize academic schedules, events, and activities for improved coordination.
- Streamline student progress tracking, communication, and bulletin publishing.
- Support project showcasing and capstone management within the college.

## System Overview

CISC V-Hub is a desktop application acting as an academic organizer, communication center, and gamification hub for CISC. It is intended for students, faculty, and staff, with future versions planned for mobile and web platforms.

## Architecture

- **Backend (`backend/`)**:  
	Built with Django, the backend provides RESTful APIs, business logic, and data management. It includes modular apps for each feature (Academics, Announcements, Appointments, etc.), a core configuration, shared utilities, middleware, and API permissions.
- **Frontend (`frontend/`)**:  
	Developed using PyQt6, the desktop frontend interacts with the backend via APIs and provides a rich user interface. Qt Designer is used for GUI layouts.
- **Database**:  
	PostgreSQL is the main production database for scalability and robustness. SQLite3 is used for local development and testing.
- **Virtual Environment (`venv/`)**:  
	All dependencies are managed in a Python virtual environment for consistency and isolation.

### Key Backend Folders

- `apps/`: Modular Django apps for each system feature.
- `core/`: Project configuration, settings, URL routing, and server entry points (`asgi.py`, `wsgi.py`).
- `common/`: Shared constants, exceptions, services, and utilities.
- `middleware/`: Custom middleware for request/response processing (e.g., logging, authentication).
- `api/`: API-specific logic, such as permission classes.
- `tests/`: Project-wide and app-specific tests.
- `manage.py`: Django’s command-line utility for running the server, migrations, and other tasks.

## System Modules

V-Hub includes modules for:
- User Profile & Resume
- Faculty-Classroom System (Internal LMS)
- Academic Schedule & Organizer
- Academic Progress Tracker
- Student Organization Directory & Membership
- Organization Event Lifecycle & Attendance
- CISC Calendar System
- Announcement Board & News Feed
- Internal Messaging & Inquiry Center
- House Management & Points System
- Faculty Appointment & Consultation Scheduler
- Document Vault & Form Repository
- Suggestion, Complaint, & Feedback Box
- Project & Competition Showcase
- Student Services & External Link Directory
- Admin Insights Dashboard

## Tools and Technologies

- **Python 3.10+**: Main programming language for backend and desktop frontend.
- **Django**: Backend framework for APIs and logic.
- **Django REST Framework**: For building RESTful APIs.
- **PyQt6**: Desktop GUI framework.
- **Qt Designer**: For designing GUI layouts.
- **PostgreSQL**: Main production database.
- **SQLite3**: Local development database.
- **Other Libraries**: Matplotlib (visualization), Requests, python-dotenv, etc.

## Quick Start

### First Time Setup (Automated)

Run the automated setup script that will:
- Create virtual environment
- Install all dependencies
- Run database migrations
- Create default users (admin, student, staff, faculty)

```powershell
python.exe .\backend\script.py
```

**Default Users Created:**
- **Admin**: username: `admin`, password: `admin123`
- **Student**: username: `Marcus`, password: `password123`
- **Staff**: username: `Donald`, password: `password123`
- **Faculty**: username: `Kim`, password: `password123`

### Running the Application

Launch both backend and frontend with a single command:

```powershell
python.exe launch.py
```

This will:
1. Start the Django backend server at `http://127.0.0.1:8000/`
2. Wait 3 seconds for backend initialization
3. Launch the PyQt6 desktop application
4. Monitor both processes (close frontend window or press Ctrl+C to stop all)

---

## Manual Setup (Alternative)

If you prefer to set up manually:

### 1. Clone the Repository
```powershell
git clone <repository-url>
cd master-merging
```

### 2. Create Virtual Environment
```powershell
python.exe -m venv .venv
```

### 3. Activate Virtual Environment
```powershell
.\.venv\Scripts\activate
```

**Note:** If you encounter a policy error:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### 4. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 5. Run Database Migrations
```powershell
cd backend
python.exe manage.py makemigrations
python.exe manage.py migrate
cd ..
```

### 6. Create Superuser (Optional)
```powershell
cd backend
python.exe manage.py createsuperuser
cd ..
```

### 7. Start Backend Server
```powershell
cd backend
python.exe manage.py runserver
```

### 8. Start Frontend Application (in new terminal)
```powershell
.\.venv\Scripts\activate
cd frontend
python.exe main.py
```

---

## Useful Commands

### Reset Database & Migrations
To completely reset your database and start fresh:
```powershell
python.exe .\backend\script.py
```
This will delete `db.sqlite3` and recreate everything from scratch.

### Access Django Admin Panel
1. Start the backend server
2. Navigate to `http://127.0.0.1:8000/admin/`
3. Login with admin credentials

### Run Backend Only
```powershell
.\.venv\Scripts\python.exe .\backend\manage.py runserver
```

### Run Frontend Only
```powershell
.\.venv\Scripts\python.exe .\frontend\main.py
```

### Run Tests
```powershell
cd backend
.\.venv\Scripts\python.exe manage.py test
```

---

## Project Structure

```
root/
├── backend/
│   ├── api/
│   ├── apps/
│   │   ├── Academics/
│   │   ├── Admin/
│   │   ├── Announcements/
│   │   ├── Appointments/
│   │   ├── Calendar/
│   │   ├── Dashboard/
│   │   ├── Documents/
│   │   ├── Feedback/
│   │   ├── House/
│   │   ├── Links/
│   │   ├── Messaging/
│   │   ├── Organizations/
│   │   ├── Showcase/
│   │   └── Users/
│   ├── common/
│   ├── config/
│   ├── core/
│   ├── docs/
│   ├── middleware/
│   ├── tests/
│   ├── db.sqlite3
│   ├── manage.py
│   └── script.py
├── frontend/
│   ├── assets/
│   ├── controller/
│   ├── database/
│   ├── docs/
│   ├── Mock/
│   ├── model/
│   ├── router/
│   ├── services/
│   ├── ui/
│   ├── utils/
│   ├── views/
│   ├── widgets/
│   └── main.py
├── launch.py
├── README.md
└── requirements.txt
```