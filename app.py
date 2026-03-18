from flask import Flask, render_template, request, redirect, session
import psycopg2
from datetime import date
import os

app = Flask(__name__)
app.secret_key = "secret123"

# ✅ Use Render DATABASE_URL
def get_db_connection():
    return psycopg2.connect(os.environ.get("DATABASE_URL"))


# ✅ Create tables automatically (safe)
def create_tables():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS teachers (
        id SERIAL PRIMARY KEY,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id SERIAL PRIMARY KEY,
        name TEXT,
        roll_no INTEGER
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id SERIAL PRIMARY KEY,
        student_id INTEGER,
        date DATE,
        status TEXT
    );
    """)

    conn.commit()
    cur.close()
    conn.close()


# Run once when app starts
create_tables()


@app.route('/')
def home():
    return redirect('/login')


# ---------- TEACHER REGISTER ----------
@app.route('/register', methods=['GET','POST'])
def register():

    if request.method == 'POST':

        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute(
                "INSERT INTO teachers (name,email,password) VALUES (%s,%s,%s)",
                (name,email,password)
            )

            conn.commit()
            cur.close()
            conn.close()

            return redirect('/login')

        except Exception as e:
            print(e)
            return "Error: Email may already exist"

    return render_template('register.html')


# ---------- LOGIN ----------
@app.route('/login', methods=['GET','POST'])
def login():

    if request.method == 'POST':

        email = request.form.get('email')
        password = request.form.get('password')

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM teachers WHERE email=%s AND password=%s",
            (email,password)
        )

        teacher = cur.fetchone()

        cur.close()
        conn.close()

        if teacher:
            session['teacher_id'] = teacher[0]
            session['teacher_name'] = teacher[1]

            return redirect('/dashboard')

        else:
            return "Invalid email or password"

    return render_template('login.html')


# ---------- DASHBOARD ----------
@app.route('/dashboard')
def dashboard():

    if 'teacher_id' not in session:
        return redirect('/login')

    selected_date = request.args.get('date')

    if not selected_date:
        selected_date = str(date.today())

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM students ORDER BY roll_no")
    students = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "dashboard.html",
        students=students,
        selected_date=selected_date,
        teacher=session['teacher_name']
    )


# ---------- ADD STUDENT ----------
@app.route('/add_student', methods=['POST'])
def add_student():

    name = request.form.get('name')
    roll_no = request.form.get('roll_no')

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO students (name,roll_no) VALUES (%s,%s)",
        (name,roll_no)
    )

    conn.commit()
    cur.close()
    conn.close()

    return redirect('/dashboard')


# ---------- DELETE STUDENT ----------
@app.route('/delete_student/<int:student_id>')
def delete_student(student_id):

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM attendance WHERE student_id=%s",(student_id,))
    cur.execute("DELETE FROM students WHERE id=%s",(student_id,))

    conn.commit()
    cur.close()
    conn.close()

    return redirect('/dashboard')


# ---------- MARK ATTENDANCE ----------
@app.route('/mark/<int:student_id>', methods=['POST'])
def mark(student_id):

    status = request.form.get('status')
    selected_date = request.form.get('date')

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO attendance (student_id,date,status) VALUES (%s,%s,%s)",
        (student_id,selected_date,status)
    )

    conn.commit()
    cur.close()
    conn.close()

    return redirect('/dashboard?date=' + selected_date)


# ---------- VIEW ATTENDANCE ----------
@app.route('/view')
def view():

    filter_date = request.args.get('date')

    conn = get_db_connection()
    cur = conn.cursor()

    if filter_date:
        cur.execute("""
        SELECT students.roll_no, students.name, attendance.date, attendance.status
        FROM attendance
        JOIN students ON attendance.student_id = students.id
        WHERE attendance.date=%s
        ORDER BY students.roll_no
        """,(filter_date,))
    else:
        cur.execute("""
        SELECT students.roll_no, students.name, attendance.date, attendance.status
        FROM attendance
        JOIN students ON attendance.student_id = students.id
        ORDER BY attendance.date DESC
        """)

    records = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("view.html",records=records)


# ---------- LOGOUT ----------
@app.route('/logout')
def logout():

    session.clear()
    return redirect('/login')


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
