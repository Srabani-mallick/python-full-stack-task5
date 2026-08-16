from flask import Flask, render_template, request, redirect, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
# app.secret_key = "secure-secret-key"
app.secret_key = os.environ.get("SECRET_KEY", "fallback-dev-key")
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

# ---------- ROLE-BASED ACCESS DECORATOR ----------

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user' not in session or session.get('role') != 'admin':
            return redirect('/dashboard')
        return f(*args, **kwargs)
    return wrapper

# ---------- AUTH ROUTES ----------

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        db = get_db()
        db.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password)
        )
        db.commit()
        return redirect('/login')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()

        if user and check_password_hash(user['password'], password):
            session['user'] = user['username']
            session['role'] = user['role']
            return redirect('/dashboard')

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')
    return render_template('dashboard.html', user=session['user'], role=session.get('role'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# ---------- ADMIN PANEL (Step 4) ----------

@app.route('/admin')
@admin_required
def admin_dashboard():
    db = get_db()
    users = db.execute("SELECT id, username, role FROM users").fetchall()
    return render_template('admin.html', users=users)

# ---------- ADMIN-ONLY DELETE (Step 5) ----------

@app.route('/admin/delete/<int:id>')
@admin_required
def admin_delete_student(id):
    db = get_db()
    db.execute("DELETE FROM students WHERE id=?", (id,))
    db.commit()
    return redirect('/students')

# ---------- CRUD ROUTES ----------

@app.route('/add-student', methods=['GET', 'POST'])
def add_student():
    if 'user' not in session:
        return redirect('/login')

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        course = request.form['course']

        db = get_db()
        db.execute(
            "INSERT INTO students (name, email, course) VALUES (?, ?, ?)",
            (name, email, course)
        )
        db.commit()
        return redirect('/students')

    return render_template('add_student.html')

@app.route('/students')
def students():
    if 'user' not in session:
        return redirect('/login')

    db = get_db()
    data = db.execute("SELECT * FROM students").fetchall()
    return render_template('students.html', students=data, role=session.get('role'))

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_student(id):
    if 'user' not in session:
        return redirect('/login')

    db = get_db()
    student = db.execute("SELECT * FROM students WHERE id = ?", (id,)).fetchone()

    if request.method == 'POST':
        db.execute(
            "UPDATE students SET name=?, email=?, course=? WHERE id=?",
            (request.form['name'], request.form['email'], request.form['course'], id)
        )
        db.commit()
        return redirect('/students')

    return render_template('edit_student.html', student=student)

# ---------- REST API ENDPOINTS (Step 6) ----------

@app.route('/api/students', methods=['GET'])
def api_get_students():
    db = get_db()
    students = db.execute("SELECT * FROM students").fetchall()
    return jsonify([dict(row) for row in students])

@app.route('/api/students', methods=['POST'])
def api_add_student():
    data = request.get_json()
    db = get_db()
    db.execute(
        "INSERT INTO students (name, email, course) VALUES (?, ?, ?)",
        (data['name'], data['email'], data['course'])
    )
    db.commit()
    return jsonify({"message": "Student added successfully"})

@app.route('/api/students/<int:id>', methods=['PUT'])
def api_update_student(id):
    data = request.get_json()
    db = get_db()
    db.execute(
        "UPDATE students SET name=?, email=?, course=? WHERE id=?",
        (data['name'], data['email'], data['course'], id)
    )
    db.commit()
    return jsonify({"message": "Student updated"})

@app.route('/api/students/<int:id>', methods=['DELETE'])
def api_delete_student(id):
    db = get_db()
    db.execute("DELETE FROM students WHERE id=?", (id,))
    db.commit()
    return jsonify({"message": "Student deleted"})

if __name__ == '__main__':
    app.run(debug=False)