# OPD Management System

## Overview
A simple outpatient department (OPD) management system built with Flask, demonstrating status-driven workflows and relational data modeling.

## Features
- Patient management (Active/Inactive status)
- Appointment scheduling with validations
- Consultation workflow with status transitions
- Server-side business rule enforcement

## Table Relationships
```
Patient (1) ----< (N) Appointment (1) ---- (1) Consultation
```

- One patient can have multiple appointments
- Each appointment belongs to one patient
- Each appointment can have one consultation
- Each consultation is linked to both appointment and patient

## Status & Workflow Rules

### Patient Status
- **Active**: Can book appointments
- **Inactive**: Cannot book appointments

### Appointment Status
- **Scheduled** (default): Initial state
- **Completed**: Set when consultation is completed
- **Cancelled**: Manual cancellation

### Consultation Status
- **Draft** (default): Initial state, editable
- **Completed**: Final state, marks appointment as completed

### Business Rules
1. Appointments cannot be created in the past
2. Appointments can only be created for Active patients
3. Consultations can only be created for Scheduled appointments
4. Only one consultation allowed per appointment
5. When consultation is marked Completed, appointment automatically becomes Completed

## How to Run Locally

### Prerequisites
- Python 3.9+
- MariaDB or MySQL

### Setup Database
```sql
CREATE DATABASE opd_db;
```

### Install Dependencies
```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Configure Database
Edit `config.py` with your database credentials:
```python
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://username:password@localhost/opd_db'
```

### Run Development Server
```bash
python app.py
```

Visit: http://localhost:5000

### Run with Gunicorn (Production)
```bash
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

## Application Flow

1. **Create Patient** → Patient is Active by default
2. **Book Appointment** → Must select Active patient, cannot be in past
3. **View Today's Appointments** → See all appointments for current date
4. **Start Consultation** → Only for Scheduled appointments
5. **Mark Consultation Complete** → Automatically completes the appointment
6. **View Patient Consultations** → See all completed consultations per patient

## Project Structure
```
opd_application/
├── app.py              # Main Flask application
├── models.py           # Database models
├── config.py           # Configuration
├── requirements.txt    # Python dependencies
├── templates/          # HTML templates
│   ├── base.html
│   ├── patients.html
│   ├── patient_form.html
│   ├── appointment_form.html
│   ├── today_appointments.html
│   ├── consultation_form.html
│   └── patient_consultations.html
└── README.md
```