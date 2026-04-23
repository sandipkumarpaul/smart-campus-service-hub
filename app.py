import os
import uuid
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import Flow
    from googleapiclient.discovery import build

    GOOGLE_CALENDAR_AVAILABLE = True
except ImportError:
    Request = None
    Credentials = None
    Flow = None
    build = None
    GOOGLE_CALENDAR_AVAILABLE = False


app = Flask(__name__)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
ALLOWED_EXTENSIONS = {"pdf", "docx"}
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
# Connected to XAMPP MySQL Database
app.config['SECRET_KEY'] = 'bracu_smart_campus_secure_key_2026' 
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/smart_campus_service_hub(1)'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
db = SQLAlchemy(app)

# ==========================================
# HELPERS
# ==========================================


def current_user_id():
    return session.get("user_id")


def require_login_redirect():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return None


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_calendar_service():
    if not GOOGLE_CALENDAR_AVAILABLE:
        raise RuntimeError("Google Calendar dependencies are not installed.")

    token_path = os.path.join(BASE_DIR, "token.json")
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        if creds and creds.valid:
            return build("calendar", "v3", credentials=creds)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(token_path, "w") as token:
                token.write(creds.to_json())
            return build("calendar", "v3", credentials=creds)

    raise FileNotFoundError("No valid token found. Please authenticate at /auth first.")

# ==========================================
# CENTRALIZED MYSQL MODELS
# ==========================================

# The Central Users Table
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(50), unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    department = db.Column(db.String(50))
    major = db.Column(db.String(100))

# Queenw's Feature 1: Study Partner Finder
class StudyPartnerPost(db.Model):
    __tablename__ = 'study_partner_posts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    goals = db.Column(db.Text, nullable=True)
    preferred_study_time = db.Column(db.String(150), nullable=True)
    
    current_topic = db.Column(db.String(150))
    prep_goal = db.Column(db.String(50))
    study_style = db.Column(db.String(50))
    group_size = db.Column(db.Integer, default=2)
    
    status = db.Column(db.String(50), default='open')
    user = db.relationship('User', backref='study_posts')

class StudySession(db.Model):
    __tablename__ = 'study_sessions'
    id = db.Column(db.Integer, primary_key=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text) 
    session_date = db.Column(db.String(50), nullable=False)
    start_time = db.Column(db.String(50), nullable=False)
    location_text = db.Column(db.String(255))
    status = db.Column(db.String(50), default='scheduled')

# Sandip's Feature 1: Tutoring Listings
class TutoringListing(db.Model):
    __tablename__ = 'tutoring_listings'
    id = db.Column(db.Integer, primary_key=True)
    tutor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject_title = db.Column(db.String(150), nullable=False)
    teaching_style = db.Column(db.Text) 
    availability_text = db.Column(db.String(255))
    mode = db.Column(db.String(50), default='both') 
    location_text = db.Column(db.String(255)) 
    rate_type = db.Column(db.String(50), default='Paid') 
    hourly_rate = db.Column(db.Numeric(10, 2), default=0.00)
    free_consult = db.Column(db.String(10), default='No')
    
    user = db.relationship('User', backref='tutoring_posts')
    bookings = db.relationship('TutoringBooking', backref='listing', lazy=True)

class TutoringBooking(db.Model):
    __tablename__ = 'tutoring_bookings'
    id = db.Column(db.Integer, primary_key=True)
    tutoring_listing_id = db.Column(db.Integer, db.ForeignKey('tutoring_listings.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_date = db.Column(db.String(50))
    start_time = db.Column(db.String(50))
    note = db.Column(db.Text)
    status = db.Column(db.String(50), default='pending')

# Sandip's Feature 2: Campus Events
class CampusEvent(db.Model):
    __tablename__ = 'campus_events'
    id = db.Column(db.Integer, primary_key=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100)) 
    event_date = db.Column(db.String(50), nullable=False) 
    location_text = db.Column(db.String(255))
    target_audience = db.Column(db.String(100), default='Open to all')
    capacity_limit = db.Column(db.Integer, default=0)
    recap_text = db.Column(db.Text)
    status = db.Column(db.String(50), default='upcoming')
    
    creator = db.relationship('User', backref='events')
    participants = db.relationship('EventParticipant', backref='event', lazy=True)

class EventParticipant(db.Model):
    __tablename__ = 'event_participants'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('campus_events.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    attendance_status = db.Column(db.String(50), default='interested') 

# Queenw's Feature 2: Real-Time Messaging
class Conversation(db.Model):
    __tablename__ = 'conversations'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150))
    conversation_type = db.Column(db.String(50), default='private')
    context_type = db.Column(db.String(50)) 
    context_id = db.Column(db.Integer)      
    
    messages = db.relationship('Message', backref='conversation', lazy=True)

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message_text = db.Column(db.Text)
    is_seen = db.Column(db.Integer, default=0) 
    sender = db.relationship('User', backref='sent_messages')

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(100), nullable=False) 
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)


