from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
import os
from werkzeug.utils import secure_filename
import traceback
import secrets
from datetime import datetime, timedelta


app = Flask(__name__)
app.config.from_object(Config)

mysql = MySQL(app)
mail = Mail(app)

app.config['UPLOAD_FOLDER'] = 'uploads'  # Define the upload folder
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit file size to 16MB


os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/contact_us')
def contact_us():
    return render_template('contact-us.html')

@app.route('/our_gallery')
def our_gallery():
    return render_template('our-gallery.html')

@app.route('/select_role')
def select_role():
    return render_template('select_role.html')

@app.route('/therapist-terms')
def therapist_terms():
    return render_template('Therapist_Terms.html')

@app.route('/dashboardtest')
def dashboard():
    return render_template('vinay.html')

from flask import session, redirect, url_for

@app.route('/logout')
def logout():
    session.clear()  # or use session.pop('user_id', None) if you want to keep other data
    return redirect(url_for('home'))  # redirect to your login page



@app.route('/forget_password', methods=['GET', 'POST'])
def forget_password():
    if request.method == 'POST':
        email = request.form['email']
        user_type = request.form['user_type']  # 'patient' or 'doctor'

        cur = mysql.connection.cursor()

        # ✅ Check if the email belongs to a Patient or Doctor
        if user_type == 'patient':
            cur.execute("SELECT id, patient_name FROM patients WHERE email = %s", (email,))
            user = cur.fetchone()
            reset_route = 'reset_password'
        else:
            cur.execute("SELECT id, doctor_name FROM doctors WHERE email = %s", (email,))
            user = cur.fetchone()
            reset_route = 'doctor_reset_password'

        if not user:
            flash("No account found with this email.", "danger")
            return redirect(url_for('forget_password'))

        user_id, user_name = user

        # ✅ Generate a unique token
        reset_token = secrets.token_urlsafe(32)

        # ✅ Save token in the database
        if user_type == 'patient':
            cur.execute("UPDATE patients SET reset_token = %s WHERE id = %s", (reset_token, user_id))
        else:
            cur.execute("UPDATE doctors SET reset_token = %s WHERE id = %s", (reset_token, user_id))

        mysql.connection.commit()
        cur.close()

        # ✅ Generate Reset Link
        reset_url = url_for(reset_route, token=reset_token, _external=True)

        # ✅ Send Email with Reset Link
        msg = Message(
            subject="Password Reset Request",
            sender="vinaykakad56@gmail.com",
            recipients=[email]
        )
        msg.html = render_template("reset_email.html", user_name=user_name, reset_link=reset_url)

        try:
            mail.send(msg)
            flash("A password reset link has been sent to your email.", "success")
        except Exception as e:
            flash(f"Error sending email: {e}", "danger")

        return redirect(url_for('login' if user_type == 'patient' else 'doctor_login'))

    return render_template('forget_password.html')


# ✅ Reset Password for Patients
@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM patients WHERE reset_token = %s", (token,))
    user = cur.fetchone()

    if not user:
        flash("Invalid or expired reset token.", "danger")
        return redirect(url_for('forget_password'))

    if request.method == 'POST':
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        # ✅ Update password & clear token
        cur.execute("UPDATE patients SET password = %s, reset_token = NULL WHERE id = %s", 
                    (hashed_password, user[0]))
        mysql.connection.commit()
        cur.close()

        flash("Password reset successful! You can now log in.", "success")
        return redirect(url_for('login'))

    return render_template('reset_password.html')


# ✅ Reset Password for Doctors
@app.route('/doctor_reset_password/<token>', methods=['GET', 'POST'])
def doctor_reset_password(token):
    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM doctors WHERE reset_token = %s", (token,))
    user = cur.fetchone()

    if not user:
        flash("Invalid or expired reset token.", "danger")
        return redirect(url_for('forget_password'))

    if request.method == 'POST':
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        # ✅ Update password & clear token
        cur.execute("UPDATE doctors SET password = %s, reset_token = NULL WHERE id = %s", 
                    (hashed_password, user[0]))
        mysql.connection.commit()
        cur.close()

        flash("Password reset successful! You can now log in.", "success")
        return redirect(url_for('doctor_login'))

    return render_template('reset_password.html')







disorder_to_specialist = {
    "Stuttering": ["SLP"],  # Updated to match the database
    "Voice Disorder": ["ENT Specialist"],  # Updated to match the database
    "Neurological Speech Issue": ["Neurologist"],
    "Pediatric Speech Delay": ["Pediatrician"],
    "Autism Communication Issue": ["Psychologist"],
    "Post-Surgery Recovery": ["Rehabilitation Specialist"],
    "Hearing and Speech Issue": ["Audiologist"],
}

import re

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        try:
            print("➡️ Signup Form Submitted")
            print(request.form)  # Debug: Print received form data

            # Retrieve form data
            patient_name = request.form['patient-name']
            age = request.form['age']
            gender = request.form['gender']
            parents_name = request.form['parents-name']
            contact_no = request.form['contact-no']
            email = request.form['email']
            password = request.form['password']
            address = request.form['address']
            disorder = request.form['disorder']

            print(f"📌 DEBUG: Contact No = {contact_no}, Length = {len(contact_no)}")

            # 🚨 Validate Contact Number Length
            if not contact_no.isdigit():  
                flash("⚠️ Contact number should contain only digits.", "danger")
                return redirect(url_for('signup'))

            if len(contact_no) < 10 or len(contact_no) > 15:  
                flash("⚠️ Contact number should be between 10 to 15 digits.", "danger")
                return redirect(url_for('signup'))

            # Hash password before storing
            hashed_password = generate_password_hash(password)

            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO patients (patient_name, age, gender, parents_name, contact_no, email, password, address, disorder)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (patient_name, age, gender, parents_name, contact_no, email, hashed_password, address, disorder))

            mysql.connection.commit()
            cur.close()

            flash("✅ Signup successful! Please log in.", "success")
            return redirect(url_for('login'))

        except Exception as e:
            print(f"❌ Error: {str(e)}")  # Debugging
            flash(f"⚠️ Error: {str(e)}", "danger")
            return redirect(url_for('signup'))

    return render_template('signup.html')





