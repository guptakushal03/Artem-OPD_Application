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
            patient = Patient(
                name=request.form['name'],
                gender=request.form['gender'],
                age=int(request.form['age']),
                phone=request.form['phone'],
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
            patient_id = int(request.form['patient_id'])
            patient = Patient.query.get_or_404(patient_id)
            
            # Business Rule: Patient must be Active
            if not patient.is_active():
                flash('Cannot create appointment for inactive patient!', 'danger')
                return redirect(url_for('create_appointment'))
            
            appointment_datetime = datetime.strptime(
                request.form['appointment_datetime'], 
                '%Y-%m-%dT%H:%M'
            )
            
            # Business Rule: Appointment cannot be in the past
            if appointment_datetime < datetime.now():
                flash('Appointment cannot be scheduled in the past!', 'danger')
                return redirect(url_for('create_appointment'))
            
            appointment = Appointment(
                patient_id=patient_id,
                doctor_name=request.form['doctor_name'],
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

# ============= CONSULTATION ROUTES =============

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
            
            consultation = Consultation(
                appointment_id=appointment_id,
                patient_id=appointment.patient_id,
                vitals_1=request.form['vitals_1'],
                vitals_2=request.form['vitals_2'],
                notes=request.form['notes'],
                status='Draft'
            )
            db.session.add(consultation)
            db.session.commit()
            flash('Consultation created successfully!', 'success')
            return redirect(url_for('today_appointments'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating consultation: {str(e)}', 'danger')
    
    # Validation before showing form
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