# Dipto's Features
class Note(db.Model):
    __tablename__ = "notes"
    __table_args__ = {'mysql_engine': 'InnoDB'}

    id = db.Column(db.Integer, primary_key=True)
    uploader_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    course_id = db.Column(db.Integer, nullable=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    file_path = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50))
    semester = db.Column(db.String(50))
    tags = db.Column(db.String(255))
    downloads_count = db.Column(db.Integer, default=0)
    visibility = db.Column(db.String(20), default="public")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AcademicDeadline(db.Model):
    __tablename__ = "academic_deadlines"
    __table_args__ = {'mysql_engine': 'InnoDB'}

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    deadline_datetime = db.Column(db.DateTime, nullable=False)
    priority = db.Column(db.String(20), default="medium")
    reminder_enabled = db.Column(db.Boolean, default=True)
    status = db.Column(db.String(20), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ScheduledStudySession(db.Model):
    __tablename__ = "scheduled_study_sessions"
    __table_args__ = {'mysql_engine': 'InnoDB'}

    id = db.Column(db.Integer, primary_key=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    session_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    mode = db.Column(db.String(20), default="both")
    location_text = db.Column(db.String(255))
    meeting_link = db.Column(db.String(255))
    status = db.Column(db.String(20), default="scheduled")

# ==========================================
# ROUTES
# ==========================================

#@app.route('/')
#def home():
    #return render_template('base.html')
@app.route("/")
def home():
    if "user_id" in session:
        # If logged in, go to dashboard
        return redirect(url_for("dashboard"))
    # If not logged in, go to login
    return redirect(url_for("login"))

# ==========================================
# AUTHENTICATION ROUTES
# ==========================================

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form["email"]
        #hashed_pw = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered. Please log in or use a different email.", "danger")
            return redirect(url_for("register"))

        hashed_pw = generate_password_hash(request.form["password"], method="pbkdf2:sha256")        
        new_user = User(
            full_name=request.form['full_name'],
            username=request.form['username'],
            email=request.form['email'],
            password_hash=hashed_pw,
            department=request.form['department']

        )
        try:
            db.session.add(new_user)
            db.session.commit()
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("login"))
        except IntegrityError:
            db.session.rollback()
            flash("An error occurred during registration. Please try again.", "danger")
            return redirect(url_for("register"))
        #db.session.add(new_user)
        #db.session.commit()
        #flash("Registration successful! Please log in.", "success")
        #return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        
        if user and check_password_hash(user.password_hash, request.form['password']):
            session['user_id'] = user.id
            session['full_name'] = user.full_name
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password. Please try again.", "danger")
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear() 
    return redirect(url_for('login'))


# ==========================================
# GOOGLE CALENDAR AUTH ROUTES
# ==========================================

@app.route("/auth")
def auth():
    if not GOOGLE_CALENDAR_AVAILABLE:
        flash("Google Calendar integration dependencies are not installed.", "danger")
        return redirect(url_for("dashboard"))

    creds_path = os.path.join(BASE_DIR, "credentials.json")
    redirect_uri = request.host_url.rstrip("/") + "/callback"
    flow = Flow.from_client_secrets_file(creds_path, scopes=SCOPES, redirect_uri=redirect_uri)
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
    )
    session["state"] = state
    session["code_verifier"] = flow.code_verifier
    return redirect(authorization_url)


