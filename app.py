# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash
import mysql.connector
from datetime import datetime
from config import DB_CONFIG, FLASK_SECRET

app = Flask(__name__)
app.secret_key = FLASK_SECRET

def get_db_connection():
    conn = mysql.connector.connect(**DB_CONFIG)
    return conn

def login_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

@app.route("/")
def index():
    if session.get("admin_logged_in"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM admins WHERE username = %s", (username,))
        admin = cur.fetchone()
        cur.close()
        conn.close()
        if admin and check_password_hash(admin["password_hash"], password):
            session["admin_logged_in"] = True
            session["admin_username"] = username
            flash("Logged in successfully.", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials.", "danger")
            return render_template("login.html")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM patients")
    patients_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM appointments WHERE status = 'booked'")
    appointments_count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return render_template("dashboard.html", patients_count=patients_count, appointments_count=appointments_count)

@app.route("/add_patient", methods=["GET", "POST"])
@login_required
def add_patient():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        age = request.form.get("age") or None
        gender = request.form.get("gender") or "Male"
        phone = request.form.get("phone") or ""
        address = request.form.get("address") or ""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO patients (name, age, gender, phone, address) VALUES (%s, %s, %s, %s, %s)",
            (name, age, gender, phone, address)
        )
        conn.commit()
        cur.close()
        conn.close()
        flash("Patient added successfully.", "success")
        return redirect(url_for("patients"))
    return render_template("add_patient.html")

@app.route("/patients")
@login_required
def patients():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM patients ORDER BY created_at DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("patients.html", patients=rows)

@app.route("/appointments", methods=["GET", "POST"])
@login_required
def appointments():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    # For booking new appointment (POST)
    if request.method == "POST":
        patient_id = request.form.get("patient_id")
        appt_dt = request.form.get("appointment_datetime")  # format: 'YYYY-MM-DDTHH:MM'
        doctor = request.form.get("doctor", "").strip()
        notes = request.form.get("notes", "").strip()
        if not patient_id or not appt_dt:
            flash("Select patient and date/time.", "warning")
            return redirect(url_for("appointments"))
        # Convert datetime-local to MySQL DATETIME format
        appt_dt_sql = appt_dt.replace("T", " ")
        cur.execute(
            "INSERT INTO appointments (patient_id, appointment_datetime, doctor, notes) VALUES (%s, %s, %s, %s)",
            (patient_id, appt_dt_sql, doctor, notes)
        )
        conn.commit()
        flash("Appointment booked.", "success")
        return redirect(url_for("appointments"))

    # GET: show appointments & patients list for the booking form
    cur.execute("SELECT a.*, p.name as patient_name FROM appointments a JOIN patients p ON a.patient_id = p.id ORDER BY a.appointment_datetime DESC")
    appts = cur.fetchall()
    cur.execute("SELECT id, name FROM patients ORDER BY name")
    patients_list = cur.fetchall()
    cur.close()
    conn.close()
    # Convert datetime strings to more readable format in template if needed
    return render_template("appointments.html", appointments=appts, patients=patients_list)

@app.route("/cancel_appointment/<int:appointment_id>", methods=["POST"])
@login_required
def cancel_appointment(appointment_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE appointments SET status = 'cancelled' WHERE id = %s", (appointment_id,))
    conn.commit()
    cur.close()
    conn.close()
    flash("Appointment cancelled.", "info")
    return redirect(url_for("appointments"))

if __name__ == "__main__":
    app.run(debug=True)
