from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, Patient, Appointment, Consultation
from config import Config
from datetime import datetime, date
from sqlalchemy import or_

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return redirect(url_for('list_patients'))

@app.route('/patients')
def list_patients():
    search = request.args.get('search', '')
    if search:
        patients = Patient.query.filter(
            or_(Patient.name.like(f'%{search}%'), 
                Patient.phone.like(f'%{search}%'))
        ).all()
    else:
        patients = Patient.query.all()
    return render_template('patients.html', patients=patients, search=search)

@app.route('/patients/create', methods=['GET', 'POST'])
def create_patient():
    if request.method == 'POST':
        try:
            # Validate name
            name = request.form.get('name', '').strip()
            if not name:
                flash('Name is required!', 'danger')
                return render_template('patient_form.html')
            if len(name) < 2:
                flash('Name must be at least 2 characters!', 'danger')
                return render_template('patient_form.html')
            if len(name) > 100:
                flash('Name is too long (max 100 characters)!', 'danger')
                return render_template('patient_form.html')
            
            # Validate gender
            gender = request.form.get('gender', '').strip()
            valid_genders = ['Male', 'Female', 'Other']
            if gender not in valid_genders:
                flash('Please select a valid gender!', 'danger')
                return render_template('patient_form.html')
            
            # Validate age
            age_str = request.form.get('age', '').strip()
            if not age_str:
                flash('Age is required!', 'danger')
                return render_template('patient_form.html')
            
            try:
                age = int(age_str)
            except ValueError:
                flash('Age must be a valid number!', 'danger')
                return render_template('patient_form.html')
            
            if age < 0 or age > 150:
                flash('Age must be between 0 and 150!', 'danger')
                return render_template('patient_form.html')
            
            # Validate phone
            phone = request.form.get('phone', '').strip()
            if not phone:
                flash('Phone number is required!', 'danger')
                return render_template('patient_form.html')
            
            # Remove common separators and validate digits
            phone_digits = ''.join(c for c in phone if c.isdigit())
            if len(phone_digits) < 10 or len(phone_digits) > 15:
                flash('Phone number must be 10-15 digits!', 'danger')
                return render_template('patient_form.html')
            
            # All validations passed - create patient
            patient = Patient(
                name=name,
                gender=gender,
                age=age,
                phone=phone,
                status='Active'
            )
            db.session.add(patient)
            db.session.commit()
            flash('Patient created successfully!', 'success')
            return redirect(url_for('list_patients'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating patient: {str(e)}', 'danger')
            return render_template('patient_form.html')
    
    return render_template('patient_form.html')

@app.route('/appointments')
def list_appointments():
    appointments = Appointment.query.all()
    return render_template('appointments.html', appointments=appointments)

@app.route('/appointments/today')
def today_appointments():
    today = date.today()
    appointments = Appointment.query.filter(
        db.func.date(Appointment.appointment_datetime) == today
    ).all()
    return render_template('today_appointments.html', appointments=appointments, today=today)

@app.route('/appointments/create', methods=['GET', 'POST'])
def create_appointment():
    if request.method == 'POST':
        try:
            # Validate patient_id exists and is valid
            patient_id_str = request.form.get('patient_id', '').strip()
            if not patient_id_str:
                flash('Please select a patient!', 'danger')
                patients = Patient.query.filter_by(status='Active').all()
                return render_template('appointment_form.html', patients=patients)
            
            # Validate patient_id is a number
            try:
                patient_id = int(patient_id_str)
            except ValueError:
                flash('Invalid patient selection!', 'danger')
                patients = Patient.query.filter_by(status='Active').all()
                return render_template('appointment_form.html', patients=patients)
            
            # Validate patient exists
            patient = Patient.query.get(patient_id)
            if not patient:
                flash('Patient not found!', 'danger')
                patients = Patient.query.filter_by(status='Active').all()
                return render_template('appointment_form.html', patients=patients)
            
            # Business Rule: Patient must be Active
            if not patient.is_active():
                flash('Cannot create appointment for inactive patient!', 'danger')
                patients = Patient.query.filter_by(status='Active').all()
                return render_template('appointment_form.html', patients=patients)
            
            # Validate doctor name
            doctor_name = request.form.get('doctor_name', '').strip()
            if not doctor_name:
                flash('Doctor name is required!', 'danger')
                patients = Patient.query.filter_by(status='Active').all()
                return render_template('appointment_form.html', patients=patients)
            
            if len(doctor_name) > 100:
                flash('Doctor name is too long (max 100 characters)!', 'danger')
                patients = Patient.query.filter_by(status='Active').all()
                return render_template('appointment_form.html', patients=patients)
            
            # Validate appointment datetime
            appointment_datetime_str = request.form.get('appointment_datetime', '').strip()
            if not appointment_datetime_str:
                flash('Appointment date and time is required!', 'danger')
                patients = Patient.query.filter_by(status='Active').all()
                return render_template('appointment_form.html', patients=patients)
            
            try:
                appointment_datetime = datetime.strptime(
                    appointment_datetime_str, 
                    '%Y-%m-%dT%H:%M'
                )
            except ValueError:
                flash('Invalid date/time format!', 'danger')
                patients = Patient.query.filter_by(status='Active').all()
                return render_template('appointment_form.html', patients=patients)
            
            # Business Rule: Appointment cannot be in the past
            if appointment_datetime < datetime.now():
                flash('Appointment cannot be scheduled in the past!', 'danger')
                patients = Patient.query.filter_by(status='Active').all()
                return render_template('appointment_form.html', patients=patients)
            
            # All validations passed - create appointment
            appointment = Appointment(
                patient_id=patient_id,
                doctor_name=doctor_name,
                appointment_datetime=appointment_datetime,
                status='Scheduled'
            )
            db.session.add(appointment)
            db.session.commit()
            flash('Appointment created successfully!', 'success')
            return redirect(url_for('today_appointments'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating appointment: {str(e)}', 'danger')
            patients = Patient.query.filter_by(status='Active').all()
            return render_template('appointment_form.html', patients=patients)
    
    # GET request - show form
    patients = Patient.query.filter_by(status='Active').all()
    return render_template('appointment_form.html', patients=patients)

@app.route('/consultations/new/<int:appointment_id>', methods=['GET', 'POST'])
def create_consultation(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    
    if request.method == 'POST':
        try:
            # Business Rule: Appointment must be Scheduled
            if not appointment.is_scheduled():
                flash('Consultation can only be created for scheduled appointments!', 'danger')
                return redirect(url_for('today_appointments'))
            
            # Business Rule: Only one consultation per appointment
            if appointment.consultation:
                flash('Consultation already exists for this appointment!', 'danger')
                return redirect(url_for('today_appointments'))
            
            # Business Rule: Patient must be Active
            if not appointment.patient.is_active():
                flash('Patient is inactive!', 'danger')
                return redirect(url_for('today_appointments'))
            
            # Get and validate form data (handle None/empty values)
            vitals_1 = request.form.get('vitals_1', '').strip()
            vitals_2 = request.form.get('vitals_2', '').strip()
            notes = request.form.get('notes', '').strip()
            
            # Optional: Validate max lengths
            if vitals_1 and len(vitals_1) > 100:
                flash('Vitals 1 is too long (max 100 characters)!', 'danger')
                return render_template('consultation_form.html', appointment=appointment)
            
            if vitals_2 and len(vitals_2) > 100:
                flash('Vitals 2 is too long (max 100 characters)!', 'danger')
                return render_template('consultation_form.html', appointment=appointment)
            
            if notes and len(notes) > 1000:
                flash('Notes are too long (max 1000 characters)!', 'danger')
                return render_template('consultation_form.html', appointment=appointment)
            
            # Create consultation with validated data
            consultation = Consultation(
                appointment_id=appointment_id,
                patient_id=appointment.patient_id,
                vitals_1=vitals_1 if vitals_1 else None,
                vitals_2=vitals_2 if vitals_2 else None,
                notes=notes if notes else None,
                status='Draft'
            )
            db.session.add(consultation)
            db.session.commit()
            flash('Consultation created successfully!', 'success')
            return redirect(url_for('today_appointments'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating consultation: {str(e)}', 'danger')
            return render_template('consultation_form.html', appointment=appointment)
    
    # GET request - Validation before showing form
    if not appointment.is_scheduled():
        flash('Consultation can only be created for scheduled appointments!', 'danger')
        return redirect(url_for('today_appointments'))
    
    if appointment.consultation:
        flash('Consultation already exists for this appointment!', 'danger')
        return redirect(url_for('today_appointments'))
    
    return render_template('consultation_form.html', appointment=appointment)

@app.route('/consultations/complete/<int:id>', methods=['POST'])
def complete_consultation(id):
    try:
        consultation = Consultation.query.get_or_404(id)
        
        # Business Rule: Can only complete Draft consultations
        if not consultation.is_draft():
            flash('Consultation is already completed!', 'danger')
            return redirect(url_for('today_appointments'))
        
        # Workflow: Mark consultation and appointment as completed
        consultation.status = 'Completed'
        consultation.appointment.status = 'Completed'
        
        db.session.commit()
        flash('Consultation marked as completed!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error completing consultation: {str(e)}', 'danger')
    
    return redirect(url_for('today_appointments'))

@app.route('/patients/<int:id>/consultations')
def patient_consultations(id):
    patient = Patient.query.get_or_404(id)
    consultations = Consultation.query.filter_by(
        patient_id=id, 
        status='Completed'
    ).all()
    return render_template('patient_consultations.html', patient=patient, consultations=consultations)

if __name__ == '__main__':
    app.run(debug=True)