@app.route("/callback")
def callback():
    if not GOOGLE_CALENDAR_AVAILABLE:
        flash("Google Calendar integration dependencies are not installed.", "danger")
        return redirect(url_for("dashboard"))

    state = session.get("state")
    code_verifier = session.get("code_verifier")
    if not state or request.args.get("state") != state:
        return "State mismatch", 400

    creds_path = os.path.join(BASE_DIR, "credentials.json")
    redirect_uri = request.host_url.rstrip("/") + "/callback"
    flow = Flow.from_client_secrets_file(creds_path, scopes=SCOPES, redirect_uri=redirect_uri)
    flow.code_verifier = code_verifier
    flow.fetch_token(code=request.args.get("code"))

    token_path = os.path.join(BASE_DIR, "token.json")
    with open(token_path, "w") as token_file:
        token_file.write(flow.credentials.to_json())

    flash("Google Calendar connected successfully.", "success")
    return redirect(url_for("dashboard"))


# ==========================================
# DIPTO'S ROUTES: NOTES
# ==========================================

@app.route("/upload", methods=["GET", "POST"])
def upload_notes():
    login_redirect = require_login_redirect()
    if login_redirect:
        return login_redirect

    if request.method == "POST":
        title = request.form.get("title")
        course = request.form.get("course")
        term = request.form.get("term")
        year = request.form.get("year")
        file = request.files.get("file")

        if not title or not course or not term or not year or not file:
            flash("All fields are required.", "danger")
            return redirect(url_for("upload_notes"))

        if file.filename == "":
            flash("Please choose a file.", "danger")
            return redirect(url_for("upload_notes"))

        if not allowed_file(file.filename):
            flash("Only PDF and DOCX files are allowed.", "danger")
            return redirect(url_for("upload_notes"))

        filename = secure_filename(file.filename)
        unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], unique_filename)
        file.save(filepath)

        file_type = unique_filename.rsplit(".", 1)[1].lower() if "." in unique_filename else ""
        new_note = Note(
            uploader_id=current_user_id(),
            title=title,
            description=f"Course: {course}",
            semester=f"{term} {year}",
            file_path=unique_filename,
            file_type=file_type,
        )
        db.session.add(new_note)
        db.session.commit()

        flash("Note uploaded successfully.", "success")
        return redirect(url_for("dashboard"))

    return render_template("upload_notes.html")


@app.route("/search", methods=["GET", "POST"])
def search_notes():
    login_redirect = require_login_redirect()
    if login_redirect:
        return login_redirect

    if request.method == "POST":
        course = request.form.get("course")
        term = request.form.get("term")
        year = request.form.get("year")
        query = Note.query

        if course:
            query = query.filter(Note.description.ilike(f"%{course}%"))

        semester_parts = []
        if term:
            semester_parts.append(term)
        if year:
            semester_parts.append(year)
        if semester_parts:
            semester_str = " ".join(semester_parts)
            query = query.filter(Note.semester.ilike(f"%{semester_str}%"))

        notes = query.order_by(Note.created_at.desc()).all()
        return render_template("results.html", notes=notes, course=course, term=term, year=year)

    return render_template("search_notes.html")


@app.route("/download/<path:filename>")
def download_file(filename):
    login_redirect = require_login_redirect()
    if login_redirect:
        return login_redirect

    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)


@app.route("/edit/<int:note_id>", methods=["GET", "POST"])
def edit_note(note_id):
    login_redirect = require_login_redirect()
    if login_redirect:
        return login_redirect

    note = Note.query.get_or_404(note_id)
    if request.method == "POST":
        note.title = request.form.get("title")
        note.description = f"Course: {request.form.get('course')}"
        note.semester = f"{request.form.get('term')} {request.form.get('year')}"
        db.session.commit()
        flash("Note updated successfully.", "success")
        return redirect(url_for("search_notes"))

    course_name = ""
    if note.description and note.description.startswith("Course: "):
        course_name = note.description.replace("Course: ", "", 1)

    sem_parts = note.semester.split(" ") if note.semester else ["", ""]
    term_name = sem_parts[0] if len(sem_parts) > 0 else ""
    year_name = sem_parts[1] if len(sem_parts) > 1 else ""

    return render_template(
        "edit_note.html",
        note=note,
        course_name=course_name,
        term_name=term_name,
        year_name=year_name,
    )


