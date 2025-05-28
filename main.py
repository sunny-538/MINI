from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS students (
        roll_no TEXT PRIMARY KEY,
        password TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS admins (
        username TEXT PRIMARY KEY,
        password TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS attendance (
        roll_no TEXT,
        month TEXT,
        days_present INTEGER,
        FOREIGN KEY(roll_no) REFERENCES students(roll_no)
    )''')
    c.execute("INSERT OR IGNORE INTO students VALUES ('556', 'pass123')")
    c.execute("INSERT OR IGNORE INTO admins VALUES ('admin', 'adminpass')")
    conn.commit()
    conn.close()

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    error = None
    if request.method == 'POST':
        roll_no = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM students WHERE roll_no=? AND password=?", (roll_no, password))
        user = c.fetchone()
        conn.close()
        if user:
            session['role'] = 'student'
            session['user'] = roll_no
            return redirect('/student/dashboard')
        else:
            error = 'Invalid student credentials.'
    return render_template('student_login.html', error=error)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM admins WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()
        if user:
            session['role'] = 'admin'
            session['user'] = username
            return redirect('/admin/dashboard')
        else:
            error = 'Invalid admin credentials.'
    return render_template('admin_login.html', error=error)

@app.route('/student/dashboard')
def student_dashboard():
    if session.get('role') != 'student':
        return redirect('/')
    roll = session['user']
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT month, days_present, days_present * 100 FROM attendance WHERE roll_no=?", (roll,))
    records = c.fetchall()
    total_due = sum(row[2] for row in records)
    conn.close()
    return render_template('student_dashboard.html', records=records, total_due=total_due)

@app.route('/admin/dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect('/')
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT roll_no FROM students")
    students = [{'roll': row[0], 'name': f'Student {row[0]}'} for row in c.fetchall()]

    if request.method == 'POST':
        month = request.form['month']
        for roll in request.form.getlist('rolls'):
            days_present = request.form.get(f'days_present[{roll}]', 0)
            c.execute("REPLACE INTO attendance (roll_no, month, days_present) VALUES (?, ?, ?)",
                      (roll, month, int(days_present)))
        conn.commit()
        conn.close()
        return redirect('/admin/dashboard')
    conn.close()
    return render_template('admin_dashboard.html', students=students)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
