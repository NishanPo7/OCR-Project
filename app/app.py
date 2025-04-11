from flask import Flask, render_template, flash, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
import os
import utils
import settings
import cv2
import json
from predictions import getPredictions
from flask import session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'document_scanner_app'

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:root@localhost/student_rank'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Admin(db.Model):
    __tablename__ = 'admin_users'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

class StudentRank(db.Model):
    __tablename__ = 'rank'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    roll = db.Column(db.String, nullable=False)
    iit_score = db.Column(db.Integer, nullable=False)
    cp_score = db.Column(db.Integer, nullable=False)
    digital_score = db.Column(db.Integer, nullable=False)
    math_score = db.Column(db.Integer, nullable=False)
    physics_score = db.Column(db.Integer, nullable=False)
    total_score = db.Column(db.Integer, nullable=False)
    
    
# Upload folder from settings.py
UPLOAD_FOLDER = 'static/media'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure that upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def home():
    return render_template('student1.html')

@app.route('/admin/register', methods=['GET', 'POST'])
def admin_register():
    if request.method == 'POST':
        full_name = request.form.get('fullname')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('admin_register'))

        hashed_password = generate_password_hash(password)
        
        try:
            new_admin = Admin(
                full_name=full_name,
                email=email,
                password=hashed_password
            )
            db.session.add(new_admin)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('admin_login'))
        except IntegrityError:
            db.session.rollback()
            flash('Email already exists!', 'danger')
        
    return render_template('register.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        admin = Admin.query.filter_by(email=email).first()
        
        if admin and check_password_hash(admin.password, password):
            session['admin_logged_in'] = True
            session['admin_email'] = admin.email
            
            # Extract first name from full name
            full_name = admin.full_name  # Replace 'full_name' with your database column name
            first_name = full_name.split()[0] if full_name else 'Admin'
            session['admin_first_name'] = first_name 
            flash('Login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid email or password!', 'danger')
    
    return render_template('admin.html')

@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    # Redirect to the index route that handles data fetching
    return redirect(url_for('index'))

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_email', None)
    flash('You have been logged out!', 'success')
    return redirect(url_for('admin_login'))


@app.route('/index')
def index():
    students = StudentRank.query.order_by(StudentRank.total_score.desc()).all()
    
    top_students = students[:3] if len(students) >= 3 else students
    
    recent_updates = StudentRank.query.order_by(StudentRank.id.desc()).limit(3).all()
    
    return render_template(
        'index.html',
        students=students,
        top_students=top_students,
        recent_updates=recent_updates
    )

@app.route('/cp')
def cp():
    students = StudentRank.query.order_by(StudentRank.cp_score.desc()).all()
    top_students = students[:3] if len(students) >= 3 else students
    
    recent_updates = StudentRank.query.order_by(StudentRank.id.desc()).limit(3).all()
    
    return render_template(
        'cp.html',
        students=students,
        top_students=top_students,
        recent_updates=recent_updates
    )

@app.route('/digital')
def digital():
    students = StudentRank.query.order_by(StudentRank.digital_score.desc()).all()
    top_students = students[:3] if len(students) >= 3 else students
    
    recent_updates = StudentRank.query.order_by(StudentRank.id.desc()).limit(3).all()
    
    return render_template(
        'digital.html',
        students=students,
        top_students=top_students,
        recent_updates=recent_updates
    )

@app.route('/iit')
def iit():
    students = StudentRank.query.order_by(StudentRank.iit_score.desc()).all()
    top_students = students[:3] if len(students) >= 3 else students
    
    recent_updates = StudentRank.query.order_by(StudentRank.id.desc()).limit(3).all()
    
    return render_template(
        'iit.html',
        students=students,
        top_students=top_students,
        recent_updates=recent_updates
    )

@app.route('/mathematics')
def mathematics():
    students = StudentRank.query.order_by(StudentRank.math_score.desc()).all()
    top_students = students[:3] if len(students) >= 3 else students
    
    recent_updates = StudentRank.query.order_by(StudentRank.id.desc()).limit(3).all()
    
    return render_template(
        'mathematics.html',
        students=students,
        top_students=top_students,
        recent_updates=recent_updates
    )

@app.route('/physics')
def physics():
    students = StudentRank.query.order_by(StudentRank.physics_score.desc()).all()
    top_students = students[:3] if len(students) >= 3 else students
    
    recent_updates = StudentRank.query.order_by(StudentRank.id.desc()).limit(3).all()
    
    return render_template(
        'physics.html',
        students=students,
        top_students=top_students,
        recent_updates=recent_updates
    )
    
@app.route('/info', methods=['GET', 'POST'])
def info():
    if request.method == 'POST':
        fullname = request.form.get('fullname')
        rollnumber = request.form.get('rollnumber')
        
        # Query student (case-insensitive name match)
        student = StudentRank.query.filter(
            StudentRank.name.ilike(fullname),
            StudentRank.roll == rollnumber
        ).first()
        
        if student:
            session['student_id'] = student.id
            # Store first name in session
            session['student_first_name'] = student.name.split()[0] if student.name else 'Student'
            return redirect(url_for('info'))
        else:
            flash('Student not found. Please check your details.')
            return redirect(url_for('home'))
    
    # Handle GET requests
    student_id = session.get('student_id')
    if student_id:
        student = StudentRank.query.get(student_id)
        if student:
            return render_template('info.html', student=student)
        else:
            session.pop('student_id', None)
            flash('Session expired. Please log in again.')
            return redirect(url_for('home'))
    else:
        return redirect(url_for('home'))
    
@app.route('/ranking')
def ranking():
    students = StudentRank.query.order_by(StudentRank.total_score.desc()).all()
    top_students = students[:3] if len(students) >= 3 else students
    
    student = None
    if 'student_id' in session:
        student = StudentRank.query.get(session['student_id'])
    
    return render_template(
        'ranking.html',
        students=students,
        top_students=top_students,
        student=student
    )

@app.route('/scanner', methods=['GET', 'POST'])
def scanner():
    entities = {}

    if request.method == 'POST':
        file = request.files.get('image_name')
        ALLOWED_EXTENSIONS = {'jpg', 'jpeg'}
        if file and file.filename != '':
            
            if not ('.' in file.filename and 
                   file.filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS):
                flash('Invalid file type. Only JPG/JPEG files are allowed.', 'error')
                return redirect(request.url)
            
            # Proceed with valid JPG/JPEG file
            upload_image_path = utils.save_upload_image(file)
            print('Image saved at:', upload_image_path)
            
            image = cv2.imread(upload_image_path)
            processed_image, extracted_entities = getPredictions(image)
            print('Extracted Entities:', extracted_entities)

            result_filename = 'processed_' + file.filename
            result_path = utils.join_path(app.config['UPLOAD_FOLDER'], result_filename)
            cv2.imwrite(result_path, processed_image)

            entities = extracted_entities
            print("Entities data:", entities)
            return render_template(
                'scanner.html',
                image_url=url_for('static', filename='media/' + file.filename),
                result_image=url_for('static', filename='media/' + result_filename),
                entities=entities,
            )
        else:
            flash('Please select a file to upload', 'error')
            return redirect(request.url)

    return render_template('scanner.html', entities=entities)

@app.route('/save-data', methods=['POST'])
def save_data():
    try:
        entities = request.get_json()
        
        def safe_convert(value, default=0):
            try:
                clean = ''.join(c for c in str(value) if c.isdigit() or c == '.')
                return int(float(clean)) if clean else default
            except:
                return default

        # Handle name with default
        name = entities.get('NAME', ['Unknown'])[0] or 'Unknown'
        
        # Get and clean roll number
        raw_roll = entities.get('ROLL', [''])[0]
        roll = str(raw_roll).strip()

        # Check if roll already exists
        existing = StudentRank.query.filter_by(roll=roll).first()
        if existing:
            return {
                'success': False,
                'error': f'Roll number {roll} already exists in database'
            }, 400

        # Convert scores safely
        total_score = safe_convert(entities.get('TS', [0])[0])
        
        # Handle subject scores
        raw_ss = entities.get('SS', [])
        subject_scores = [safe_convert(score) for score in raw_ss][:5]
        while len(subject_scores) < 5:
            subject_scores.append(0)

        # Create and save new entry
        new_rank = StudentRank(
            name=name,
            roll=roll,
            iit_score=subject_scores[0],
            cp_score=subject_scores[1],
            digital_score=subject_scores[2],
            math_score=subject_scores[3],
            physics_score=subject_scores[4],
            total_score=total_score,
        )

        db.session.add(new_rank)
        db.session.commit()

        return {'success': True}

    except IntegrityError:
        db.session.rollback()
        return {
            'success': False,
            'error': 'Duplicate entry detected (database constraint)'
        }, 400
        
    except Exception as e:
        db.session.rollback()
        print(f"Error saving data: {str(e)}")
        return {'success': False, 'error': str(e)}, 500
    
if __name__ == "__main__":
    app.run(debug=True)