@app.route("/delete/<int:note_id>", methods=["POST"])
def delete_note(note_id):
    login_redirect = require_login_redirect()
    if login_redirect:
        return login_redirect

    note = Note.query.get_or_404(note_id)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], note.file_path)
    if os.path.exists(filepath):
        os.remove(filepath)

    db.session.delete(note)
    db.session.commit()
    flash("Note deleted successfully.", "success")
    return redirect(url_for("search_notes"))


# ==========================================
# DIPTO'S ROUTES: DEADLINES AND STUDY SESSION API
# ==========================================

@app.route("/deadlines")
def deadlines():
    login_redirect = require_login_redirect()
    if login_redirect:
        return login_redirect

    all_deadlines = AcademicDeadline.query.filter_by(user_id=current_user_id()).order_by(
        AcademicDeadline.deadline_datetime.asc()
    ).all()
    return render_template("deadlines.html", deadlines=all_deadlines)


@app.route("/deadlines/add", methods=["POST"])
def add_deadline():
    login_redirect = require_login_redirect()
    if login_redirect:
        return login_redirect

    title = request.form.get("title")
    description = request.form.get("description")
    deadline_date = request.form.get("deadline_date")
    deadline_time = request.form.get("deadline_time")
    priority = request.form.get("priority", "medium")

    if not title or not deadline_date or not deadline_time:
        flash("Title and deadline date/time are required.", "danger")
        return redirect(url_for("deadlines"))

    dt_obj = datetime.strptime(f"{deadline_date} {deadline_time}", "%Y-%m-%d %H:%M")
    new_deadline = AcademicDeadline(
        user_id=current_user_id(),
        title=title,
        description=description,
        deadline_datetime=dt_obj,
        priority=priority,
    )
    db.session.add(new_deadline)
    db.session.commit()

    try:
        service = get_calendar_service()
        event = {
            "summary": title,
            "description": description or "",
            "start": {"dateTime": dt_obj.isoformat(), "timeZone": "Asia/Dhaka"},
            "end": {"dateTime": (dt_obj + timedelta(hours=1)).isoformat(), "timeZone": "Asia/Dhaka"},
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "popup", "minutes": 30},
                    {"method": "email", "minutes": 30},
                ],
            },
        }
        service.events().insert(calendarId="primary", body=event).execute()
    except Exception as error:
        print(f"Google Calendar API Error: {error}")

    flash("Deadline added successfully!", "success")
    return redirect(url_for("deadlines"))


@app.route("/deadlines/delete/<int:id>", methods=["POST"])
def delete_deadline(id):
    login_redirect = require_login_redirect()
    if login_redirect:
        return login_redirect

    deadline = AcademicDeadline.query.get_or_404(id)
    db.session.delete(deadline)
    db.session.commit()
    flash("Deadline removed.", "info")
    return redirect(url_for("deadlines"))


@app.route("/api/study-sessions", methods=["GET"])
def get_study_sessions():
    login_redirect = require_login_redirect()
    if login_redirect:
        return login_redirect

    sessions = ScheduledStudySession.query.filter_by(created_by=current_user_id()).all()
    return jsonify(
        [
            {
                "id": study_session.id,
                "title": study_session.title,
                "date": study_session.session_date.strftime("%Y-%m-%d"),
                "time": (
                    f"{study_session.start_time.strftime('%H:%M')} - "
                    f"{study_session.end_time.strftime('%H:%M')}"
                ),
                "meeting_link": study_session.meeting_link,
            }
            for study_session in sessions
        ]
    )


