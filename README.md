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

## Setup

1. Clone the repository.
2. Create and activate a Python virtual environment.
	If Policy related error occurs:
		Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
3. Install dependencies:  
	 `pip install -r requirements.txt`
4. Run migrations:  
	 `python backend/manage.py migrate`
5. Start the server:  
	 `python backend/manage.py runserver`
6. Start at Login through frontent/main.py
	 `python .\frontend\main.py`