# Doctor Signup
@app.route('/doctor_signup', methods=['GET', 'POST'])
def doctor_signup():
    if request.method == 'POST':
        clinic_name = request.form['clinic_name']
        doctor_name = request.form['doctor_name']
        age = request.form['age']
        gender = request.form['gender']
        specialty = request.form['specialty']
        experience = request.form['experience']
        license_certificate_no = request.form['license_certificate_no']
        address = request.form['address']
        phone = request.form['contact-no']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])  # Hashing Password
        degree = request.form.get('degree')  # Fetch degree from form
        fees = request.form.get('fees')  # Fetch fees from form

        try:
            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO doctors (clinic_name, doctor_name, age, gender, specialty, experience, license_certificate_no, address, phone, email, password, degree, fees) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (clinic_name, doctor_name, age, gender, specialty, experience, license_certificate_no, address, phone, email, password, degree, fees))
            mysql.connection.commit()
            cur.close()

            flash("✅ Signup Successful! Redirecting to Select Doctor...", "success")
            print("✅ Doctor registered successfully! Redirecting to login...")  # Debugging
            return redirect(url_for('doctor_login'))  # Redirect to Doctor Login Page

        except Exception as e:
            print(f"❌ Error during doctor signup: {e}")  # Debugging
            flash(f"❌ Error: {e}", "danger")
            return redirect(url_for('doctor_signup'))  # Redirect back to signup page on error

    return render_template('doctor_signup.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM patients WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()

        if user:
            stored_password = user[7]  # Assuming the password is in the 7th column (index 6)
            
            if check_password_hash(stored_password, password):  # Validate password
                session['loggedin'] = True  # Set session variable
                session['role'] = 'patient'  # Set role
                session['user_id'] = user[0]  # Store user ID in session
                session['user_name'] = user[1]  # Store username for display
                session['email'] = email  # Store email in session

                flash("✅ Login successful!", "success")
                print("✅ Login successful! Redirecting to select_doctor...")  # Debugging
                return redirect(url_for('patient_dashboard'))  # Redirect to Select Doctor Page
            
            else:
                flash("⚠️ Incorrect password. Try again!", "danger")
        else:
            flash("⚠️ Email not found. Please sign up!", "danger")

    return render_template('login.html')  # Reload login page if login fails



@app.route('/doctor_login', methods=['GET', 'POST'])
def doctor_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        try:
            cur = mysql.connection.cursor()
            cur.execute("SELECT id, doctor_name, password FROM doctors WHERE email = %s", (email,))
            doctor = cur.fetchone()
            cur.close()
        except Exception as e:
            print(f"❌ Database Error: {e}")
            flash('An error occurred. Please try again later.', 'danger')
            return render_template('doctor_login.html')

        if doctor:
            doctor_id, doctor_name, stored_password = doctor

            print(f"✅ Doctor Found: {doctor}")
            print(f"🔍 Stored Password: {stored_password}")
            print(f"🔍 Entered Password: {password}")

            if stored_password and check_password_hash(stored_password, password):
                session['loggedin'] = True
                session['email'] = email
                session['role'] = 'doctor'
                session['doctor_id'] = doctor_id
                session['doctor_name'] = doctor_name
                print("✅ Login Successful!")
                return redirect(url_for('doctor_dashboard'))
            else:
                print("❌ Invalid Password")
                flash('Invalid password. Please try again.', 'danger')
        else:
            print("❌ Doctor Not Found")
            flash('Doctor not found. Please sign up.', 'danger')

    return render_template('doctor_login.html')


# Select Doctor Based on Disease
@app.route('/select_doctor', methods=['GET'])
def select_doctor():
    if 'loggedin' not in session or session['role'] != 'patient':
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()

    # Fetch the patient's disorder
    cur.execute("SELECT disorder FROM patients WHERE email = %s", (session['email'],))
    patient_disorder = cur.fetchone()

    if patient_disorder:
        disorder = patient_disorder[0]
        print(f"DEBUG: Patient's Disorder = {disorder}")  # Debugging

        # Get the relevant specializations for the patient's disorder
        specializations = disorder_to_specialist.get(disorder, [])
        print(f"DEBUG: Mapped Specializations = {specializations}")  # Debugging

        if specializations:
            # Fetch doctors whose specialty matches the relevant specializations
            query = "SELECT id, doctor_name, specialty, experience, degree,fees FROM doctors WHERE specialty IN %s"
            print(f"DEBUG: Executing Query = {query % (tuple(specializations),)}")  # Debugging
            cur.execute(query, (tuple(specializations),))
            doctors = cur.fetchall()
            print(f"DEBUG: Doctors Found = {doctors}")  # Debugging
        else:
            doctors = []
            flash("No specializations found for your disorder.", "warning")
    else:
        doctors = []
        flash("No disorder found for the patient.", "danger")

    cur.close()

    return render_template('select_doctor.html', doctors=doctors)

@app.route('/upload_plan/<int:appointment_id>', methods=['POST'])
def upload_plan(appointment_id):  # Change 'patient_id' to 'appointment_id'
    if 'loggedin' not in session or session['role'] != 'doctor':
        return redirect(url_for('login'))

    # ✅ Fetch the correct patient_id from appointments table
    cur = mysql.connection.cursor()
    cur.execute("SELECT patient_id FROM appointment_requests WHERE id = %s", (appointment_id,))
    actual_patient_id = cur.fetchone()

    if not actual_patient_id:
        flash("🚨 ERROR: No patient found for this appointment!", "danger")
        return redirect(url_for('doctor_dashboard'))

    patient_id = actual_patient_id[0]  # Extract the patient_id
    print(f"✅ DEBUG: Uploading for Patient ID {patient_id}")

    # ✅ Now continue uploading with the correct patient_id
    if 'therapy_plan' not in request.files:
        flash("No file uploaded!", "danger")
        return redirect(url_for('doctor_dashboard'))

    file = request.files['therapy_plan']
    if file.filename == '':
        flash("No file selected!", "danger")
        return redirect(url_for('doctor_dashboard'))

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    try:
        # ✅ Insert report upload & update report_status
        file.save(file_path)

        cur.execute("""
            INSERT INTO patient_reports (appointment_id, patient_id, doctor_id, file_path)
            VALUES (%s, %s, %s, %s)
        """, (appointment_id, patient_id, doctor_id, file_path))

        # ✅ Update report_status in appointment_requests
        cur.execute("""
            UPDATE appointment_requests 
            SET report_status = 'Uploaded' 
            WHERE id = %s
        """, (appointment_id,))
        mysql.connection.commit()


        flash("Therapy plan uploaded successfully!", "success")
    except Exception as e:
        flash(f"Error uploading file: {e}", "danger")
    finally:
        cur.close()

    return redirect(url_for('doctor_dashboard'))

@app.route('/upload_patient_report/<int:appointment_id>', methods=['POST'])
def upload_patient_report(appointment_id):
    print(f"DEBUG: Uploading report for appointment_id = {appointment_id}")  # Add a debug print statement
    if 'loggedin' not in session or session['role'] != 'patient':
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()

    # ✅ Get patient_id and doctor_id from appointment
    cur.execute("SELECT patient_id, doctor_id FROM appointment_requests WHERE id = %s", (appointment_id,))
    appointment = cur.fetchone()

    if not appointment:
        flash("🚨 ERROR: Appointment not found!", "danger")
        return redirect(url_for('patient_dashboard'))

    patient_id, doctor_id = appointment

    # ✅ Check if file is uploaded
    if 'report_file' not in request.files:
        flash("No file uploaded!", "danger")
        return redirect(url_for('patient_dashboard'))

    file = request.files['report_file']
    if file.filename == '':
        flash("No file selected!", "danger")
        return redirect(url_for('patient_dashboard'))

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    try:
        # ✅ Save the file
        file.save(file_path)
        print(f"DEBUG: File saved at {file_path}")  # Add a debug print statement

        # ✅ Check if a report row already exists
        cur.execute("SELECT id FROM patient_reports WHERE appointment_id = %s", (appointment_id,))
        report = cur.fetchone()

        if report:
            # ✅ Update existing report
            cur.execute("""
                UPDATE patient_reports
                SET file_path = %s, status = 'Uploaded'
                WHERE appointment_id = %s
            """, (file_path, appointment_id))
        else:
            # ✅ Insert new report (only if not inserted already)
            cur.execute("""
                INSERT INTO patient_reports (appointment_id, patient_id, doctor_id, file_path, status)
                VALUES (%s, %s, %s, %s, 'Uploaded')
            """, (appointment_id, patient_id, doctor_id, file_path))

        mysql.connection.commit()
        print("DEBUG: Report uploaded successfully")  # Add a debug print statement

        flash("Report uploaded successfully!", "success")
    except Exception as e:
        flash(f"Error uploading report: {e}", "danger")
    finally:
        cur.close()

    return redirect(url_for('patient_dashboard'))







from flask import send_from_directory

@app.route('/download_plan/<string:plan_name>')
def download_plan(plan_name):
    if 'loggedin' not in session or session['role'] != 'patient':
        return redirect(url_for('login'))

    # Fetch the file path from the database
    cur = mysql.connection.cursor()
    try:
        cur.execute("""
            SELECT file_path
            FROM therapy_plans
            WHERE file_path = %s AND patient_id = %s
        """, (plan_name, session['user_id']))

        file_path = cur.fetchone()[0]
    except Exception as e:
        print(f"DEBUG: Error fetching file path: {e}")
        flash("Error downloading file.", "danger")
        return redirect(url_for('patient_dashboard'))
    finally:
        cur.close()

    # Send the file for download
    return send_from_directory(app.config['UPLOAD_FOLDER'], os.path.basename(file_path), as_attachment=True)


#download report

from flask import send_file, flash, redirect, url_for
import os

@app.route('/download_report/<int:appointment_id>')
def download_report(appointment_id):
    if 'loggedin' not in session or session['role'] != 'doctor':
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT pr.file_path, p.patient_name, ar.disorder 
        FROM patient_reports pr
        JOIN appointment_requests ar ON pr.appointment_id = ar.id
        JOIN patients p ON ar.patient_id = p.id
        WHERE pr.appointment_id = %s
    """, (appointment_id,))
    report = cur.fetchone()
    cur.close()

    if not report:
        flash("Report not found!", "danger")
        return redirect(url_for('doctor_dashboard'))

    file_path, patient_name, disorder = report

    # Ensure the file exists before trying to send it
    if not os.path.exists(file_path):
        flash("File not found!", "danger")
        return redirect(url_for('doctor_dashboard'))

    # Send the file
    return send_file(file_path, as_attachment=True)




# Route to start a session
from datetime import datetime

@app.route('/start_session/<int:appointment_id>', methods=['POST'])
def start_session(appointment_id):
    if 'loggedin' not in session or session['role'] != 'doctor':
        return redirect(url_for('login'))

    meeting_link = request.form.get('meeting_link')

    if not meeting_link:
        flash("Meeting Link is required!", "danger")
        return redirect(url_for('doctor_dashboard'))

    try:
        cur = mysql.connection.cursor()

        print(f"✅ DEBUG: Received appointment_id = {appointment_id}, Type = {type(appointment_id)}")

        # ✅ Fetch appointment details from appointment_requests
        cur.execute("""
            SELECT appointment_date, time_slot, appointment_status
            FROM appointment_requests
            WHERE id = %s
        """, (appointment_id,))
        appointment_data = cur.fetchone()

        if not appointment_data:
            print(f"🚨 ERROR: No appointment found with ID {appointment_id}")
            flash("Invalid appointment ID.", "danger")
            return redirect(url_for('doctor_dashboard'))

        appointment_date, time_slot, current_status = appointment_data

        # ✅ Ensure appointment_date is correctly formatted
        if isinstance(appointment_date, datetime):
            appointment_date = appointment_date.strftime('%Y-%m-%d')

        print(f"✅ DEBUG: appointment_date = {appointment_date}, Type = {type(appointment_date)}")
        print(f"✅ DEBUG: time_slot = {time_slot}, Type = {type(time_slot)}")
        print(f"✅ DEBUG: current_status = {current_status}, Type = {type(current_status)}")

        # ✅ Ensure only approved appointments are updated
        if current_status != "Approved":
            print(f"🚨 ERROR: Appointment {appointment_id} is not 'Approved'. Current status = {current_status}")
            flash("Appointment is not in Approved status.", "danger")
            return redirect(url_for('doctor_dashboard'))

        # ✅ Update the session link and status
        cur.execute("""
            UPDATE appointment_requests 
            SET session_link = %s, appointment_status = 'Ongoing'
            WHERE id = %s AND appointment_status = 'Approved'
        """, (meeting_link, appointment_id))

        print(f"✅ DEBUG: Rows affected by UPDATE = {cur.rowcount}")  # ✅ Check if update happened

        mysql.connection.commit()

        # ✅ Verify update
        cur.execute("""
            SELECT session_link, appointment_status FROM appointment_requests WHERE id = %s
        """, (appointment_id,))
        updated_data = cur.fetchone()
        print(f"✅ DEBUG: Updated Session Data = {updated_data}")

        cur.close()

        flash("Session link submitted successfully!", "success")

    except Exception as e:
        print(f"🚨 ERROR: {e}")
        flash("An error occurred while submitting the session link.", "danger")

    return redirect(url_for('doctor_dashboard'))

# Route to get today's sessions
@app.route('/todays_sessions')
def todays_sessions():
    if 'loggedin' not in session or session['role'] != 'doctor':
        return redirect(url_for('login'))

    doctor_id = session['doctor_id']
    try:
        cur = mysql.connection.cursor()

        # ✅ Fetch only today's approved sessions
        cur.execute("""
            SELECT ar.id, p.patient_name, p.disorder, p.email, p.contact_no, 
                   TIME_FORMAT(ar.time_slot, '%%h:%%i %%p') AS formatted_time,  
                   ar.appointment_status, ar.session_link  -- ✅ Fetch session_link
            FROM appointment_requests ar  
            JOIN patients p ON ar.patient_id = p.id  
            WHERE ar.doctor_id = %s  
            AND DATE(ar.appointment_date) = CURDATE()  -- ✅ Only today's appointments
            AND ar.appointment_status IN ('Approved', 'Rescheduled', 'Ongoing')  
        """, (doctor_id,))
        
        todays_sessions = cur.fetchall()

        # ✅ Debugging: Print fetched data
        print("✅ DEBUG: Data fetched for today's approved sessions:")
        for session in todays_sessions:
            print(f" - {session}")

        return redirect(url_for('doctor_dashboard'))

    except Exception as e:
        print(f"🚨 ERROR: Error fetching today's sessions: {e}")
        flash("An error occurred while fetching today's sessions.", "danger")
        return redirect(url_for('doctor_dashboard'))

    finally:
        cur.close()



# Route to submit a meeting link
@app.route('/submit_meeting', methods=['POST'])
def submit_meeting():
    if 'doctor_id' not in session:
        return redirect(url_for('login'))
    
    appointment_id = request.form['appointment_id']
    meeting_link = request.form['meeting_link']
    
    cur = mysql.connection.cursor()
    cur.execute("UPDATE appointments SET session_link=%s WHERE id=%s", (meeting_link, appointment_id))
    mysql.connection.commit()
    cur.close()
    
    flash('Meeting link submitted successfully!', 'success')
    return redirect(url_for('doctor_dashboard'))

# Request Appointment
@app.route('/request_appointment/<int:doctor_id>', methods=['POST'])
def request_appointment(doctor_id):
    if 'loggedin' not in session or session['role'] != 'patient':
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    
    # 🔹 Fetch patient details
    cur.execute("SELECT id, patient_name, disorder, email, contact_no FROM patients WHERE email = %s", (session['email'],))
    patient = cur.fetchone()
    
    # 🔹 Fetch doctor details (including email)
    cur.execute("SELECT doctor_name, email FROM doctors WHERE id = %s", (doctor_id,))
    doctor = cur.fetchone()

    if patient and doctor:
        patient_id, patient_name, disorder, email, contact_no = patient
        doctor_name, doctor_email = doctor  # 🔹 Fetch email dynamically from DB

        # 🔹 Insert into `appointment_requests` (not `appointments`)
        from datetime import datetime  # Import datetime for current date

        cur.execute("""
            INSERT INTO appointment_requests 
            (patient_id, doctor_id, appointment_status, disorder, email, contact_no, request_date) 
            VALUES (%s, %s, 'Pending', %s, %s, %s, %s)
        """, (patient_id, doctor_id, disorder, email, contact_no, datetime.today().date()))

        mysql.connection.commit()


        # 🔹 Send email to the doctor
        msg = Message("New Appointment Request",
                      sender="vinaykakad56@gmail.com",
                      recipients=[doctor_email])  # 🔹 Automatically fetched email
        msg.body = f"Dear Dr. {doctor_name},\n\nYou have received a new appointment request from {patient_name}.\n\nPlease log in to your dashboard to respond.\n\nBest Regards,\nTherapyTalk Team"

        try:
            mail.send(msg)
            flash('Appointment request sent! The doctor has been notified via email.', 'success')
        except Exception as e:
            flash(f'Appointment requested, but email could not be sent: {str(e)}', 'warning')

    cur.close()
    return redirect(url_for('patient_dashboard'))



# Patient Dashboard
# Patient Dashboard
@app.route('/patient_dashboard')
def patient_dashboard():
    print("DEBUG: Entering patient_dashboard route")
    if 'loggedin' not in session or session['role'] != 'patient':
        print("DEBUG: Not logged in or incorrect role. Redirecting to login.")
        return redirect(url_for('login'))

    print(f"DEBUG: Session Data - {session}")
    cur = mysql.connection.cursor()

    try:
        # Fetch patient ID, name, and disorder
        cur.execute("SELECT id, patient_name, disorder FROM patients WHERE email = %s", (session['email'],))
        patient = cur.fetchone()

        if not patient:
            print("DEBUG: Patient not found. Redirecting to login.")
            flash("Patient not found!", "danger")
            return redirect(url_for('login'))

        patient_id = patient[0]  # Index 0: id
        patient_name = patient[1]  # Index 1: patient_name
        patient_disorder = patient[2]  # Index 2: disorder

        print(f"DEBUG: Logged-in Patient ID = {patient_id}")
        print(f"DEBUG: Patient's Disorder = {patient_disorder}")

        # Fetch Therapist Name (Selected Therapist)
        cur.execute("""
            SELECT d.doctor_name 
            FROM appointment_requests ar
            JOIN doctors d ON ar.doctor_id = d.id 
            WHERE ar.patient_id = %s 
            AND ar.appointment_status = 'Doctor Approved'  -- ✅ Ensuring only Doctor Approved appointments
            LIMIT 1
        """, (patient_id,))

        therapist = cur.fetchone()
        therapist_name = therapist[0] if therapist else "No Therapist Selected"


        # Fetch Appointment Statistics
        cur.execute("SELECT COUNT(*) FROM appointment_requests WHERE patient_id = %s", (patient_id,))
        total_requests = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM appointment_requests WHERE patient_id = %s AND appointment_status IN ('Ongoing', 'Approved')", (patient_id,))
        approved_requests = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM appointment_requests WHERE patient_id = %s AND appointment_status = 'Completed'", (patient_id,))
        completed_sessions = cur.fetchone()[0]
        # Fetch Appointments
        cur.execute("""
            SELECT ar.id, d.doctor_name, ar.appointment_date, ar.time_slot, 
                ar.appointment_status, ar.payment_status, ar.admin_message
            FROM appointment_requests ar 
            JOIN doctors d ON ar.doctor_id = d.id 
            WHERE ar.patient_id = %s
        """, (patient_id,))

        appointments = cur.fetchall()



        # ✅ Fetch approved doctors (Fix)
        cur.execute("""
            SELECT d.id, d.doctor_name, d.specialty, d.experience, d.degree, d.fees
            FROM doctors d
            JOIN appointment_requests ar ON d.id = ar.doctor_id
            WHERE ar.patient_id = %s 
            AND ar.appointment_status = 'Doctor Approved'
        """, (patient_id,))
        approved_doctors = cur.fetchall()


        # ✅ Fetch therapists matching patient's disorder
        cur.execute("""
            SELECT id, doctor_name, specialty, experience, degree, fees
            FROM doctors
            WHERE approval_status = 'Approved' AND specialty = %s
        """, (patient_disorder,))
        disorder_doctors = cur.fetchall()  # ✅ Filtered therapists 

        # Fetch Session Details
        cur.execute("""
            SELECT ar.id, d.doctor_name, ar.appointment_date, ar.time_slot, ar.session_link
            FROM appointment_requests ar
            JOIN doctors d ON ar.doctor_id = d.id
            WHERE ar.patient_id = %s 
            AND ar.appointment_status = 'Ongoing'
        """, (patient_id,))

        session_details = cur.fetchall()

        # ✅ Fetch default platform charge
        cur.execute("SELECT default_amount FROM appointment_requests LIMIT 1")
        platform_charge = cur.fetchone()
        default_amount = float(platform_charge[0]) if platform_charge else 0.0  # ✅ Convert to float


        # Fetch Therapy Plans
        cur.execute("""
            SELECT tp.file_path, d.doctor_name, tp.upload_date 
            FROM therapy_plans tp
            JOIN doctors d ON tp.doctor_id = d.id 
            WHERE tp.patient_id = %s
        """, (patient_id,))
        therapy_plans = cur.fetchall()

        # Upload report 
          
        # Upload report appointments (like upload plan for doctor)
        cur.execute("""
            SELECT 
                a.id AS appointment_id,
                d.doctor_name AS doctor_name,
                d.degree AS doctor_degree,
                d.email AS doctor_email,
                a.appointment_date,
                a.appointment_status AS appointment_status,
                pr.status AS report_status  -- <- from patient_reports
            FROM appointment_requests a
            JOIN doctors d ON a.doctor_id = d.id
            LEFT JOIN patient_reports pr ON pr.appointment_id = a.id
            WHERE appointment_status = 'Approved' AND a.patient_id = %s
        """, (patient_id,))

        approved_appointments = cur.fetchall()




        # Fetch Payment History
        cur.execute("""
            SELECT ar.transaction_id, 
                (CAST(d.fees AS SIGNED) + 50) AS amount,  -- Convert Decimal to Integer before addition
                ar.payment_status, 
                ar.admin_message, 
                DATE(ar.request_time) AS request_date  -- Extract only the date
            FROM appointment_requests ar
            JOIN doctors d ON ar.doctor_id = d.id  -- Join with doctors table
            WHERE ar.patient_id = %s
        """, (patient_id,))


        payment_history = cur.fetchall()




        # ✅ Fetch Doctors Based on Patient’s Disorder
        if patient_disorder:
            # Get Specializations for the Disorder
            specializations = disorder_to_specialist.get(patient_disorder, [])
            print(f"DEBUG: Mapped Specializations = {specializations}")

            if specializations:
                # Fetch Doctors Matching the Specialization
                cur.execute("""
                    SELECT id, doctor_name, specialty, experience, degree, fees
                    FROM doctors 
                    WHERE specialty IN %s
                """, (tuple(specializations),))
                doctors = cur.fetchall()
                print(f"DEBUG: Doctors Found = {doctors}")
            else:
                doctors = []
                flash("No specializations found for your disorder.", "warning")
        else:
            doctors = []
            flash("No disorder found for the patient.", "danger")

        # Prepare Patient Dashboard Data
        patient_dashboard_data = {
            "selected_therapist": therapist_name,
            "total_requests_sent": total_requests,
            "approved_appointments": approved_requests,
            "completed_sessions": completed_sessions,
        }

        print("DEBUG: Rendering patient_dashboard.html")
        return render_template(
            'patient_dashboard.html',
            patient_dashboard_data=patient_dashboard_data,
            patient_name=patient_name,
            appointments=appointments,
            session_details=session_details,
            therapy_plans=therapy_plans,
            payment_history=payment_history,
            recommendations=session.pop("recommendations", None),
            approved_doctors=approved_doctors,  # ✅ Correctly passing approved doctors
            disorder_doctors=disorder_doctors,
            doctors=doctors,
            default_amount = default_amount,
            approved_appointments=approved_appointments)
            



    except Exception as e:
        print(f"DEBUG: Error in patient_dashboard: {e}")
        flash("An error occurred. Please try again.", "danger")
        return redirect(url_for('login'))  # Redirect to login instead of patient_dashboard to avoid loops

    finally:
        cur.close()


@app.route('/activity_recommendation', methods=['POST'])
def activity_recommendation():
    disorder = request.form.get('disorder')
    duration = request.form.get('duration')

    if not disorder or not duration:
        flash("Please select both disorder and duration!", "warning")
        return redirect(url_for('patient_dashboard'))

    # Fetch recommendations using your function that accepts two arguments.
    recommendations = get_activity_recommendations(disorder, duration)
    
    # Store the results and inputs in the session for the result page.
    session["recommendations"] = recommendations
    session["last_disorder"] = disorder
    session["last_duration"] = duration

    # Redirect to the dedicated activity result page.
    return redirect(url_for('activity_result'))

    
@app.route('/activity_result')
def activity_result():
    recommendations = session.get("recommendations")
    disorder = session.get("last_disorder")
    duration = session.get("last_duration")
    
    if not recommendations or not disorder or not duration:
        flash("No activity recommendations available. Please submit the form first.", "warning")
        return redirect(url_for('patient_dashboard'))
    
    return render_template('activity_result.html',
                           disorder=disorder,
                           duration=duration,
                           recommendations=recommendations)







def get_activity_recommendations(disorder, duration):
    # Normalize disorder input
    disorder_normalized = disorder.strip().lower()

    recommendations_data = {
        "stuttering": [
            {
                "title": "Speech Therapy Fun",
                "description": "Practice engaging speech exercises with fun videos.",
                "image": "https://th.bing.com/th/id/OIG1.AthZ.EY4uowxdVm098zO?w=1024&h=1024&rs=1&pid=ImgDetMain",
                "game_link": "https://pbskids.org/games/"
            },
            {
                "title": "Read Aloud Adventure",
                "description": "Read a fun story aloud and record your performance!",
                "image": "https://www.readingrockets.org/sites/default/files/styles/large/public/field_image/read-aloud.jpg?itok=5Z5J5Z5Z",
                "game_link": "https://www.storylineonline.net/"
            },
            {
                "title": "Breathing Exercises",
                "description": "Do playful breathing exercises to relax and improve control.",
                "image": "https://www.verywellhealth.com/thmb/breathing-exercises.jpg",
                "game_link": "https://www.verywellhealth.com/breathing-exercises-for-stuttering-5210357"
            }
        ],
        "neurological speech issue": [
            {
                "title": "Articulation Therapy",
                "description": "Improve pronunciation with guided articulation exercises.",
                "image": "https://www.speechandlanguagekids.com/wp-content/uploads/2016/01/articulation-therapy.jpg",
                "game_link": "https://www.speechandlanguagekids.com/articulation-games/"
            },
            {
                "title": "Motor Speech Exercises",
                "description": "Practice mouth and tongue exercises for better speech control.",
                "image": "https://www.speechtherapyideas.com/wp-content/uploads/2021/03/motor-speech-exercises.jpg",
                "game_link": "https://www.speechtherapyideas.com/motor-speech-activities/"
            },
            {
                "title": "Cognitive-Linguistic Training",
                "description": "Boost language skills with interactive cognitive games.",
                "image": "https://www.braintraininggames.org/images/cognitive-games.jpg",
                "game_link": "https://www.braintraininggames.org/"
            }
        ],
        "voice disorder": [
            {
                "title": "Vocal Warm-ups",
                "description": "Engage in fun vocal warm-up activities to prepare your voice.",
                "image": "https://www.verywellhealth.com/thmb/vocal-warm-ups.jpg",
                "game_link": "https://www.verywellhealth.com/vocal-warm-ups-5210358"
            },
            {
                "title": "Hydration Challenge",
                "description": "Learn fun ways to stay hydrated for a healthy voice.",
                "image": "https://www.kidshealth.org/en/kids/stay-hydrated.html",
                "game_link": "https://www.kidshealth.org/en/kids/stay-hydrated.html"
            },
            {
                "title": "Voice Rest Reminder",
                "description": "A playful reminder to rest your voice when needed.",
                "image": "https://www.enthealth.org/app/uploads/2020/06/voice-care-tips.jpg",
                "game_link": "https://www.enthealth.org/be-ent-smart/voice-care-tips/"
            }
        ],
        "autism communication issue": [
            {
                "title": "PECS Activity",
                "description": "Use picture exchange communication for fun learning.",
                "image": "https://www.autismspeaks.org/sites/default/files/2021-06/PECS-autism.jpg",
                "game_link": "https://www.autismspeaks.org/pecs-communication"
            },
            {
                "title": "Social Storytime",
                "description": "Enjoy social stories to improve interaction skills.",
                "image": "https://www.socialstories.com/images/social-storytime.jpg",
                "game_link": "https://www.storylineonline.net/"
            },
            {
                "title": "Sensory Play",
                "description": "Engage in sensory activities designed for playful learning.",
                "image": "https://sensoryplaykids.com/images/sensory-play.jpg",
                "game_link": "https://sensoryplaykids.com/"
            }
        ],
        "pediatric speech delay": [
            {
                "title": "Play-Based Therapy",
                "description": "Enjoy fun play activities designed to boost speech development.",
                "image": "https://www.speechtherapyplay.com/images/play-based-therapy.jpg",
                "game_link": "https://pbskids.org/games/"
            },
            {
                "title": "Interactive Reading",
                "description": "Read interactive stories that make learning fun!",
                "image": "https://www.readingrockets.org/sites/default/files/styles/large/public/field_image/interactive-reading.jpg?itok=5Z5J5Z5Z",
                "game_link": "https://www.storylineonline.net/"
            },
            {
                "title": "Social Communication Games",
                "description": "Play games that encourage social communication skills.",
                "image": "https://www.autismsociety.org/wp-content/uploads/2020/02/social-skills-games.jpg",
                "game_link": "https://pbskids.org/games/"
            }
        ],
        "post-surgery recovery": [
            {
                "title": "Gentle Vocal Exercises",
                "description": "Start with gentle exercises to ease your recovery.",
                "image": "https://www.asha.org/public/speech/development/images/gentle-vocal-exercises.jpg",
                "game_link": "https://www.verywellhealth.com/vocal-warm-ups-5210358"
            },
            {
                "title": "Breathing Relaxation",
                "description": "Practice relaxing breathing techniques for recovery.",
                "image": "https://www.verywellhealth.com/thmb/breathing-exercises.jpg",
                "game_link": "https://www.verywellhealth.com/breathing-exercises-for-recovery-5210359"
            },
            {
                "title": "Rest & Recovery Tips",
                "description": "Learn fun tips on how to rest and recover after surgery.",
                "image": "https://www.kidshealth.org/en/teens/recovery-after-surgery.html",
                "game_link": "https://www.kidshealth.org/en/teens/recovery-after-surgery.html"
            }
        ],
        "hearing and speech issue": [
            {
                "title": "Lip-Reading Fun",
                "description": "Practice lip reading with interactive videos and games.",
                "image": "https://www.hearingloss.org/wp-content/uploads/lip-reading-children.jpg",
                "game_link": "https://www.hearingloss.org/lip-reading-games/"
            },
            {
                "title": "Sign Language Basics",
                "description": "Learn basic sign language through fun animations.",
                "image": "https://www.startasl.com/wp-content/uploads/asl-signing.jpg",
                "game_link": "https://www.startasl.com/"
            },
            {
                "title": "Auditory Training Game",
                "description": "Enhance your listening skills with this engaging game.",
                "image": "https://www.hearingfirst.org/images/auditory-training-games.jpg",
                "game_link": "https://www.hearingfirst.org/listening-games"
            }
        ]
    }

    # Get recommendations for the disorder; if not found, use a default.
    activities = recommendations_data.get(disorder_normalized, [{
        "title": "General Speech Activity",
        "description": "Practice general speech exercises to improve clarity.",
        "image": "https://www.asha.org/public/speech/development/images/general-speech.jpg",
        "game_link": "https://pbskids.org/games/"
    }])

    # Modify the recommendations based on duration
    if duration == "15 days":
        return activities[:2]
    elif duration == "1 month":
        return activities
    elif duration == "3 months":
        follow_up = {
            "title": "Follow-Up Assessment",
            "description": "Review your progress with a fun interactive quiz!",
            "image": "https://www.speechtherapyquiz.com/images/follow-up.jpg",
            "game_link": "https://www.speechtherapyquiz.com/"
        }
        return activities + [follow_up]
    else:
        return activities








from flask_mail import Message

@app.route('/accept_appointment/<int:appointment_id>', methods=['POST'])
def accept_appointment(appointment_id):
    if 'loggedin' not in session or session['role'] != 'doctor':
        return redirect(url_for('doctor_login'))

    cur = mysql.connection.cursor()

    try:
        print(f"✅ DEBUG: Received appointment ID = {appointment_id}")

        # Ensure that this ID actually exists
        cur.execute("SELECT id, patient_id, doctor_id, appointment_status FROM appointment_requests WHERE id = %s", (appointment_id,))
        appointment = cur.fetchone()

        if appointment:
            print(f"✅ DEBUG: Fetched Appointment = {appointment}")
        else:
            print(f"❌ ERROR: No appointment found with ID = {appointment_id}")
            return redirect(url_for('doctor_dashboard'))

        # ✅ Approve the appointment request
        cur.execute("""
            UPDATE appointment_requests 
            SET appointment_status = 'Doctor Approved' 
            WHERE id = %s
        """, (appointment_id,))
        mysql.connection.commit()

        print(f"✅ DEBUG: Successfully updated appointment ID = {appointment_id}")


   


        # ✅ Fetch patient details to send an email notification
        cur.execute("""
            SELECT p.patient_name, p.email, d.doctor_name, d.specialty 
            FROM appointment_requests ar
            JOIN patients p ON ar.patient_id = p.id 
            JOIN doctors d ON ar.doctor_id = d.id 
            WHERE ar.id = %s
        """, (appointment_id,))
        appointment_details = cur.fetchone()

        if appointment_details:
            patient_name, patient_email, doctor_name, specialty = appointment_details

            # ✅ Send email to the patient
            msg = Message(
                subject="Doctor Approval - TherapyTalk",
                sender="vinaykakad56@gmail.com",  
                recipients=[patient_email]
            )
            msg.body = f"""
            Dear {patient_name},

            Your appointment request with Dr. {doctor_name} ({specialty}) has been approved by the doctor.
            
            You can now proceed to book your appointment in the TherapyTalk system.

            Best Regards,
            TherapyTalk Team
            """
            mail.send(msg)
            print(f"DEBUG: Email sent to {patient_email} for request {appointment_id}")
            flash("Appointment request approved. Patient notified to book the appointment.", "success")

    except Exception as e:
        print(f"DEBUG: Error updating appointment request status: {e}")
        flash("An error occurred while approving the request.", "danger")
    finally:
        cur.close()

    return redirect(url_for('doctor_dashboard'))


@app.route('/reject_appointment/<int:appointment_id>', methods=['POST'])
def reject_appointment(appointment_id):
    if 'loggedin' not in session or session['role'] != 'doctor':
        return redirect(url_for('doctor_login'))

    cur = mysql.connection.cursor()

    try:
        # ✅ Update the appointment request status to "Rejected"
        cur.execute("""
            UPDATE appointment_requests 
            SET appointment_status = 'Rejected' 
            WHERE id = %s
        """, (appointment_id,))
        mysql.connection.commit()

        # ✅ Fetch appointment details
        cur.execute("""
            SELECT p.patient_name, p.email, d.doctor_name, d.specialty 
            FROM appointment_requests ar
            JOIN patients p ON ar.patient_id = p.id 
            JOIN doctors d ON ar.doctor_id = d.id 
            WHERE ar.id = %s
        """, (appointment_id,))
        appointment_details = cur.fetchone()

        if appointment_details:
            patient_name, patient_email, doctor_name, specialty = appointment_details

            # ✅ Send email to the patient
            msg = Message(
                subject="Appointment Request Rejected - TherapyTalk",
                sender="vinaykakad56@gmail.com",  
                recipients=[patient_email]
            )
            msg.body = f"""
            Dear {patient_name},

            Unfortunately, your appointment request with Dr. {doctor_name} ({specialty}) has been rejected.

            You may request another appointment with a different doctor or try again later.

            Best Regards,
            TherapyTalk Team
            """
            mail.send(msg)

            flash("Appointment request rejected. Patient notified via email.", "success")
        else:
            flash("Appointment request not found.", "danger")

    except Exception as e:
        print(f"Error: {e}")
        flash("An error occurred while processing the rejection.", "danger")

    finally:
        cur.close()

    return redirect(url_for('doctor_dashboard'))


@app.route('/complete_appointment/<int:appointment_id>', methods=['POST'])
def complete_appointment(appointment_id):
    if 'loggedin' not in session or session['role'] != 'doctor':
        return redirect(url_for('doctor_login'))

    cur = mysql.connection.cursor()

    try:
        # Update the appointment status to "Completed" in the appointment_requests table
        cur.execute("UPDATE appointment_requests SET appointment_status = 'Completed' WHERE id = %s", (appointment_id,))
        mysql.connection.commit()

        flash("Appointment marked as completed!", "success")
    except Exception as e:
        print(f"Error: {e}")
        flash("An error occurred while completing the appointment.", "danger")
    finally:
        cur.close()

    return redirect(url_for('doctor_dashboard'))


@app.route('/admin/approve_appointment/<int:request_id>', methods=['POST'])
def approve_appointment(request_id):
    if 'loggedin' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    try:
        cur = mysql.connection.cursor()
        
        # ✅ Check if the appointment exists
        cur.execute("""
            SELECT ar.id, ar.patient_id, p.email, d.doctor_name, ar.appointment_date, ar.time_slot 
            FROM appointment_requests ar
            JOIN patients p ON ar.patient_id = p.id
            JOIN doctors d ON ar.doctor_id = d.id
            WHERE ar.id = %s
        """, (request_id,))
        appointment = cur.fetchone()

        if not appointment:
            flash("Invalid appointment request.", "danger")
            return redirect(url_for('admin_dashboard'))

        request_id, patient_id, patient_email, doctor_name, appointment_date, time_slot = appointment

        # ✅ Check if the admin rejected the request
        action = request.form.get("action")  # Fetch action from the form (Approve/Reject)
        admin_message = request.form.get("admin_message", "").strip()  # Get rejection message if any

        if action == "Reject":
            # ❌ Mark payment as FAILED and save admin message
            cur.execute("""
                UPDATE appointment_requests
                SET payment_status = 'Failed', appointment_status = 'Rejected', admin_message = %s
                WHERE id = %s
            """, (admin_message, request_id))

            mysql.connection.commit()

            # ✅ Send Rejection Email
            msg = Message(
                subject="Appointment Rejected ❌",
                sender="vinaykakad56@gmail.com",
                recipients=[patient_email]
            )
            msg.body = f"""
            Dear Patient,

            Unfortunately, your appointment with Dr. {doctor_name} on {appointment_date} at {time_slot} has been **rejected by the admin**.

            **Reason:** {admin_message if admin_message else "No specific reason provided."}

            If you have any concerns, please contact support.

            Best Regards,  
            TherapyTalk Team
            """
            mail.send(msg)
            print(f"DEBUG: Rejection email sent to {patient_email} with message: {admin_message}")

            flash("Appointment rejected, and patient has been notified.", "danger")
        
        else:
            # ✅ Approve Appointment (Keep existing logic)
            cur.execute("""
                UPDATE appointment_requests
                SET payment_status = 'Completed', appointment_status = 'Pending Doctor Approval'
                WHERE id = %s
            """, (request_id,))

            mysql.connection.commit()

            # ✅ Send Approval Email
            msg = Message(
                subject="Payment Successful & Appointment Under Review ✅",
                sender="vinaykakad56@gmail.com",
                recipients=[patient_email]
            )
            msg.body = f"""
            Dear Patient,

            Your payment for the appointment with Dr. {doctor_name} on {appointment_date} at {time_slot} has been successfully processed. 

            Your appointment request is now **under review by the doctor**. You will receive another update once the doctor accepts or reschedules the appointment.

            Best Regards,  
            TherapyTalk Team
            """
            mail.send(msg)
            print(f"DEBUG: Payment confirmation email sent to {patient_email}")

            flash("Appointment approved. The doctor will now review the request.", "success")

        return redirect(url_for('admin_dashboard'))

    except Exception as e:
        print(f"ERROR: {e}")
        flash("An error occurred while processing the request.", "danger")
        return redirect(url_for('admin_dashboard'))

    finally:
        cur.close()



from datetime import datetime

# ✅ Custom Jinja filter to format time
from datetime import datetime

from datetime import datetime

def format_time(time_str):
    try:
        if not time_str:
            return None  # Return None if no time is provided
        
        time_str = time_str.strip()  # Remove extra spaces

        # ✅ Convert `HH:MM AM/PM` → `HH:MM:SS` (24-hour format)
        if "AM" in time_str.upper() or "PM" in time_str.upper():
            return datetime.strptime(time_str, "%I:%M %p").strftime("%H:%M:%S") 
        
        # ✅ Convert `HH:MM` (24-hour format without seconds) → `HH:MM:SS`
        elif ":" in time_str and len(time_str.split(":")) == 2:
            return datetime.strptime(time_str, "%H:%M").strftime("%H:%M:%S") 

        # ✅ Convert `HH:MM:SS` (24-hour format) → Keep as is
        return time_str  

    except ValueError as e:
        print(f"ERROR: Failed to convert time '{time_str}': {e}")
        return None  # Return None if conversion fails




# ✅ Register the custom filter in Flask
app.jinja_env.filters['format_time'] = format_time



    
 

from flask_mail import Message

@app.route('/doctor/accept_appointment/<int:request_id>', methods=['POST'])
def doctor_accept_appointment(request_id):
    if 'loggedin' not in session or session['role'] != 'doctor':
        return redirect(url_for('doctor_login'))

    action = request.form.get('action')
    new_date = request.form.get('new_date')
    new_time = request.form.get('new_time')

    print(f"DEBUG: Entering doctor_accept_appointment() for Request ID: {request_id}, Action: {action}")

    try:
        cur = mysql.connection.cursor()

        # Fetch appointment details including patient email
        cur.execute("""
            SELECT ar.patient_id, ar.doctor_id, ar.appointment_status, ar.appointment_date, ar.time_slot, 
                   p.patient_name, p.email, d.doctor_name, d.specialty
            FROM appointment_requests ar
            JOIN patients p ON ar.patient_id = p.id
            JOIN doctors d ON ar.doctor_id = d.id
            WHERE ar.id = %s
        """, (request_id,))
        appointment_data = cur.fetchone()

        if not appointment_data:
            print(f"ERROR: Appointment {request_id} not found!")
            flash("Appointment not found or already processed.", "danger")
            return redirect(url_for('doctor_dashboard'))

        (patient_id, doctor_id, req_status, appointment_date, time_slot,
         patient_name, patient_email, doctor_name, specialty) = appointment_data

        if req_status != 'Pending Doctor Approval':
            print(f"ERROR: Appointment {request_id} is not awaiting doctor approval! Current status: {req_status}")
            flash("Appointment already processed.", "danger")
            return redirect(url_for('doctor_dashboard'))

        converted_time = format_time(time_slot)  # Convert to MySQL-compatible format


        if action == 'accept':
            print(f"DEBUG: Accepting appointment ID {request_id}")

            # Update status in appointment_requests table
            cur.execute("""
                UPDATE appointment_requests
                SET appointment_status = 'Approved'
                WHERE id = %s
            """, (request_id,))

            # Insert into appointments table
            cur.execute("""
                INSERT INTO appointments (id, patient_id, doctor_id, appointment_date, time_slot, status)
                VALUES (%s, %s, %s, %s, %s, 'Approved')
                ON DUPLICATE KEY UPDATE status = 'Approved', appointment_date = VALUES(appointment_date), time_slot = VALUES(time_slot)
            """, (request_id, patient_id, doctor_id, appointment_date, converted_time))

            flash("Appointment accepted successfully!", "success")
            print(f"DEBUG: Appointment {request_id} accepted and moved to appointments.")

            # ✅ Send confirmation email to the patient
            msg = Message(
                subject="Appointment Confirmed ✅",
                sender="vinaykakad56@gmail.com",
                recipients=[patient_email]
            )
            msg.body = f"""
            Dear {patient_name},

            Your appointment with Dr. {doctor_name} ({specialty}) on {appointment_date} at {time_slot} has been **confirmed**.

            Please make sure to be available at the scheduled time.

            Best Regards,  
            TherapyTalk Team
            """
            mail.send(msg)
            print(f"DEBUG: Confirmation email sent to {patient_email}")

        elif action == 'reschedule':
            print(f"DEBUG: Rescheduling appointment ID {request_id} to {new_date} {new_time}")

            converted_new_time = format_time(new_time)
            print(f"DEBUG: Converted time = {converted_new_time}, Original time = {new_time}")
            if not converted_new_time:
                print(f"ERROR: Failed to convert new_time '{new_time}'")
                flash("Invalid time format for reschedule!", "danger")
                return redirect(url_for('doctor_dashboard'))

            # Update the appointment request
            cur.execute("""
                UPDATE appointment_requests
                SET appointment_date = %s, time_slot = %s, appointment_status = 'Rescheduled'
                WHERE id = %s
            """, (new_date, converted_new_time, request_id))

            # Insert or update the appointment record
            cur.execute("""
                INSERT INTO appointments (id, patient_id, doctor_id, appointment_date, time_slot, status)
                VALUES (%s, %s, %s, %s, %s, 'Rescheduled')
                ON DUPLICATE KEY UPDATE status = 'Rescheduled', appointment_date = VALUES(appointment_date), time_slot = VALUES(time_slot)
            """, (request_id, patient_id, doctor_id, new_date, converted_new_time))

            flash("Appointment rescheduled successfully!", "success")
            print(f"DEBUG: Appointment {request_id} rescheduled.")

            # ✅ Send reschedule email to the patient
            msg = Message(
                subject="Appointment Rescheduled 🔄",
                sender="vinaykakad56@gmail.com",
                recipients=[patient_email]
            )
            msg.body = f"""
            Dear {patient_name},

            Your appointment with Dr. {doctor_name} ({specialty}) has been **rescheduled**.

            **New Date:** {new_date}  
            **New Time:** {new_time}  

            Please make sure to be available at the updated schedule.

            Best Regards,  
            TherapyTalk Team
            """
            mail.send(msg)
            print(f"DEBUG: Reschedule email sent to {patient_email}")

        mysql.connection.commit()
        cur.close()
        print(f"DEBUG: Successfully updated appointment {request_id}!")

    except Exception as e:
        print(f"ERROR: {e}")
        flash("An error occurred while processing the appointment.", "danger")

    return redirect(url_for('doctor_dashboard'))








@app.route('/book_appointment', methods=['GET', 'POST'])
def book_appointment():
    if 'loggedin' not in session or session['role'] != 'patient':
        return redirect(url_for('login'))

    patient_id = session.get('user_id')
    cur = mysql.connection.cursor()

    try:
        # ✅ Fetch only approved doctors for the patient
        cur.execute("""
            SELECT d.id, d.doctor_name, d.fees
            FROM doctors d
            JOIN appointment_requests ar ON d.id = ar.doctor_id
            WHERE ar.patient_id = %s AND ar.appointment_status = 'Doctor Approved'
        """, (patient_id,))
        approved_doctors = cur.fetchall()

        # ✅ Fetch default platform charge
        cur.execute("SELECT default_amount FROM appointment_requests LIMIT 1")
        platform_charge = cur.fetchone()
        default_amount = float(platform_charge[0]) if platform_charge else 0.0  # ✅ Convert to float

        if request.method == 'POST':
            doctor_id = request.form.get('doctor_id')
            appointment_date = request.form.get('appointmentDate')
            time_slot = request.form.get('timeSlot')
            account_holder = request.form.get('account_holder')
            transaction_id = request.form.get('transaction_id')

            # ✅ Fetch selected doctor's fee
            cur.execute("SELECT fees FROM doctors WHERE id = %s", (doctor_id,))
            doctor_fee = cur.fetchone()
            if doctor_fee:
                doctor_fee = float(doctor_fee[0])  # ✅ Convert to float
                total_amount = doctor_fee + default_amount  # ✅ Corrected calculation

                # ✅ Fetch patient details
                cur.execute("SELECT disorder, email, contact_no FROM patients WHERE id = %s", (patient_id,))
                patient_data = cur.fetchone()
                if patient_data:
                    disorder, email, contact_no = patient_data

                    # ✅ Insert appointment request with corrected total_amount
                    cur.execute("""
                        INSERT INTO appointment_requests 
                        (patient_id, doctor_id, appointment_date, time_slot, account_holder, transaction_id, amount, 
                        payment_status, appointment_status, disorder, email, contact_no) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, 'Pending', 'Pending Admin Approval', %s, %s, %s)
                    """, (patient_id, doctor_id, appointment_date, time_slot, account_holder, transaction_id, total_amount, disorder, email, contact_no))
                    mysql.connection.commit()

                    flash(f"Appointment booked successfully! Total amount paid: ₹{total_amount}. Waiting for admin approval.", "info")
                    return redirect(url_for('patient_dashboard'))

        return render_template('book_appointment.html', approved_doctors=approved_doctors, default_amount=default_amount)

    except Exception as e:
        print(f"DEBUG: Error booking appointment: {e}")
        flash("An error occurred while booking the appointment.", "danger")
    finally:
        cur.close()

    return redirect(url_for('patient_dashboard'))






@app.route('/doctor_dashboard', methods=['GET', 'POST'])
def doctor_dashboard():
    # Check if the user is logged in and is a doctor
    if 'loggedin' not in session or session['role'] != 'doctor' or 'doctor_id' not in session:
        return redirect(url_for('doctor_login'))

    doctor_id = session['doctor_id']
    print(f"DEBUG: Doctor ID = {doctor_id}")

    # Handle Start Session form submission
    if request.method == 'POST':
        appointment_id = request.form.get('appointment_id')
        meeting_link = request.form.get('meeting_link')
        time_slot = request.form.get('time_slot')

        try:
            cur = mysql.connection.cursor()

            # Update the appointment with session link and time slot, and set status to "Ongoing"
            cur.execute("""
                UPDATE appointments 
                SET session_link = %s, time_slot = %s, status = 'Ongoing' 
                WHERE id = %s AND doctor_id = %s
            """, (meeting_link, time_slot, appointment_id, doctor_id))
            mysql.connection.commit()

            flash("Session started successfully!", "success")

        except Exception as e:
            print(f"DEBUG: Error starting session: {e}")
            flash("An error occurred while starting the session.", "danger")

        finally:
            cur.close()

        return redirect(url_for('doctor_dashboard'))

    try:
        cur = mysql.connection.cursor()

        # Fetch Patient Activity (Dashboard Stats)
        cur.execute("""
            SELECT 
                COUNT(DISTINCT patient_id) AS total_requests,
                SUM(CASE WHEN appointment_status = 'Pending Doctor Approval' THEN 1 ELSE 0 END) AS approved_requests,
                SUM(CASE WHEN appointment_status IN ('Ongoing','Rescheduled') THEN 1 ELSE 0 END) AS active_patients,
                SUM(CASE WHEN appointment_status = 'Completed' THEN 1 ELSE 0 END) AS completed_therapy,
                SUM(CASE WHEN appointment_status = 'Pending' THEN 1 ELSE 0 END) AS pending_requests
            FROM appointment_requests 
            WHERE doctor_id = %s
        """, (doctor_id,))

        patient_activity = cur.fetchone()
        print(f"DEBUG: Patient Activity = {patient_activity}")

        # Fetch Pending Requests (Appointments Table)
        cur.execute("""
            SELECT ar.id, p.patient_name, ar.disorder, p.email, p.contact_no, p.address, ar.request_date
            FROM appointment_requests ar
            JOIN patients p ON ar.patient_id = p.id
            WHERE ar.appointment_status = 'Pending' AND ar.doctor_id = %s
        """, (doctor_id,))

        pending_requests_list = cur.fetchall()
        print(f"DEBUG: Pending Requests = {pending_requests_list}")

        # Fetch Active Patients (Approved appointments)
        cur.execute("""
            SELECT ar.id, p.patient_name, p.disorder, p.email, p.contact_no 
            FROM appointment_requests ar 
            JOIN patients p ON ar.patient_id = p.id 
            WHERE ar.doctor_id = %s AND ar.appointment_status IN ('Ongoing','Rescheduled')
        """, (doctor_id,))
        active_patients_list = cur.fetchall()
        print(f"DEBUG: Active Patients = {active_patients_list}")

        # Fetch Appointments for "Start Session"
        # Fetch Appointments for "Start Session"
        # Fetch Appointments for "Start Session"
        cur.execute("""
            SELECT ar.id, p.patient_name, p.disorder, p.email, p.contact_no, 
                ar.appointment_date, 
                ar.time_slot, 
                ar.session_link, 
                ar.appointment_status 
            FROM appointment_requests ar
            JOIN patients p ON ar.patient_id = p.id 
            WHERE ar.doctor_id = %s 
            AND ar.appointment_status IN ('Approved','Rescheduled');
        """, (doctor_id,))

        start_session_list = cur.fetchall()

# Fetch appointments from `appointment_requests`
        cur.execute("""
            SELECT ar.id, p.patient_name, p.disorder, p.email, p.contact_no, ar.appointment_date, ar.time_slot, ar.appointment_status
            FROM appointment_requests ar
            JOIN patients p ON ar.patient_id = p.id  -- JOIN to fetch patient details
            WHERE ar.doctor_id = %s
        """, (session['doctor_id'],))

        appointments = cur.fetchall()


        # Debugging output
        

                
        # Fetch Completed Therapy Patients
        cur.execute("""
            SELECT p.patient_name, p.disorder, p.email, p.contact_no, ar.appointment_date, ar.time_slot, ar.appointment_status
            FROM appointment_requests ar
            JOIN patients p ON ar.patient_id = p.id  -- Ensure this column exists
            WHERE ar.doctor_id = %s AND ar.appointment_status = 'Completed'
        """, (doctor_id,))

        completed_therapy_list = cur.fetchall()

        print(f"DEBUG: Completed Therapy = {completed_therapy_list}")  # Debugging output




        # Fetch Patients for Uploading Therapy Plan
        cur.execute("""
            SELECT 
                ar.id, 
                p.patient_name,  -- ✅ Fetch from 'patients' table
                p.disorder, 
                p.email, 
                p.contact_no, 
                ar.appointment_status,
                ar.therapy_plan_status -- ✅ Ensure this column exists in 'appointment_requests'
            FROM 
                appointment_requests ar
            JOIN 
                patients p ON ar.patient_id = p.id  -- ✅ Correct join with 'patients' table
            WHERE 
                ar.doctor_id = %s 
                AND ar.therapy_plan_status = 'Pending'
                AND ar.appointment_status IN ('Ongoing', 'Approved', 'Rescheduled'); -- ✅ Constraint added
        """, (doctor_id,))



        upload_plan_appointments = cur.fetchall()
        print(f"✅ DEBUG: Upload Plan Appointments = {upload_plan_appointments}")


        # Fetch pending appointment requests
        
        # Fetch pending appointment requests
        cur.execute("""
            SELECT ar.id, p.patient_name, ar.appointment_date, 
                   TIME_FORMAT(ar.time_slot, '%%h:%%i %%p') AS formatted_time,  
                   ar.appointment_status
            FROM appointment_requests ar
            JOIN patients p ON ar.patient_id = p.id
            WHERE ar.appointment_status = 'Pending Doctor Approval' 
            AND ar.doctor_id = %s
            ORDER BY ar.appointment_date ASC
        """, (doctor_id,))

        pending_payment_requests = cur.fetchall()
        print(f"DEBUG: Pending Payment Requests = {pending_payment_requests}")

        


        

        # Fetch already approved or rescheduled appointments
        cur.execute("""
            SELECT ar.id, p.patient_name, ar.appointment_date, ar.time_slot, ar.appointment_status
            FROM appointment_requests ar
            JOIN patients p ON ar.patient_id = p.id
            WHERE ar.doctor_id = %s 
            AND ar.appointment_status IN ('Approved', 'Rescheduled')
            ORDER BY ar.appointment_date ASC
        """, (doctor_id,))

        processed_appointments = cur.fetchall()

        formatted_appointments = []
        for appointment in processed_appointments:
            appointment_id, patient_name, appointment_date, time_slot, status = appointment

            # ✅ Convert 'time_slot' (VARCHAR) to proper AM/PM format
            try:
                formatted_time = datetime.strptime(time_slot, "%H:%M").strftime("%I:%M %p") if time_slot else "No Time"
            except ValueError:
                print(f"ERROR: Failed to convert time '{time_slot}' for appointment {appointment_id}")
                formatted_time = "Invalid Time"

            formatted_appointments.append((appointment_id, patient_name, appointment_date, formatted_time, status))

        print(f"✅ DEBUG: Processed Appointments with Formatted Time = {formatted_appointments}")



        
        

        # ✅ Fetch today's sessions from 'appointment_requests' table
        cur.execute("""
            SELECT ar.id, p.patient_name, p.disorder, p.email, p.contact_no, 
                   TIME_FORMAT(ar.time_slot, '%%h:%%i %%p') AS formatted_time,  
                   ar.appointment_status, ar.session_link  -- ✅ Fetch session_link
            FROM appointment_requests ar  
            JOIN patients p ON ar.patient_id = p.id  
            WHERE ar.doctor_id = %s  
            AND DATE(ar.appointment_date) = CURDATE()  -- ✅ Only today's appointments
            AND ar.appointment_status = 'Ongoing'  
        """, (doctor_id,))
        
        todays_sessions = cur.fetchall()

        # Pending Session

        cur.execute("""
            SELECT ar.id, p.patient_name, p.disorder, p.contact_no, 
                DATE_FORMAT(ar.appointment_date, '%%Y-%%m-%%d') AS appointment_date,  
                TIME_FORMAT(ar.time_slot, '%%h:%%i %%p') AS formatted_time,  
                ar.session_link  
            FROM appointment_requests ar  
            JOIN patients p ON ar.patient_id = p.id  
            WHERE ar.doctor_id = %s  
                AND ar.appointment_status = 'Ongoing'  
            ORDER BY ar.appointment_date ASC  
        """, (doctor_id,))


        pending_sessions = cur.fetchall()

        # 🔍 Get appointments with uploaded reports
        cur.execute("""
                SELECT 
                    a.id AS appointment_id,
                    p.patient_name AS patient_name,
                    p.disorder AS disorder,
                    a.appointment_date,
                    pr.file_path AS report_file_path
                FROM appointment_requests a
                JOIN patients p ON a.patient_id = p.id
                JOIN patient_reports pr ON a.id = pr.appointment_id
                WHERE a.doctor_id = %s AND pr.status = 'Uploaded'
                ORDER BY a.appointment_date DESC
            """, (doctor_id,))
        
        report_data = cur.fetchall()
        print("DEBUG: Patient reports fetched = ", report_data)




        # Fetch Payment history
        cur.execute("""
            SELECT p.patient_name, t.transaction_id,t.doctor_receivable,
                 t.status, t.payment_date
            FROM appointment_requests ar
            JOIN patients p ON ar.patient_id = p.id
            LEFT JOIN transactions t ON ar.id = t.appointment_id
            WHERE ar.doctor_id = %s 
                AND t.status = 'Paid'
        """, (doctor_id,))

        payment_history = cur.fetchall()
        print("✅ DEBUG: Payment History =", payment_history)


        

        # Calculate dashboard stats
        if patient_activity:
            total_requests = int(patient_activity[0]) if patient_activity[0] is not None else 0
            approved_requests = int(patient_activity[1]) if patient_activity[1] is not None else 0
            active_patients = int(patient_activity[2]) if patient_activity[2] is not None else 0
            completed_therapy = int(patient_activity[3]) if patient_activity[3] is not None else 0
            pending_requests = int(patient_activity[4]) if patient_activity[4] is not None else 0
        else:
            total_requests = 0
            approved_requests = 0
            active_patients = 0
            completed_therapy = 0
            pending_requests = 0

        return render_template(
            'doctor_dashboard.html',
            total_requests=total_requests,
            approved_requests=approved_requests,
            active_patients=active_patients,
            completed_therapy=completed_therapy,
            pending_requests=pending_requests,
            pending_requests_list=pending_requests_list,
            active_patients_list=active_patients_list,
            completed_therapy_list=completed_therapy_list,
            upload_plan_appointments=upload_plan_appointments,
            pending_payment_requests=pending_payment_requests,
            payment_history=payment_history,
            start_session_list=start_session_list,
            processed_appointments=processed_appointments,
            todays_sessions = todays_sessions,
            appointments = appointments,
            pending_sessions = pending_sessions,
            reports=report_data
            
             )
            
        

    except Exception as general_err:
        print(f"DEBUG: General Error in doctor_dashboard: {general_err}")
        traceback.print_exc()  # Log the full traceback
        flash("An unexpected error occurred. Please contact support.", "danger")
        return redirect(url_for('doctor_login'))

    finally:
        if 'cur' in locals() and cur:
            cur.close()

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        print(f"Received username: {username}, password: {password}")  # Debugging

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM admins WHERE username = %s", (username,))
        admin = cur.fetchone()
        cur.close()

        if admin:
            print(f"Stored password in DB: {admin[2]}")  # Debugging

            if admin[2] == password:  # Direct comparison
                session['loggedin'] = True
                session['role'] = 'admin'
                session['user_id'] = admin[0]
                session['username'] = username

                print("Login successful!")  # Debugging
                flash("Login successful!", "success")
                return redirect(url_for('admin_dashboard'))
            else:
                print("Password mismatch")  # Debugging
                flash("Invalid username or password.", "danger")
                return render_template('admin_login.html')

        flash("Invalid username or password.", "danger")
        return render_template('admin_login.html')

    return render_template('admin_login.html')

            

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'loggedin' not in session or session['role'] != 'admin':
        return redirect(url_for('admin_login'))

    cur = mysql.connection.cursor()

    # ✅ Fetch dashboard statistics
    cur.execute("SELECT COUNT(*) FROM patients")
    patient_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM doctors")
    therapist_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM appointment_requests WHERE appointment_status = 'Ongoing'")
    active_cases = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM appointment_requests WHERE appointment_status = 'Completed'")
    completed_cases = cur.fetchone()[0]

    cur.execute("""
        SELECT SUM(amount ) 
        FROM appointment_requests WHERE payment_status = 'Completed'
    """)
    total_revenue = cur.fetchone()[0] or 0.0  # ✅ Ensures result is not None


    # ✅ Fetch therapist list (Including Contact Number)
    cur.execute("""
        SELECT d.doctor_name, d.email, d.specialty, d.phone,
            COUNT(CASE WHEN ar.appointment_status IN ('Ongoing', 'Completed') THEN 1 END) AS patients_allocated,
            COUNT(CASE WHEN ar.appointment_status = 'Completed' THEN 1 END) AS patients_completed
        FROM doctors d
        LEFT JOIN appointment_requests ar ON d.id = ar.doctor_id
        GROUP BY d.id
    """)
    therapists = cur.fetchall()

    # ✅ Fetch patient data (With therapist allocation & Contact Number)
    cur.execute("""
        SELECT 
            p.patient_name, 
            p.disorder, 
            COALESCE(ar.appointment_status, 'Not Assigned') AS appointment_status, 
            COALESCE(d.doctor_name, 'Not Assigned') AS doctor_name,
            p.contact_no
        FROM patients p
        LEFT JOIN appointment_requests ar ON p.id = ar.patient_id
        LEFT JOIN doctors d ON ar.doctor_id = d.id
        WHERE ar.appointment_status IN ('Ongoing', 'Completed', 'Doctor Approved', 'Pending Admin Approval', 'Pending Doctor Approval')
        OR ar.appointment_status IS NULL
    """)
    patient_details = cur.fetchall()

    therapist_specialties = list(set([t[2] for t in therapists]))  # Extract unique specializations
    patient_disorders = list(set([p[1] for p in patient_details]))  # Extract unique disorders




    # ✅ Fetch payment history
    cur.execute("""
        SELECT p.patient_name, 
            COALESCE(ar.transaction_id, 'Not Available') AS transaction_id, 
            COALESCE(ar.amount, 0) AS amount, 
            COALESCE(DATE_FORMAT(ar.request_time, '%Y-%m-%d'), 'Not Available') AS payment_date
        FROM appointment_requests ar
        JOIN patients p ON ar.patient_id = p.id
        WHERE ar.payment_status = 'Completed'
    """)
    payments = cur.fetchall()

    # Fetch completed appointments where payment is pending
    cur.execute("""
        SELECT d.doctor_name, p.patient_name, d.fees, 
            ROUND(d.fees * 0.80, 2) AS doctor_receivable, 
            d.phone, ar.id
        FROM appointment_requests ar
        JOIN doctors d ON ar.doctor_id = d.id
        JOIN patients p ON ar.patient_id = p.id
        LEFT JOIN transactions t ON ar.id = t.appointment_id
        WHERE ar.appointment_status = 'Completed' 
            AND (t.status IS NULL OR t.status = 'Pending')
    """)
    pending_payments = cur.fetchall() or []
    print("✅ Pending Payments:", pending_payments)  # Debugging


    # all paid payment
    cur.execute("""
        SELECT d.doctor_name, p.patient_name, d.fees AS total_fees, 
            ROUND(d.fees * 0.80, 2) AS doctor_receivable, 
            t.platform_fee, t.phonepe_number, 
            t.transaction_id, t.status, t.payment_date
        FROM transactions t
        JOIN appointment_requests ar ON t.appointment_id = ar.id
        JOIN doctors d ON ar.doctor_id = d.id
        JOIN patients p ON ar.patient_id = p.id
        WHERE t.status = 'Paid'
    """)
    paid_transactions = cur.fetchall()
    print("✅ Paid Transactions:", paid_transactions)  # Debugging






    # ✅ Fetch pending approval appointments
    from datetime import datetime

    cur.execute("""
        SELECT ar.id, p.patient_name, p.email, p.disorder, 
               ar.amount, ar.account_holder, ar.transaction_id, 
               ar.appointment_date, ar.time_slot, ar.request_time
        FROM appointment_requests ar
        JOIN patients p ON ar.patient_id = p.id
        WHERE ar.appointment_status = 'Pending Admin Approval'
    """)

    pending_appointments = cur.fetchall()

    pending_appointments = [
        (
            row[0],  # Appointment ID
            row[1],  # Patient Name
            row[2],  # Email
            row[3],  # Disorder
            f"{row[4]:,.2f}" if row[4] else "Not Set",  # Amount
            row[5] if row[5] else "Not Set",  # Account Holder
            row[6] if row[6] else "Not Set",  # Transaction ID
            row[7].strftime("%Y-%m-%d") if row[7] else "Not Set",  # Appointment Date
            row[8] if row[8] else "Not Set",  # Time Slot
            row[9].strftime("%Y-%m-%d %H:%M:%S") if isinstance(row[9], datetime) else "Not Set",  # Request Time
            row[0]
        )
        for row in pending_appointments
    ]

    return render_template(
        'admin_dashboard.html',
        patient_count=patient_count,
        therapist_count=therapist_count,
        active_cases=active_cases,
        completed_cases=completed_cases,
        total_revenue=total_revenue,
        therapists=therapists,
        patient_details=patient_details,
        payments=payments,
        pending_appointments=pending_appointments ,
        therapist_specialties=therapist_specialties, 
        patient_disorders=patient_disorders,
        pending_payments = pending_payments ,
        paid_transactions = paid_transactions # ✅ Add pending approvals
    )

@app.route('/process_payment/<int:appointment_id>', methods=['POST'])
def process_payment(appointment_id):
    print(f"✅ DEBUG: Received Payment Request for Appointment ID: {appointment_id}")  # Debugging

    cur = mysql.connection.cursor()

    try:
        # Fetch appointment details
        cur.execute("""
            SELECT d.id, d.doctor_name, d.fees, d.phone, ar.patient_id 
            FROM appointment_requests ar
            JOIN doctors d ON ar.doctor_id = d.id
            WHERE ar.id = %s
        """, (appointment_id,))
        
        appointment = cur.fetchone()
        print(f"✅ DEBUG: Appointment Details: {appointment}")  # Debugging

        if not appointment:
            flash("Invalid appointment ID.", "danger")
            return redirect(url_for('admin_dashboard'))

        doctor_id, doctor_name, fees, phone_number, patient_id = appointment
        fees = float(fees)

        platform_fee = round(fees * 0.20, 2)  
        doctor_receivable = round(fees - platform_fee, 2)  
        transaction_id = request.form.get('transaction_id', '').strip()

        print(f"✅ DEBUG: Transaction ID: {transaction_id}")  # Debugging

        if not transaction_id:
            flash("Please enter a valid Transaction ID.", "danger")
            return redirect(url_for('admin_dashboard'))

        # Insert transaction into database
        cur.execute("""
            INSERT INTO transactions (appointment_id, doctor_id, doctor_name, patient_id, phonepe_number, 
                                      total_fees, platform_fee, doctor_receivable, transaction_id, status, payment_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'Paid', NOW())
        """, (appointment_id, doctor_id, doctor_name, patient_id, phone_number, fees, platform_fee, doctor_receivable, transaction_id))

        
        
        mysql.connection.commit()
        print("✅ DEBUG: Payment successfully processed!")  # Debugging
        flash("Payment sent successfully!", "success")

    except Exception as e:
        mysql.connection.rollback()
        print(f"❌ ERROR: Payment processing failed: {e}")  # Debugging
        flash(f"Payment processing failed: {str(e)}", "danger")

    finally:
        cur.close()

    return redirect(url_for('admin_dashboard'))





@app.route('/doctor_payments')
def doctor_payments():
    doctor_id = session.get('doctor_id')

    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT patient_name, id, doctor_receivable, status, 
               (SELECT appointment_date FROM appointment_requests WHERE id = t.appointment_id)
        FROM transactions t
        WHERE doctor_id = %s
        ORDER BY id DESC
    """, (doctor_id,))
    
    payment_history = cur.fetchall()
    cur.close()

    return render_template('doctor_dashboard.html', payment_history=payment_history)





if __name__ == '__main__':
    app.run(debug=True)