@app.route("/api/study-sessions/create", methods=["POST"])
def create_scheduled_study_session():
    login_redirect = require_login_redirect()
    if login_redirect:
        return login_redirect

    data = request.get_json(silent=True) or {}
    try:
        session_date = datetime.strptime(data["date"], "%Y-%m-%d").date()
        start_time = datetime.strptime(data["start_time"], "%H:%M").time()
        end_time = datetime.strptime(data["end_time"], "%H:%M").time()
        start_datetime = datetime.combine(session_date, start_time)
        end_datetime = datetime.combine(session_date, end_time)

        if start_datetime >= end_datetime:
            return jsonify({"error": "End time must be after start time"}), 400

        meeting_link = ""

        try:
            service = get_calendar_service()
            event = {
                "summary": data.get("title", "Study Session"),
                "description": data.get("description", ""),
                "start": {"dateTime": start_datetime.isoformat(), "timeZone": "Asia/Dhaka"},
                "end": {"dateTime": end_datetime.isoformat(), "timeZone": "Asia/Dhaka"},
                "conferenceData": {
                    "createRequest": {
                        "requestId": str(uuid.uuid4()),
                        "conferenceSolutionKey": {"type": "hangoutsMeet"},
                    }
                },
                "reminders": {
                    "useDefault": False,
                    "overrides": [
                        {"method": "popup", "minutes": 30},
                        {"method": "email", "minutes": 30},
                    ],
                },
            }
            event_result = service.events().insert(
                calendarId="primary",
                body=event,
                conferenceDataVersion=1,
            ).execute()
            meeting_link = event_result.get("hangoutLink", "")
        except Exception as calendar_error:
            print(f"Google Calendar API Error: {calendar_error}")
            return jsonify({"error": f"Failed to create Google Calendar event: {calendar_error}"}), 500

        new_session = ScheduledStudySession(
            created_by=current_user_id(),
            title=data["title"],
            description=data.get("description", ""),
            session_date=session_date,
            start_time=start_time,
            end_time=end_time,
            mode=data.get("mode", "online"),
            location_text=data.get("location_text"),
            meeting_link=meeting_link,
        )
        db.session.add(new_session)
        db.session.commit()

        return jsonify(
            {
                "message": "Study session scheduled successfully!",
                "session_id": new_session.id,
                "meeting_link": meeting_link,
            }
        ), 201
    except KeyError as missing_field:
        return jsonify({"error": f"Missing required field: {missing_field.args[0]}"}), 400
    except ValueError as value_error:
        return jsonify({"error": f"Invalid date/time format: {value_error}"}), 400
    except Exception as error:
        return jsonify({"error": str(error)}), 500


# --- Sandip's Routes ---
@app.route('/tutors', methods=['GET', 'POST'])
def tutors():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        is_free = 'Yes' if request.form.get('free_consult') else 'No' 
        
        new_listing = TutoringListing(
            tutor_id=session['user_id'], # Using dynamic session ID
            subject_title=request.form['subject'],
            teaching_style=request.form['teaching_style'],
            availability_text=request.form['availability'],
            mode=request.form['mode'],
            location_text=request.form['location'],
            rate_type=request.form['rate_type'],
            hourly_rate=request.form['rate'],
            free_consult=is_free
        )
        db.session.add(new_listing)
        db.session.commit()
        return redirect(url_for('tutors'))
    
    all_tutors = TutoringListing.query.order_by(TutoringListing.id.desc()).all()
    return render_template('tutors.html', tutors=all_tutors)

@app.route('/book_tutor/<int:listing_id>', methods=['POST'])
def book_tutor(listing_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    new_booking = TutoringBooking(
        tutoring_listing_id=listing_id,
        student_id=session['user_id'], # Using dynamic session ID
        session_date=request.form['session_date'],
        start_time=request.form['start_time'],
        note=request.form['note']
    )
    db.session.add(new_booking)
    db.session.commit()
    return redirect(url_for('tutors'))

@app.route('/events', methods=['GET', 'POST'])
def events():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        new_event = CampusEvent(
            created_by=session['user_id'], # Using dynamic session ID
            title=request.form['title'],
            category=request.form['category'],
            event_date=request.form['date'],
            location_text=request.form['location'],
            target_audience=request.form['target_audience'],
            capacity_limit = request.form['capacity_limit'] if request.form['capacity_limit'] else 0,
            description=request.form['description']
        )
        db.session.add(new_event)
        db.session.commit()
        return redirect(url_for('events'))
    
    all_events = CampusEvent.query.order_by(CampusEvent.id.desc()).all()
    return render_template('events.html', events=all_events)

@app.route('/rsvp/<int:event_id>/<string:status>')
def rsvp(event_id, status):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    existing_rsvp = EventParticipant.query.filter_by(event_id=event_id, user_id=session['user_id']).first()
    
    if existing_rsvp:
        existing_rsvp.attendance_status = status
    else:
        new_rsvp = EventParticipant(event_id=event_id, user_id=session['user_id'], attendance_status=status)
        db.session.add(new_rsvp)
        
    db.session.commit()
    return redirect(url_for('events'))

# --- Queenw's Routes ---
@app.route('/study_partners', methods=['GET', 'POST'])
def study_partners():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        new_post = StudyPartnerPost(
            user_id=session['user_id'], # Using dynamic session ID
            title=request.form['course'], 
            goals=request.form['goals'],
            preferred_study_time=request.form['schedule'],
            current_topic=request.form['current_topic'],
            prep_goal=request.form['prep_goal'],
            study_style=request.form['study_style'],
            group_size=request.form['group_size'],
            status='open'
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('study_partners'))
    
    all_posts = StudyPartnerPost.query.order_by(StudyPartnerPost.id.desc()).all()
    return render_template('study_partners.html', partners=all_posts)

@app.route('/create_session/<int:post_id>', methods=['POST'])
def create_session(post_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    new_session = StudySession(
        created_by=session['user_id'], # Using dynamic session ID
        title=request.form['session_title'],
        session_date=request.form['session_date'],
        start_time=request.form['start_time'],
        location_text=request.form['location'],
        description=request.form['task_split']
    )
    db.session.add(new_session)
    
    post = StudyPartnerPost.query.get(post_id)
    if post:
        post.status = 'matched'
        
    db.session.commit()
    return redirect(url_for('study_partners')) 

@app.route('/start_chat/<string:c_type>/<int:c_id>')
def start_chat(c_type, c_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    existing_conv = Conversation.query.filter_by(context_type=c_type, context_id=c_id).first()
    
    if not existing_conv:
        new_conv = Conversation(
            title=f"Inquiry regarding {c_type}",
            context_type=c_type,
            context_id=c_id
        )
        db.session.add(new_conv)
        db.session.commit()
        
    return redirect(url_for('messages'))

@app.route('/messages', methods=['GET', 'POST'])
def messages():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    active_conv = Conversation.query.order_by(Conversation.id.desc()).first()
    
    if not active_conv:
        active_conv = Conversation(title="General Academic Chat")
        db.session.add(active_conv)
        db.session.commit()
        
    if request.method == 'POST':
        new_msg = Message(
            conversation_id=active_conv.id,
            sender_id=session['user_id'], # Using dynamic session ID
            message_text=request.form['content'],
            is_seen=0 
        )
        db.session.add(new_msg)
        db.session.commit()
        return redirect(url_for('messages'))
    
    chat_messages = Message.query.filter_by(conversation_id=active_conv.id).all()
    
    return render_template('messages.html', 
                           messages=chat_messages, 
                           active_conv=active_conv)

# --- NEW ROUTE: UNIFIED STUDENT DASHBOARD ---
@app.route('/dashboard')
def dashboard():
    login_redirect = require_login_redirect()
    #if 'user_id' not in session:
    if login_redirect:
        return redirect(url_for('login'))
        
    current_user_id = session['user_id']
    
    my_tutors = TutoringListing.query.filter_by(tutor_id=current_user_id).all()
    my_study_posts = StudyPartnerPost.query.filter_by(user_id=current_user_id).all()
    my_rsvps = EventParticipant.query.filter_by(user_id=current_user_id).all()
    my_notifications = Notification.query.filter_by(user_id=current_user_id).order_by(Notification.id.desc()).limit(5).all()
    

    stats = {
        "notes": Note.query.filter_by(uploader_id=current_user_id).count(),
        "deadlines": AcademicDeadline.query.filter_by(user_id=current_user_id).count(),
        "completed_deadlines": AcademicDeadline.query.filter_by(user_id=current_user_id, status="completed").count(),
        "upcoming_sessions": ScheduledStudySession.query.filter_by(created_by=current_user_id).count(),
    }

    return render_template('dashboard.html', 
                           tutors=my_tutors, 
                           study_posts=my_study_posts, 
                           rsvps=my_rsvps,
                           notifications=my_notifications,
                           stats=stats,)
with app.app_context():
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    db.create_all()

    
if __name__ == '__main__':
    app.run(debug=True)