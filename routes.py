import json
import os
import re
import uuid
from datetime import datetime, timedelta
from flask import (
    current_app,
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
from sqlalchemy import func, text
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename
from urllib.parse import urlencode
from urllib.request import Request as UrlRequest, urlopen
from urllib.error import HTTPError, URLError

from models import (
    AcademicDeadline,
    Booking,
    CampusEvent,
    Conversation,
    DirectMessage,
    EventParticipant,
    Item,
    Message,
    Note,
    NoteRating,
    Notification,
    Report,
    Review,
    Ride,
    ScheduledStudySession,
    SkillExchange,
    SkillProposal,
    StudyPartner,
    StudyPartnerPost,
    StudySession,
    Tutor,
    TutorMessage,
    TutorProfileBooking,
    TutorReview,
    TutoringBooking,
    TutoringListing,
    User,
    db,
)

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


def _clean_env_value(value):
    if value is None:
        return None
    return value.strip().strip('"').strip("'")


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
ALLOWED_EXTENSIONS = {"pdf", "docx"}
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
GOOGLE_MAPS_API_KEY = _clean_env_value(os.environ.get("GOOGLE_MAPS_API_KEY")) or ""
OPENROUTESERVICE_API_KEY = _clean_env_value(os.environ.get("OPENROUTESERVICE_API_KEY")) or ""
DEFAULT_MAP_CENTER = (23.7806, 90.4070)

_routes = []


def route(*args, **kwargs):
    def decorator(view_func):
        _routes.append((args, kwargs, view_func))
        return view_func

    return decorator


def register_routes(app):
    app.context_processor(inject_globals)
    for rule_args, rule_options, view_func in _routes:
        app.add_url_rule(*rule_args, view_func=view_func, **rule_options)


def openrouteservice_api_key():
    return _clean_env_value(os.environ.get("OPENROUTESERVICE_API_KEY")) or OPENROUTESERVICE_API_KEY

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


def build_note_cards(notes, viewer_id=None):
    note_ids = [note.id for note in notes]
    uploader_ids = {note.uploader_id for note in notes}
    uploaders = {
        user.id: user
        for user in User.query.filter(User.id.in_(uploader_ids)).all()
    } if uploader_ids else {}

    rating_rows = []
    viewer_ratings = {}
    if note_ids:
        rating_rows = (
            db.session.query(
                NoteRating.note_id,
                func.avg(NoteRating.rating).label("average_rating"),
                func.count(NoteRating.id).label("rating_count"),
            )
            .filter(NoteRating.note_id.in_(note_ids))
            .group_by(NoteRating.note_id)
            .all()
        )
        if viewer_id:
            viewer_ratings = {
                rating.note_id: rating.rating
                for rating in NoteRating.query.filter(
                    NoteRating.note_id.in_(note_ids),
                    NoteRating.rater_id == viewer_id,
                ).all()
            }

    rating_summary = {
        note_id: {"average": float(average or 0), "count": count}
        for note_id, average, count in rating_rows
    }

    return [
        {
            "note": note,
            "uploader": uploaders.get(note.uploader_id),
            "rating": rating_summary.get(note.id, {"average": 0, "count": 0}),
            "viewer_rating": viewer_ratings.get(note.id),
            "can_rate": bool(viewer_id and note.uploader_id != viewer_id),
        }
        for note in notes
    ]


def inject_globals():
    current_user = None
    user_id = session.get("user_id")
    global_unread_count = 0
    if user_id:
        current_user = db.session.get(User, user_id)
        global_unread_count = Message.query.join(Conversation).filter(
            Message.sender_id != user_id,
            Message.is_seen == 0,
            (Conversation.participant1_id == user_id) | (Conversation.participant2_id == user_id),
        ).count()

    return {
        "available_views": set(current_app.view_functions.keys()),
        "current_user": current_user,
        "global_unread_count": global_unread_count,
        "google_maps_api_key": GOOGLE_MAPS_API_KEY,
        "openrouteservice_available": bool(openrouteservice_api_key()),
        "tutors_exists": "tutors" in current_app.view_functions,
        "map_view_exists": "map_view" in current_app.view_functions,
        "browse_rides_exists": "browse_rides" in current_app.view_functions,
    }


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


def trigger_notification(target_user_id, notif_type, title, message):
    new_notif = Notification(user_id=target_user_id, type=notif_type, title=title, message=message, is_read=False)
    db.session.add(new_notif)


def check_restrictions():
    if "user_id" in session:
        user = db.session.get(User, session["user_id"])
        if user and (user.is_banned or user.reputation_score < 0):
            return True
    return False

# ==========================================
# CENTRALIZED MYSQL MODELS
# ==========================================

# The Central Users Table

# ==========================================
# ROUTES
# ==========================================

@route("/")
def home():
    if "user_id" in session:
        # If logged in, go to dashboard
        return redirect(url_for("dashboard"))
    # If not logged in, go to login
    return redirect(url_for("login"))

# ==========================================
# AUTHENTICATION ROUTES
# ==========================================

@route('/register', methods=['GET', 'POST'])
def register():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))

    if request.method == 'POST':
        email = (request.form.get("email") or "").strip().lower()
        username = (request.form.get("username") or "").strip()
        full_name = (request.form.get("full_name") or "").strip()
        department = (request.form.get("department") or "").strip()
        password = request.form.get("password") or ""

        if not all([email, username, full_name, department, password]):
            flash("Please fill in all signup fields.", "danger")
            return redirect(url_for("register"))

        #hashed_pw = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
        # Check if email already exists
        existing_user = User.query.filter(
            (func.lower(User.email) == email) | (func.lower(User.username) == username.lower())
        ).first()
        if existing_user:
            flash("Email or username already registered. Please log in or use a different one.", "danger")
            return redirect(url_for("register"))

        hashed_pw = generate_password_hash(password, method="pbkdf2:sha256")
        new_user = User(
            full_name=full_name,
            username=username,
            email=email,
            password_hash=hashed_pw,
            department=department,
            major=department,

        )
        try:
            db.session.add(new_user)
            db.session.commit()
            session["user_id"] = new_user.id
            session["full_name"] = new_user.full_name
            session["user_major"] = new_user.major or new_user.department
            session["is_admin"] = new_user.is_admin
            flash("Registration successful. You are now logged in.", "success")
            return redirect(url_for("dashboard"))
        except IntegrityError:
            db.session.rollback()
            flash("An error occurred during registration. Please try again.", "danger")
            return redirect(url_for("register"))
        #db.session.add(new_user)
        #db.session.commit()
        #flash("Registration successful! Please log in.", "success")
        #return redirect(url_for('login'))
        
    return render_template('register.html')

@route('/login', methods=['GET', 'POST'])
def login():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))

    if request.method == 'POST':
        email = (request.form.get("email") or "").strip().lower()
        user = User.query.filter(func.lower(User.email) == email).first()
        
        if user and check_password_hash(user.password_hash, request.form.get("password", "")):
            session['user_id'] = user.id
            session['full_name'] = user.full_name
            session["user_major"] = user.major or user.department
            session["is_admin"] = user.is_admin
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password. Please try again.", "danger")
            
    return render_template('login.html')

@route('/logout')
def logout():
    session.clear() 
    return redirect(url_for('login'))


# ==========================================
# GOOGLE CALENDAR AUTH ROUTES
# ==========================================

@route("/auth")
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


@route("/callback")
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

@route("/upload", methods=["GET", "POST"])
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
        filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], unique_filename)
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


@route("/search", methods=["GET", "POST"])
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


@route("/download/<path:filename>")
def download_file(filename):
    login_redirect = require_login_redirect()
    if login_redirect:
        return login_redirect

    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename, as_attachment=True)


@route("/notes/<int:note_id>/rate", methods=["POST"])
def rate_note(note_id):
    login_redirect = require_login_redirect()
    if login_redirect:
        return login_redirect

    note = Note.query.get_or_404(note_id)
    rater_id = current_user_id()
    if note.uploader_id == rater_id:
        flash("You cannot rate your own note.", "warning")
        return redirect(request.referrer or url_for("dashboard"))

    try:
        rating_value = int(request.form.get("rating", 0))
    except ValueError:
        rating_value = 0

    if rating_value < 1 or rating_value > 5:
        flash("Please choose a rating between 1 and 5.", "danger")
        return redirect(request.referrer or url_for("dashboard"))

    existing_rating = NoteRating.query.filter_by(note_id=note.id, rater_id=rater_id).first()
    if existing_rating:
        existing_rating.rating = rating_value
    else:
        db.session.add(NoteRating(note_id=note.id, rater_id=rater_id, rating=rating_value))

    rater = db.session.get(User, rater_id)
    rater_name = rater.full_name if rater else "A student"
    db.session.add(Notification(
        user_id=note.uploader_id,
        type="note_rating",
        title="Your note received a rating",
        message=f"{rater_name} rated your note '{note.title}' {rating_value} out of 5.",
        related_table="notes",
        related_id=note.id,
    ))
    db.session.commit()

    flash("Thanks for rating this note.", "success")
    return redirect(request.referrer or url_for("dashboard"))


@route("/edit/<int:note_id>", methods=["GET", "POST"])
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


@route("/delete/<int:note_id>", methods=["POST"])
def delete_note(note_id):
    login_redirect = require_login_redirect()
    if login_redirect:
        return login_redirect

    note = Note.query.get_or_404(note_id)
    filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], note.file_path)
    if os.path.exists(filepath):
        os.remove(filepath)

    NoteRating.query.filter_by(note_id=note.id).delete()
    db.session.delete(note)
    db.session.commit()
    flash("Note deleted successfully.", "success")
    return redirect(url_for("search_notes"))


# ==========================================
# DIPTO'S ROUTES: DEADLINES AND STUDY SESSION API
# ==========================================

@route("/deadlines")
def deadlines():
    login_redirect = require_login_redirect()
    if login_redirect:
        return login_redirect

    all_deadlines = AcademicDeadline.query.filter_by(user_id=current_user_id()).order_by(
        AcademicDeadline.deadline_datetime.asc()
    ).all()
    return render_template("deadlines.html", deadlines=all_deadlines)


@route("/academic-dashboard")
def academic_dashboard():
    login_redirect = require_login_redirect()
    if login_redirect:
        return login_redirect

    user_id = current_user_id()
    all_notes = Note.query.order_by(Note.created_at.desc()).all()
    active_deadlines = (
        AcademicDeadline.query
        .filter_by(user_id=user_id, status="pending")
        .order_by(AcademicDeadline.deadline_datetime.asc())
        .all()
    )
    completed_deadlines = (
        AcademicDeadline.query
        .filter_by(user_id=user_id, status="completed")
        .order_by(AcademicDeadline.deadline_datetime.desc())
        .all()
    )
    scheduled_sessions = (
        ScheduledStudySession.query
        .filter_by(created_by=user_id)
        .order_by(ScheduledStudySession.session_date.asc(), ScheduledStudySession.start_time.asc())
        .all()
    )

    return render_template(
        "academic_dashboard.html",
        note_cards=build_note_cards(all_notes, viewer_id=user_id),
        active_deadlines=active_deadlines,
        completed_deadlines=completed_deadlines,
        scheduled_sessions=scheduled_sessions,
    )


@route("/deadlines/add", methods=["POST"])
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


@route("/deadlines/delete/<int:id>", methods=["POST"])
def delete_deadline(id):
    login_redirect = require_login_redirect()
    if login_redirect:
        return login_redirect

    deadline = AcademicDeadline.query.get_or_404(id)
    db.session.delete(deadline)
    db.session.commit()
    flash("Deadline removed.", "info")
    return redirect(url_for("deadlines"))


@route("/api/study-sessions", methods=["GET"])
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


@route("/api/study-sessions/create", methods=["POST"])
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
@route('/tutors', methods=['GET', 'POST'])
def tutors():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        if check_restrictions():
            flash("Your account is restricted from posting.", "danger")
            return redirect(url_for('dashboard'))

        listing_latitude = None
        listing_longitude = None
        listing_location = request.form.get('location')
        if listing_location:
            listing_latitude, listing_longitude = _best_effort_geocode(listing_location)

        is_free = 'Yes' if request.form.get('free_consult') else 'No' 
        try:
            safe_rate = float(request.form.get('rate', 0.00))
        except ValueError:
            safe_rate = 0.00
        
        new_listing = TutoringListing(
            tutor_id=session['user_id'], # Using dynamic session ID
            subject_title=request.form['subject'],
            teaching_style=request.form['teaching_style'],
            availability_text=request.form['availability'],
            mode=request.form['mode'],
            location_text=listing_location,
            latitude=listing_latitude,
            longitude=listing_longitude,
            rate_type=request.form['rate_type'],
            hourly_rate=safe_rate,
            free_consult=is_free
        )
        db.session.add(new_listing)
        db.session.commit()
        return redirect(url_for('tutors'))
    
    all_tutors = (
        TutoringListing.query
        .join(User)
        .filter(User.is_banned == False, TutoringListing.status == "Active")
        .order_by(TutoringListing.id.desc())
        .all()
    )
    my_reports = Report.query.filter_by(reporter_id=session['user_id'], reported_type='Tutor').all()
    reported_ids = [report.reported_id for report in my_reports]
    return render_template("tutors.html", tutors=all_tutors, reported_ids=reported_ids)


@route("/top-rated-tutors")
def top_rated_tutors():
    login_redirect = require_login_redirect()
    if login_redirect:
        return login_redirect

    department_query = (request.args.get("department") or session.get("user_major") or "").strip()
    subject_query = (request.args.get("subject") or "").strip()
    min_rating_query = (request.args.get("min_rating") or "").strip()

    query = (
        TutoringListing.query
        .join(User)
        .filter(User.is_banned == False, TutoringListing.status == "Active")
    )
    if department_query:
        query = query.filter(
            (func.lower(User.department) == department_query.lower()) |
            (func.lower(User.major) == department_query.lower())
        )
    if subject_query:
        query = query.filter(TutoringListing.subject_title.ilike(f"%{subject_query}%"))

    min_rating_value = None
    if min_rating_query:
        try:
            min_rating_value = float(min_rating_query)
        except ValueError:
            min_rating_value = None

    listings = query.all()
    if min_rating_value is not None:
        listings = [listing for listing in listings if listing.user.average_rating >= min_rating_value]
    listings.sort(key=lambda listing: (listing.user.average_rating, listing.user.review_count, listing.id), reverse=True)

    return render_template(
        "top_rated_tutors.html",
        tutors=listings,
        selected_department=department_query,
        selected_subject=subject_query,
        selected_min_rating=min_rating_query if min_rating_value is not None else "",
    )

@route('/book_tutor/<int:listing_id>', methods=['POST'])
def book_tutor(listing_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if check_restrictions():
        flash("Your account is restricted from making requests.", "danger")
        return redirect(url_for('tutors'))

    listing = db.session.get(TutoringListing, listing_id)
    if not listing:
        flash("This tutoring listing no longer exists.", "warning")
        return redirect(url_for("tutors"))
    if listing.tutor_id == session["user_id"]:
        flash("You cannot book your own tutoring service.", "danger")
        return redirect(url_for("tutors"))

    existing = TutoringBooking.query.filter_by(
        tutoring_listing_id=listing.id,
        student_id=session["user_id"],
    ).filter(TutoringBooking.status.in_(["Pending", "Accepted"])).first()
    if existing:
        flash("You already have an active request for this tutor.", "info")
        return redirect(url_for("tutors"))

    new_booking = TutoringBooking(
        tutoring_listing_id=listing_id,
        student_id=session['user_id'], # Using dynamic session ID
        session_date=request.form.get('session_date'),
        start_time=request.form.get('start_time'),
        note=request.form.get('note')
    )
    db.session.add(new_booking)
    trigger_notification(
        target_user_id=listing.tutor_id,
        notif_type="booking",
        title="New Tutoring Request",
        message=f"{session.get('full_name', 'A student')} requested a session for {listing.subject_title}! Check your Dashboard.",
    )
    db.session.commit()
    flash("Request sent to the tutor! They will respond via your Dashboard.", "success")
    return redirect(url_for('tutors'))


@route("/handle_tutor_request/<int:booking_id>/<string:action>", methods=["POST"])
def handle_tutor_request(booking_id, action):
    login_redirect = require_login_redirect()
    if login_redirect:
        return login_redirect

    booking = TutoringBooking.query.get_or_404(booking_id)
    if not booking.listing or booking.listing.tutor_id != session["user_id"]:
        flash("You are not authorized to manage this tutor request.", "danger")
        return redirect(url_for("dashboard"))

    if action == "accept":
        booking.status = "Accepted"
        existing_conv = Conversation.query.filter(
            ((Conversation.participant1_id == booking.student_id) & (Conversation.participant2_id == booking.listing.tutor_id)) |
            ((Conversation.participant1_id == booking.listing.tutor_id) & (Conversation.participant2_id == booking.student_id)),
            Conversation.context_type == "Tutor",
            Conversation.context_id == booking.listing.id,
        ).first()

        if not existing_conv:
            existing_conv = Conversation(
                participant1_id=booking.student_id,
                participant2_id=booking.listing.tutor_id,
                context_type="Tutor",
                context_id=booking.listing.id,
            )
            db.session.add(existing_conv)
            db.session.commit()

        trigger_notification(
            target_user_id=booking.student_id,
            notif_type="message",
            title="Tutor Request Accepted!",
            message=f"{session.get('full_name', 'Your tutor')} accepted your request. Chat now!",
        )
        flash("Request accepted! A chat has been created.", "success")
    elif action == "decline":
        booking.status = "Declined"
        trigger_notification(
            target_user_id=booking.student_id,
            notif_type="system",
            title="Request Declined",
            message=f"Your tutoring request for {booking.listing.subject_title} was declined.",
        )
        flash("Request declined.", "info")
    db.session.commit()
    return redirect(url_for("dashboard"))


@route("/submit_review/<int:reviewee_id>", methods=["POST"])
def submit_review(reviewee_id):
    login_redirect = require_login_redirect()
    if login_redirect:
        return login_redirect
    if check_restrictions():
        flash("Your account is restricted from reviewing.", "danger")
        return redirect(url_for("dashboard"))

    if reviewee_id == session["user_id"]:
        flash("You cannot review yourself.", "danger")
        return redirect(url_for("top_rated_tutors"))

    has_accepted_tutoring = (
        TutoringBooking.query
        .join(TutoringListing)
        .filter(
            TutoringBooking.student_id == session["user_id"],
            TutoringListing.tutor_id == reviewee_id,
            TutoringBooking.status == "Accepted",
        )
        .first()
    )
    has_skill = SkillProposal.query.join(SkillExchange).filter(
        ((SkillProposal.proposer_id == session["user_id"]) & (SkillExchange.user_id == reviewee_id)) |
        ((SkillProposal.proposer_id == reviewee_id) & (SkillExchange.user_id == session["user_id"])),
        SkillProposal.status == "Accepted",
    ).first()

    if not (has_accepted_tutoring or has_skill):
        flash("You can only review users you have successfully completed a service with.", "danger")
        return redirect(request.referrer or url_for("dashboard"))

    service_type = request.form.get("service_type") or "Tutoring"
    existing = Review.query.filter_by(
        reviewer_id=session["user_id"],
        reviewee_id=reviewee_id,
        service_type=service_type,
    ).first()
    if existing:
        flash("You have already submitted a review for this service.", "danger")
        return redirect(request.referrer or url_for("dashboard"))

    try:
        knowledge = max(1, min(5, int(request.form.get("knowledge", 5))))
        communication = max(1, min(5, int(request.form.get("communication", 5))))
        punctuality = max(1, min(5, int(request.form.get("punctuality", 5))))
    except ValueError:
        knowledge, communication, punctuality = 5, 5, 5

    review = Review(
        reviewer_id=session["user_id"],
        reviewee_id=reviewee_id,
        service_type=service_type,
        knowledge=knowledge,
        communication=communication,
        punctuality=punctuality,
        best_for=request.form.get("best_for", ""),
        feedback=request.form.get("feedback", ""),
        is_anonymous=bool(request.form.get("is_anonymous")),
    )
    db.session.add(review)
    trigger_notification(
        target_user_id=reviewee_id,
        notif_type="review",
        title="Detailed Review Received!",
        message="Someone just left you a verified review!",
    )
    db.session.commit()
    flash("Detailed review submitted! Thank you for building campus trust.", "success")
    return redirect(request.referrer or url_for("dashboard"))


@route("/read_notification/<int:notif_id>")
def read_notification(notif_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    notif = db.session.get(Notification, notif_id)
    target_url = url_for("dashboard")

    if notif and notif.user_id == session["user_id"]:
        notif.is_read = True
        db.session.commit()
        if notif.type == "message":
            target_url = url_for("messages")
        elif notif.type == "event":
            target_url = url_for("events")
        elif notif.type in ["booking", "review", "system"]:
            target_url = url_for("dashboard")

    return redirect(target_url)


@route("/all_notifications")
def all_notifications():
    if "user_id" not in session:
        return redirect(url_for("login"))

    notifications = Notification.query.filter_by(user_id=session["user_id"]).order_by(Notification.id.desc()).all()
    return render_template("all_notifications.html", notifications=notifications)


@route('/report', methods=['POST'])
def submit_report():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if check_restrictions():
        flash("Your account is restricted from submitting reports.", "danger")
        return redirect(url_for('dashboard'))

    try:
        reported_id = int(request.form['reported_id'])
    except (ValueError, KeyError):
        flash("Invalid report data.", "danger")
        return redirect(request.referrer or url_for('dashboard'))

    existing = Report.query.filter_by(
        reporter_id=session['user_id'],
        reported_type=request.form['reported_type'],
        reported_id=reported_id,
    ).first()
    if existing:
        flash("You have already reported this item. Our admin team is reviewing it.", "info")
        return redirect(request.referrer or url_for('dashboard'))

    new_report = Report(
        reporter_id=session['user_id'],
        reported_type=request.form['reported_type'],
        reported_id=reported_id,
        reason=request.form['reason'],
    )
    db.session.add(new_report)
    db.session.commit()

    trigger_notification(target_user_id=session['user_id'], notif_type='system', title='Report Logged', message=f"Ticket #{new_report.id}: Your report has been securely logged.")
    for admin in User.query.filter_by(is_admin=True).all():
        trigger_notification(target_user_id=admin.id, notif_type='system', title='New Moderation Ticket', message=f"A new report (#{new_report.id}) requires your review.")
    db.session.commit()

    flash("Report submitted successfully. Decision pending.", "success")
    return redirect(request.referrer or url_for('dashboard'))


@route('/admin/resolve/<int:report_id>/<string:action>', methods=['POST'])
def resolve_report(report_id, action):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if not session.get('is_admin'):
        return redirect(url_for('dashboard'))

    report = db.session.get(Report, report_id)
    if report and report.status == 'Pending':
        offender_id = None
        if report.reported_type == 'Tutor':
            item = db.session.get(TutoringListing, report.reported_id)
            if item:
                offender_id = item.tutor_id
                item.status = 'Banned'
        elif report.reported_type == 'Skill Exchange':
            item = db.session.get(SkillExchange, report.reported_id)
            if item:
                offender_id = item.user_id
                item.status = 'Banned'
        elif report.reported_type == 'Study Group':
            item = db.session.get(StudyPartnerPost, report.reported_id)
            if item:
                offender_id = item.user_id
                item.status = 'Banned'

        if action == 'approve':
            report.status = 'Approved (Banned)'
            if offender_id:
                offender = db.session.get(User, offender_id)
                if offender:
                    offender.is_banned = True
                    trigger_notification(target_user_id=offender.id, notif_type='system', title='Account Restricted', message="Your account has been restricted due to community guidelines violations.")
            trigger_notification(target_user_id=report.reporter_id, notif_type='system', title='Report Resolved', message=f"Action taken on Ticket #{report.id}. The user has been banned.")
            flash("Report approved and user banned.", "success")
        elif action == 'reject':
            report.status = 'Rejected (Penalty)'
            reporter = db.session.get(User, report.reporter_id)
            if reporter:
                reporter.trust_penalty += 20
                trigger_notification(target_user_id=report.reporter_id, notif_type='system', title='False Report Penalty', message=f"Ticket #{report.id} was rejected. A penalty has been applied to your Trust Score.")
            flash("Report rejected and reporter penalized.", "warning")

        db.session.commit()
    return redirect(url_for('admin_reports'))


@route('/admin/reports')
def admin_reports():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if not session.get('is_admin'):
        return redirect(url_for('dashboard'))
    reports = Report.query.order_by(Report.id.desc()).all()
    return render_template('admin_reports.html', reports=reports)


@route('/skill_exchange', methods=['GET', 'POST'])
def skill_exchange():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        if check_restrictions():
            flash("Your account is restricted from posting.", "danger")
            return redirect(url_for('dashboard'))
        new_skill = SkillExchange(
            user_id=session['user_id'],
            offering_skill=request.form['offering_skill'],
            seeking_skill=request.form['seeking_skill'],
            credibility=request.form.get('credibility', ''),
            description=request.form['description'],
            availability=request.form.get('availability', ''),
        )
        db.session.add(new_skill)
        db.session.commit()
        return redirect(url_for('skill_exchange'))

    skills = SkillExchange.query.join(User).filter(User.is_banned == False, SkillExchange.status == 'Active').order_by(SkillExchange.id.desc()).all()
    my_reports = Report.query.filter_by(reporter_id=session['user_id'], reported_type='Skill Exchange').all()
    reported_ids = [report.reported_id for report in my_reports]
    return render_template('skill_exchange.html', skills=skills, reported_ids=reported_ids)


@route('/propose_trade/<int:skill_id>', methods=['POST'])
def propose_trade(skill_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if check_restrictions():
        flash("Your account is restricted from making proposals.", "danger")
        return redirect(url_for('skill_exchange'))

    skill = db.session.get(SkillExchange, skill_id)
    if skill and skill.user_id != session['user_id']:
        existing = SkillProposal.query.filter_by(skill_id=skill.id, proposer_id=session['user_id']).first()
        if not existing:
            db.session.add(SkillProposal(skill_id=skill.id, proposer_id=session['user_id']))
            trigger_notification(target_user_id=skill.user_id, notif_type='system', title='New Trade Proposal!', message=f"{session.get('full_name', 'A student')} wants to trade skills! Check your Dashboard.")
            db.session.commit()
            flash("Proposal sent!", "success")
    return redirect(url_for('skill_exchange'))


@route('/handle_proposal/<int:proposal_id>/<string:action>', methods=['POST'])
def handle_proposal(proposal_id, action):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    proposal = db.session.get(SkillProposal, proposal_id)
    if not proposal or proposal.skill.user_id != session['user_id']:
        return redirect(url_for('dashboard'))

    if action == 'accept':
        proposal.status = 'Accepted'
        proposal.skill.status = 'Matched'
        existing_conv = Conversation.query.filter(
            ((Conversation.participant1_id == proposal.proposer_id) & (Conversation.participant2_id == proposal.skill.user_id)) |
            ((Conversation.participant1_id == proposal.skill.user_id) & (Conversation.participant2_id == proposal.proposer_id)),
            Conversation.context_type == 'Skill Exchange',
            Conversation.context_id == proposal.skill.id,
        ).first()
        if not existing_conv:
            db.session.add(Conversation(participant1_id=proposal.proposer_id, participant2_id=proposal.skill.user_id, context_type='Skill Exchange', context_id=proposal.skill.id))
            db.session.commit()
        trigger_notification(target_user_id=proposal.proposer_id, notif_type='message', title='Proposal Accepted!', message=f"{session.get('full_name', 'A student')} accepted your skill trade. Click here to chat!")
        flash("Proposal accepted! A chat has been created.", "success")
    elif action == 'decline':
        proposal.status = 'Declined'
        trigger_notification(target_user_id=proposal.proposer_id, notif_type='system', title='Proposal Declined', message=f"Your skill trade proposal for {proposal.skill.offering_skill} was declined.")
        flash("Proposal declined.", "info")

    db.session.commit()
    return redirect(url_for('dashboard'))


@route('/delete/<string:post_type>/<int:post_id>', methods=['POST'])
def delete_post(post_type, post_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    model_map = {
        'tutor': (TutoringListing, 'tutor_id'),
        'study': (StudyPartnerPost, 'user_id'),
        'skill': (SkillExchange, 'user_id'),
    }
    if post_type not in model_map:
        flash("Invalid post type.", "danger")
        return redirect(url_for('dashboard'))

    model, owner_field = model_map[post_type]
    post = db.session.get(model, post_id)
    if not post or getattr(post, owner_field) != session['user_id']:
        flash("You are not authorized to delete this post.", "danger")
        return redirect(url_for('dashboard'))

    post.status = 'Deleted'
    db.session.commit()
    redirect_map = {'tutor': 'tutors', 'study': 'study_partners', 'skill': 'skill_exchange'}
    flash("Your post has been deleted.", "success")
    return redirect(url_for(redirect_map[post_type]))

@route('/events', methods=['GET', 'POST'])
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

@route('/rsvp/<int:event_id>/<string:status>')
@route('/events/<int:event_id>/rsvp/<string:status>')
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
@route('/study_partners', methods=['GET', 'POST'])
@route('/study-partners', methods=['GET', 'POST'])
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
    
    all_posts = StudyPartnerPost.query.join(User).filter(User.is_banned == False).order_by(StudyPartnerPost.id.desc()).all()
    my_reports = Report.query.filter_by(reporter_id=session['user_id'], reported_type='Study Group').all()
    reported_ids = [report.reported_id for report in my_reports]
    return render_template('study_partners.html', partners=all_posts, reported_ids=reported_ids)

@route('/create_session/<int:post_id>', methods=['POST'])
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

@route('/start_chat/<string:c_type>/<int:c_id>')
def start_chat(c_type, c_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    receiver_id = None

    if c_type == "Tutor":
        listing = db.session.get(TutoringListing, c_id)
        if listing:
            receiver_id = listing.tutor_id
    elif c_type == "Study Partner":
        post = db.session.get(StudyPartnerPost, c_id)
        if post:
            receiver_id = post.user_id
    elif c_type == "Skill Exchange":
        skill = db.session.get(SkillExchange, c_id)
        if skill:
            receiver_id = skill.user_id

    if not receiver_id or receiver_id == session["user_id"]:
        flash("Cannot start a chat with this user.", "warning")
        return redirect(request.referrer or url_for("dashboard"))

    existing_conv = Conversation.query.filter(
        ((Conversation.participant1_id == session["user_id"]) & (Conversation.participant2_id == receiver_id)) |
        ((Conversation.participant1_id == receiver_id) & (Conversation.participant2_id == session["user_id"])),
        Conversation.context_type == c_type,
        Conversation.context_id == c_id,
    ).first()

    if not existing_conv:
        existing_conv = Conversation(
            participant1_id=session["user_id"],
            participant2_id=receiver_id,
            context_type=c_type,
            context_id=c_id,
        )
        db.session.add(existing_conv)
        db.session.commit()

    return redirect(url_for("messages", conv_id=existing_conv.id))

@route('/messages')
@route('/messages/<int:conv_id>', methods=['GET', 'POST'])
def messages(conv_id=None):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    current_user_id = session["user_id"]

    my_convs = Conversation.query.filter(
        (Conversation.participant1_id == current_user_id) |
        (Conversation.participant2_id == current_user_id)
    ).order_by(Conversation.id.desc()).all()
    active_conv = None

    if conv_id:
        active_conv = db.session.get(Conversation, conv_id)
        if active_conv and current_user_id not in [active_conv.participant1_id, active_conv.participant2_id]:
            active_conv = None
    elif my_convs:
        active_conv = my_convs[0]

    if request.method == 'POST' and active_conv:
        new_msg = Message(
            conversation_id=active_conv.id,
            sender_id=current_user_id,
            message_text=request.form.get('content', ''),
            is_seen=0 
        )
        db.session.add(new_msg)
        other_user = active_conv.get_other_user(current_user_id)
        if other_user:
            trigger_notification(
                target_user_id=other_user.id,
                notif_type="message",
                title="New Message",
                message=f"{session.get('full_name', 'Someone')} sent you a message!",
            )
        db.session.commit()
        return redirect(url_for('messages', conv_id=active_conv.id))

    if active_conv:
        unseen_msgs = Message.query.filter_by(conversation_id=active_conv.id, is_seen=0).filter(Message.sender_id != current_user_id).all()
        for msg in unseen_msgs:
            msg.is_seen = 1
        if unseen_msgs:
            db.session.commit()

    chat_messages = Message.query.filter_by(conversation_id=active_conv.id).all() if active_conv else []
    user = db.session.get(User, session["user_id"])
    direct_messages = []
    if user:
        identities = [value.lower() for value in (user.full_name, user.username, user.email) if value]
        direct_messages = (
            DirectMessage.query
            .filter(func.lower(DirectMessage.receiver).in_(identities))
            .order_by(DirectMessage.created_at.desc())
            .limit(20)
            .all()
        )
    
    return render_template('messages.html', 
                           conversations=my_convs,
                           messages=chat_messages, 
                           active_conv=active_conv,
                           direct_messages=direct_messages)


@route("/home")
def portal_home():
    login_redirect = require_login_redirect()
    if login_redirect:
        return login_redirect

    major = request.args.get("major") or session.get("user_major")
    tutor_query = TutoringListing.query.join(User).filter(TutoringListing.status == "Active")
    if major:
        tutor_query = tutor_query.filter(
            (func.lower(User.department) == major.lower()) |
            (func.lower(User.major) == major.lower())
        )
    top_tutors = tutor_query.all()
    top_tutors.sort(key=lambda listing: (listing.user.average_rating, listing.user.review_count, listing.id), reverse=True)
    top_tutors = top_tutors[:5]

    total_notes = Note.query.count()
    recent_notes = Note.query.order_by(Note.created_at.desc()).limit(5).all()
    return render_template("home.html", total_notes=total_notes, recent_notes=recent_notes, top_tutors=top_tutors)


@route("/db-health")
def db_health():
    try:
        with db.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return jsonify({"status": "ok", "database": "reachable"})
    except Exception as error:
        return jsonify({"status": "error", "database": "unreachable", "error": str(error)}), 503


@route("/browse")
def browse():
    search_query = (request.args.get("q") or "").strip()
    query = Item.query
    if search_query:
        query = query.filter(Item.title.ilike(f"%{search_query}%"))

    items = query.order_by(Item.created_at.desc()).all()
    return render_template("browse_items.html", items=items, search_query=search_query)


@route("/post", methods=["GET", "POST"])
def post_item():
    current_user = db.session.get(User, session.get("user_id")) if session.get("user_id") else None
    if not current_user:
        flash("Please log in to post an item.", "warning")
        return redirect(url_for("login"))

    if request.method == "POST":
        image_file = request.files.get("image")
        filename = None
        if image_file and image_file.filename:
            filename = secure_filename(image_file.filename)
            image_file.save(os.path.join(current_app.config["ITEM_UPLOAD_FOLDER"], filename))

        try:
            item = Item(
                title=request.form.get("title"),
                description=request.form.get("description"),
                price=float(request.form.get("price") or 0),
                condition=request.form.get("condition") or "Used",
                category=request.form.get("category") or "Other",
                image_filename=filename,
                seller_name=request.form.get("seller_name") or current_user.full_name,
                seller_email=request.form.get("seller_email") or current_user.email,
                seller_phone=request.form.get("seller_phone") or "",
                latitude=float(request.form.get("latitude")) if request.form.get("latitude") else None,
                longitude=float(request.form.get("longitude")) if request.form.get("longitude") else None,
            )
            db.session.add(item)
            db.session.commit()
            flash("Your item has been posted successfully.", "success")
            return redirect(url_for("my_listings"))
        except Exception as error:
            db.session.rollback()
            flash(f"Error posting item: {error}", "danger")
            return redirect(url_for("post_item"))

    return render_template("post_item.html", current_user=current_user)


@route("/my-listings")
def my_listings():
    current_user = db.session.get(User, session.get("user_id")) if session.get("user_id") else None
    if not current_user:
        flash("Please log in to view your listings.", "warning")
        return redirect(url_for("login"))

    items = Item.query.filter(func.lower(Item.seller_email) == current_user.email.lower()).order_by(Item.created_at.desc()).all()
    return render_template("my_listings.html", items=items, current_user=current_user)


@route("/item/<int:item_id>")
def item_details(item_id):
    item = Item.query.get_or_404(item_id)
    current_user = db.session.get(User, session.get("user_id")) if session.get("user_id") else None
    return render_template(
        "item_details.html",
        item=item,
        current_user=current_user,
    )


@route("/item/<int:item_id>/edit", methods=["GET", "POST"])
def edit_item(item_id):
    item = Item.query.get_or_404(item_id)
    current_user = db.session.get(User, session.get("user_id")) if session.get("user_id") else None
    user_email = current_user.email if current_user else (request.args.get("email") or request.form.get("email"))
    if not user_email:
        flash("Please log in to edit your item.", "warning")
        return redirect(url_for("login"))
    if user_email.lower() != item.seller_email.lower():
        flash("You are not authorized to edit this item.", "danger")
        return redirect(url_for("item_details", item_id=item.id))

    if request.method == "POST":
        try:
            item.title = request.form.get("title") or item.title
            item.description = request.form.get("description") or item.description
            item.price = float(request.form.get("price") or item.price)
            item.condition = request.form.get("condition") or item.condition
            item.category = request.form.get("category") or item.category
            item.seller_email = request.form.get("seller_email") or item.seller_email
            item.seller_phone = request.form.get("seller_phone") or item.seller_phone
            item.latitude = float(request.form.get("latitude")) if request.form.get("latitude") else item.latitude
            item.longitude = float(request.form.get("longitude")) if request.form.get("longitude") else item.longitude
            db.session.commit()
            flash("Item updated successfully.", "success")
            return redirect(url_for("item_details", item_id=item.id))
        except Exception as error:
            db.session.rollback()
            flash(f"Error updating item: {error}", "danger")

    return render_template("edit_item.html", item=item)


@route("/item/<int:item_id>/delete", methods=["POST"])
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    current_user = db.session.get(User, session.get("user_id")) if session.get("user_id") else None
    user_email = current_user.email if current_user else request.form.get("email")
    if not user_email:
        flash("Please log in to delete your item.", "warning")
        return redirect(url_for("login"))
    if user_email.lower() != item.seller_email.lower():
        flash("You are not authorized to delete this item.", "danger")
        return redirect(url_for("item_details", item_id=item.id))

    db.session.delete(item)
    db.session.commit()
    flash("Item deleted successfully.", "success")
    return redirect(url_for("my_listings"))


@route("/rides")
def browse_rides():
    query = Ride.query
    route_query = request.args.get("route")
    date_query = request.args.get("date")
    time_query = request.args.get("time")
    min_seats = request.args.get("min_seats")

    if route_query:
        query = query.filter((Ride.start_location.ilike(f"%{route_query}%")) | (Ride.destination.ilike(f"%{route_query}%")))
    if date_query:
        try:
            query = query.filter(Ride.travel_date == datetime.strptime(date_query, "%Y-%m-%d").date())
        except ValueError:
            pass
    if time_query:
        try:
            query = query.filter(Ride.travel_time == datetime.strptime(time_query, "%H:%M").time())
        except ValueError:
            pass
    if min_seats:
        try:
            query = query.filter(Ride.available_seats >= int(min_seats))
        except ValueError:
            pass

    rides = query.order_by(Ride.travel_date.asc(), Ride.travel_time.asc()).all()
    return render_template("rides.html", rides=rides)


@route("/rides/post", methods=["GET", "POST"])
def post_ride():
    current_user = db.session.get(User, session.get("user_id")) if session.get("user_id") else None
    if not current_user:
        flash("Please log in to post a ride.", "warning")
        return redirect(url_for("login"))

    if request.method == "POST":
        try:
            start_location = request.form.get("start_location")
            destination = request.form.get("destination")
            notes = request.form.get("notes")
            pickup_lat, pickup_lng, destination_lat, destination_lng = _resolve_ride_coordinates(
                start_location,
                destination,
                notes,
            )
            ride = Ride(
                user_id=current_user.username,
                start_location=start_location,
                destination=destination,
                travel_date=datetime.strptime(request.form.get("travel_date"), "%Y-%m-%d").date(),
                travel_time=datetime.strptime(request.form.get("travel_time"), "%H:%M").time(),
                available_seats=int(request.form.get("available_seats")),
                cost_share=float(request.form.get("cost_share")),
                notes=notes,
                contact_info=request.form.get("contact_info"),
                latitude=pickup_lat,
                longitude=pickup_lng,
                destination_latitude=destination_lat,
                destination_longitude=destination_lng,
            )
            db.session.add(ride)
            db.session.commit()
            flash("Your ride has been posted successfully.", "success")
            return redirect(url_for("ride_details", ride_id=ride.id))
        except Exception as error:
            db.session.rollback()
            flash(f"Error creating ride: {error}", "danger")

    return render_template("post_ride.html", current_user=current_user)


@route("/rides/<int:ride_id>")
def ride_details(ride_id):
    ride = Ride.query.get_or_404(ride_id)
    current_user = db.session.get(User, session.get("user_id")) if session.get("user_id") else None
    is_owner = bool(current_user and ride.user_id == current_user.username)
    return render_template("ride_details.html", ride=ride, current_user=current_user, is_owner=is_owner)


@route("/rides/<int:ride_id>/book", methods=["POST"])
def book_ride(ride_id):
    ride = Ride.query.get_or_404(ride_id)
    current_user = db.session.get(User, session.get("user_id")) if session.get("user_id") else None
    if not current_user:
        flash("Please log in to book a ride seat.", "warning")
        return redirect(url_for("login"))
    if ride.user_id == current_user.username:
        flash("You cannot book seats on your own ride post.", "danger")
        return redirect(url_for("ride_details", ride_id=ride.id))

    try:
        seats = int(request.form.get("seats", 1))
    except ValueError:
        flash("Please enter a valid seat count.", "danger")
        return redirect(url_for("ride_details", ride_id=ride.id))

    if seats < 1:
        flash("You must book at least one seat.", "danger")
        return redirect(url_for("ride_details", ride_id=ride.id))
    if seats > ride.available_seats:
        flash("Not enough seats available.", "danger")
        return redirect(url_for("ride_details", ride_id=ride.id))

    booking = Booking(
        ride_id=ride.id,
        user_id=current_user.username,
        seats_booked=seats,
        contact_info=(request.form.get("contact_info") or current_user.email).strip(),
    )
    ride.available_seats -= seats
    db.session.add(booking)
    db.session.commit()
    flash("Seat booked successfully.", "success")
    return redirect(url_for("ride_details", ride_id=ride.id))


@route("/rides/<int:ride_id>/edit", methods=["GET", "POST"])
def edit_ride(ride_id):
    ride = Ride.query.get_or_404(ride_id)
    current_user = db.session.get(User, session.get("user_id")) if session.get("user_id") else None
    if not current_user:
        flash("Please log in to edit your ride.", "warning")
        return redirect(url_for("login"))
    if ride.user_id != current_user.username:
        flash("You are not authorized to edit this ride.", "danger")
        return redirect(url_for("ride_details", ride_id=ride.id))

    if request.method == "POST":
        try:
            start_location = request.form.get("start_location")
            destination = request.form.get("destination")
            notes = request.form.get("notes")
            pickup_lat, pickup_lng, destination_lat, destination_lng = _resolve_ride_coordinates(
                start_location,
                destination,
                notes,
            )
            ride.start_location = start_location
            ride.destination = destination
            ride.travel_date = datetime.strptime(request.form.get("travel_date"), "%Y-%m-%d").date()
            ride.travel_time = datetime.strptime(request.form.get("travel_time"), "%H:%M").time()
            ride.available_seats = int(request.form.get("available_seats"))
            ride.cost_share = float(request.form.get("cost_share"))
            ride.notes = notes
            ride.contact_info = request.form.get("contact_info")
            ride.latitude = pickup_lat if pickup_lat is not None else ride.latitude
            ride.longitude = pickup_lng if pickup_lng is not None else ride.longitude
            ride.destination_latitude = destination_lat if destination_lat is not None else ride.destination_latitude
            ride.destination_longitude = destination_lng if destination_lng is not None else ride.destination_longitude
            db.session.commit()
            flash("Ride updated successfully.", "success")
            return redirect(url_for("ride_details", ride_id=ride.id))
        except Exception as error:
            db.session.rollback()
            flash(f"Error updating ride: {error}", "danger")

    return render_template("edit_ride.html", ride=ride)


@route("/rides/<int:ride_id>/delete", methods=["POST"])
def delete_ride(ride_id):
    ride = Ride.query.get_or_404(ride_id)
    current_user = db.session.get(User, session.get("user_id")) if session.get("user_id") else None
    if not current_user:
        flash("Please log in to delete your ride.", "warning")
        return redirect(url_for("login"))
    if ride.user_id != current_user.username:
        flash("You are not authorized to delete this ride.", "danger")
        return redirect(url_for("ride_details", ride_id=ride.id))

    db.session.delete(ride)
    db.session.commit()
    flash("Ride deleted successfully.", "success")
    return redirect(url_for("browse_rides"))


def _openrouteservice_request(url, method="GET", body=None):
    headers = {
        "Authorization": openrouteservice_api_key(),
        "Accept": "application/json, application/geo+json",
    }
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")

    request_obj = UrlRequest(url, data=data, headers=headers, method=method)
    with urlopen(request_obj, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def _query_mentions_local_area(query):
    return bool(re.search(r"dhaka|bangladesh|brac|bracu|badda|merul|mohakhali|banani|gulshan|bashundhara|uttara|dhanmondi|mirpur|farmgate", query, re.IGNORECASE))


def _clean_geocode_query(text_query):
    query = (text_query or "").strip()
    if not query:
        raise ValueError("Destination is required for routing.")
    return re.sub(r"\s+", " ", query)


def _geocode_search_candidates(text_query, context_parts=None):
    query = _clean_geocode_query(text_query)
    context = " ".join(part.strip() for part in (context_parts or []) if part and part.strip())
    candidates = []

    if context and context.lower() not in query.lower():
        candidates.append(f"{query}, {context}")
    candidates.append(query)
    if not _query_mentions_local_area(query):
        candidates.append(f"{query}, Dhaka, Bangladesh")

    seen = set()
    for candidate in candidates:
        key = candidate.lower()
        if key not in seen:
            seen.add(key)
            yield candidate


def _geocode_with_openrouteservice(text_query, context_parts=None):
    last_error = None
    for candidate in _geocode_search_candidates(text_query, context_parts=context_parts):
        query_args = {
            "text": candidate,
            "size": 5,
            "boundary.country": "BD",
            "focus.point.lat": DEFAULT_MAP_CENTER[0],
            "focus.point.lon": DEFAULT_MAP_CENTER[1],
        }
        url = f"https://api.openrouteservice.org/geocode/search?{urlencode(query_args)}"
        data = _openrouteservice_request(url)
        features = data.get("features") or []
        if not features:
            last_error = "Could not find that location."
            continue

        best_feature = features[0]
        coordinates = best_feature.get("geometry", {}).get("coordinates")
        if coordinates and len(coordinates) >= 2:
            return coordinates
        last_error = "Coordinates were not returned."

    raise ValueError(last_error or "Could not find that location.")


def _best_effort_geocode(text_query, context_parts=None):
    if not text_query or not openrouteservice_api_key():
        return None, None
    try:
        lng, lat = _geocode_with_openrouteservice(text_query, context_parts=context_parts)
        return lat, lng
    except Exception:
        return None, None


def _form_float(name):
    value = (request.form.get(name) or "").strip()
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _resolve_ride_coordinates(start_location, destination, notes=None):
    context_parts = [start_location, destination, notes]
    pickup_lat = _form_float("latitude")
    pickup_lng = _form_float("longitude")
    destination_lat = _form_float("destination_latitude")
    destination_lng = _form_float("destination_longitude")

    if pickup_lat is None or pickup_lng is None:
        pickup_lat, pickup_lng = _best_effort_geocode(start_location, context_parts=context_parts)
    if destination_lat is None or destination_lng is None:
        destination_lat, destination_lng = _best_effort_geocode(destination, context_parts=context_parts)

    return pickup_lat, pickup_lng, destination_lat, destination_lng


@route("/api/geocode")
def geocode_api():
    query = (request.args.get("q") or "").strip()
    if not query:
        return jsonify({"error": "Query text is required."}), 400
    if not openrouteservice_api_key():
        return jsonify({"error": "OpenRouteService API key is missing."}), 503

    try:
        context = (request.args.get("context") or "").strip()
        lng, lat = _geocode_with_openrouteservice(query, context_parts=[context])
        return jsonify({"lat": lat, "lng": lng}), 200
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except HTTPError:
        return jsonify({"error": "OpenRouteService rejected the geocoding request."}), 502
    except URLError:
        return jsonify({"error": "Could not reach OpenRouteService right now."}), 502
    except Exception:
        return jsonify({"error": "Geocoding failed unexpectedly."}), 500


@route("/api/rides/<int:ride_id>/route")
def ride_route_api(ride_id):
    if not openrouteservice_api_key():
        return jsonify({"error": "OpenRouteService API key is missing."}), 503

    current_user = db.session.get(User, session.get("user_id")) if session.get("user_id") else None
    if not current_user:
        return jsonify({"error": "Please log in to view ride routes."}), 401

    ride = Ride.query.get_or_404(ride_id)
    is_owner = ride.user_id == current_user.username
    has_booking = Booking.query.filter_by(ride_id=ride.id, user_id=current_user.username).first() is not None
    if not is_owner and not has_booking:
        return jsonify({"error": "You can only view routes for your own rides or rides you booked."}), 403

    if ride.latitude is None or ride.longitude is None:
        ride.latitude, ride.longitude, ride.destination_latitude, ride.destination_longitude = _resolve_ride_coordinates(
            ride.start_location,
            ride.destination,
            ride.notes,
        )
        db.session.commit()
    if ride.latitude is None or ride.longitude is None:
        return jsonify({"error": "This ride pickup location could not be found from the post details."}), 400

    try:
        source_coords = [ride.longitude, ride.latitude]
        destination_coords = (
            [ride.destination_longitude, ride.destination_latitude]
            if ride.destination_latitude is not None and ride.destination_longitude is not None
            else _geocode_with_openrouteservice(
                ride.destination,
                context_parts=[ride.start_location, ride.notes],
            )
        )
        route_data = _openrouteservice_request(
            "https://api.openrouteservice.org/v2/directions/driving-car/geojson",
            method="POST",
            body={"coordinates": [source_coords, destination_coords]},
        )
        if route_data.get("features"):
            feature = route_data["features"][0]
            coordinates = (feature.get("geometry") or {}).get("coordinates") or []
            if coordinates:
                if coordinates[0] != source_coords:
                    coordinates.insert(0, source_coords)
                if coordinates[-1] != destination_coords:
                    coordinates.append(destination_coords)
        route_data["metadata"] = {
            "source": source_coords,
            "destination": destination_coords,
            "start_location": ride.start_location,
            "destination_label": ride.destination,
        }
        return jsonify(route_data), 200
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except HTTPError:
        return jsonify({"error": "OpenRouteService rejected the routing request."}), 502
    except URLError:
        return jsonify({"error": "Could not reach OpenRouteService right now."}), 502
    except Exception:
        return jsonify({"error": "Route lookup failed unexpectedly."}), 500


@route("/map")
def map_view():
    current_user = db.session.get(User, session.get("user_id")) if session.get("user_id") else None
    if not current_user:
        return render_template("map.html", locations=[])

    own_rides = Ride.query.filter(
        Ride.latitude.isnot(None),
        Ride.longitude.isnot(None),
        func.lower(Ride.user_id) == current_user.username.lower(),
    ).order_by(Ride.updated_at.desc(), Ride.created_at.desc()).all()
    booked_ride_ids = [
        ride_id for (ride_id,) in (
            db.session.query(Booking.ride_id)
            .filter(func.lower(Booking.user_id) == current_user.username.lower())
            .distinct()
            .all()
        )
    ]
    booked_rides = []
    if booked_ride_ids:
        booked_rides = Ride.query.filter(
            Ride.id.in_(booked_ride_ids),
            Ride.latitude.isnot(None),
            Ride.longitude.isnot(None),
        ).order_by(Ride.updated_at.desc(), Ride.created_at.desc()).all()

    locations = []
    own_ride_ids = set()
    for ride in own_rides:
        own_ride_ids.add(ride.id)
        locations.append({
            "type": "ride",
            "id": ride.id,
            "title": f"Your ride to {ride.destination}",
            "details": f"Your post | Date: {ride.travel_date.strftime('%b %d')} | From {ride.start_location} to {ride.destination}",
            "start_location": ride.start_location,
            "destination": ride.destination,
            "lat": ride.latitude,
            "lng": ride.longitude,
            "destination_lat": ride.destination_latitude,
            "destination_lng": ride.destination_longitude,
        })
    for ride in booked_rides:
        if ride.id in own_ride_ids:
            continue
        locations.append({
            "type": "ride",
            "id": ride.id,
            "title": f"Booked ride to {ride.destination}",
            "details": f"Booked by you | Date: {ride.travel_date.strftime('%b %d')} | From {ride.start_location} to {ride.destination}",
            "start_location": ride.start_location,
            "destination": ride.destination,
            "lat": ride.latitude,
            "lng": ride.longitude,
            "destination_lat": ride.destination_latitude,
            "destination_lng": ride.destination_longitude,
        })

    return render_template("map.html", locations=locations)


@route("/post_tutor", methods=["GET", "POST"])
def post_tutor():
    current_user = db.session.get(User, session.get("user_id")) if session.get("user_id") else None
    if request.method == "POST":
        try:
            tutor = Tutor(
                name=request.form.get("name") or (current_user.full_name if current_user else ""),
                major=request.form.get("major") or request.form.get("subject"),
                subject=request.form.get("subject"),
                rating=0.0,
                review_count=0,
                bio=request.form.get("bio"),
                location=request.form.get("location"),
                latitude=float(request.form.get("latitude")) if request.form.get("latitude") else None,
                longitude=float(request.form.get("longitude")) if request.form.get("longitude") else None,
                contact_info=request.form.get("contact_info") or (current_user.email if current_user else "Not provided"),
            )
            db.session.add(tutor)
            db.session.commit()
            flash("Tutor posted successfully.", "success")
            return redirect(url_for("tutors"))
        except Exception as error:
            db.session.rollback()
            flash(f"Error posting tutor: {error}", "danger")

    return render_template("post_tutor.html", current_user=current_user)


@route("/tutors/<int:tutor_id>")
def tutor_details(tutor_id):
    tutor = Tutor.query.get_or_404(tutor_id)
    recent_reviews = TutorReview.query.filter_by(tutor_id=tutor.id).order_by(TutorReview.created_at.desc()).limit(5).all()
    return render_template("tutor_details.html", tutor=tutor, recent_reviews=recent_reviews)


@route("/tutors/<int:tutor_id>/book", methods=["POST"])
def book_tutor_profile(tutor_id):
    current_user = db.session.get(User, session.get("user_id")) if session.get("user_id") else None
    if not current_user:
        flash("Please log in to book a tutor slot.", "warning")
        return redirect(url_for("login"))

    tutor = Tutor.query.get_or_404(tutor_id)
    if current_user.email.lower() == tutor.contact_info.lower() or current_user.full_name.lower() == tutor.name.lower():
        flash("You cannot book your own tutor profile.", "danger")
        return redirect(url_for("tutors"))

    session_date = (request.form.get("session_date") or "").strip()
    start_time = (request.form.get("start_time") or "").strip()
    note = (request.form.get("note") or "").strip()
    if not session_date or not start_time or not note:
        flash("Please fill in date, time, and note for the tutor booking.", "danger")
        return redirect(url_for("tutors"))

    booking = TutorProfileBooking(
        tutor_id=tutor.id,
        student_id=current_user.id,
        session_date=session_date,
        start_time=start_time,
        note=note,
        status="pending",
    )
    db.session.add(booking)
    db.session.commit()
    flash(f"Your booking request has been sent to {tutor.name}.", "success")
    return redirect(url_for(
        "tutors",
        major=request.form.get("major", ""),
        subject=request.form.get("subject", ""),
        min_rating=request.form.get("min_rating", ""),
    ))


@route("/tutors/<int:tutor_id>/contact", methods=["GET", "POST"])
def tutor_contact(tutor_id):
    tutor = Tutor.query.get_or_404(tutor_id)
    if request.method == "POST":
        student_id = request.form.get("student_id")
        message = request.form.get("message")
        if not student_id or not message:
            flash("Please provide your identifier and a message.", "danger")
            return redirect(url_for("tutor_contact", tutor_id=tutor.id))
        db.session.add(TutorMessage(
            tutor_id=tutor.id,
            student_id=student_id,
            student_contact=request.form.get("student_contact"),
            subject=request.form.get("subject"),
            message=message,
        ))
        db.session.commit()
        flash("Message sent to tutor.", "success")
        return redirect(url_for("tutors"))

    return render_template("tutor_contact.html", tutor=tutor)


@route("/tutors/<int:tutor_id>/review", methods=["GET", "POST"])
def tutor_review(tutor_id):
    tutor = Tutor.query.get_or_404(tutor_id)
    if request.method == "POST":
        student_id = request.form.get("student_id")
        rating = int(request.form.get("rating", 0))
        if not student_id or rating < 1 or rating > 5:
            flash("Please provide a valid student id and rating between 1 and 5.", "danger")
            return redirect(url_for("tutor_review", tutor_id=tutor.id))

        review = TutorReview(
            tutor_id=tutor.id,
            student_id=student_id,
            rating=rating,
            review=request.form.get("review"),
        )
        total = (tutor.rating * tutor.review_count) + rating
        tutor.review_count += 1
        tutor.rating = total / tutor.review_count
        db.session.add(review)
        db.session.commit()
        flash("Thank you for your review.", "success")
        return redirect(url_for("tutors"))

    return render_template("tutor_review.html", tutor=tutor)


@route("/set-major", methods=["POST"])
def set_major():
    major = request.form.get("major")
    if major:
        session["user_major"] = major
        flash(f"Major set to {major} for recommendations.", "success")
    else:
        flash("Please provide a major.", "danger")
    return redirect(url_for("portal_home"))


@route("/api/events")
def get_events():
    events = CampusEvent.query.order_by(CampusEvent.id.desc()).all()
    return jsonify({
        "events": [
            {
                "id": event.id,
                "title": event.title,
                "category": event.category,
                "location": event.location_text,
                "date": event.event_date,
            }
            for event in events
        ]
    }), 200


@route("/api/study-partners")
def get_partners():
    partners = StudyPartnerPost.query.order_by(StudyPartnerPost.id.desc()).all()
    return jsonify({
        "study_partners": [
            {
                "id": partner.id,
                "name": partner.user.full_name if partner.user else "Student",
                "course": partner.title,
                "current_topic": partner.current_topic,
            }
            for partner in partners
        ]
    }), 200


@route("/api/messages", methods=["POST"])
def send_message():
    req_json = request.get_json(silent=True) or {}
    sender = req_json.get("sender")
    receiver = req_json.get("receiver")
    message_text = req_json.get("message")
    if not sender or not receiver or not message_text:
        return jsonify({"error": "sender, receiver, and message are required"}), 400

    message = DirectMessage(sender=sender, receiver=receiver, message=message_text)
    db.session.add(message)
    db.session.commit()
    return jsonify({"response": "Message Sent Successfully", "id": message.id}), 201


@route("/api/tutors", methods=["POST"])
def add_tutor():
    req_json = request.get_json(silent=True) or {}
    name = req_json.get("name")
    subject = req_json.get("subject")
    rate = req_json.get("rate")
    if not name or not subject or rate is None:
        return jsonify({"error": "name, subject, and rate are required"}), 400

    try:
        rating = float(rate)
    except (TypeError, ValueError):
        return jsonify({"error": "rate must be numeric"}), 400

    tutor = Tutor(
        name=name,
        major=req_json.get("major") or subject,
        subject=subject,
        rating=rating,
        review_count=int(req_json.get("review_count") or 1),
        bio=req_json.get("bio") or "Tutor listing imported from the API.",
        location=req_json.get("location"),
        contact_info=req_json.get("contact") or req_json.get("contact_info") or "Not provided",
    )
    db.session.add(tutor)
    db.session.commit()
    return jsonify({"response": "Tutor Listing Created Successfully", "id": tutor.id}), 201

# --- NEW ROUTE: UNIFIED STUDENT DASHBOARD ---
@route('/dashboard')
def dashboard():
    login_redirect = require_login_redirect()
    #if 'user_id' not in session:
    if login_redirect:
        return redirect(url_for('login'))
        
    current_user_id = session['user_id']
    current_user = db.session.get(User, current_user_id)
    if not current_user:
        session.clear()
        flash("Your session has expired. Please log in again.", "warning")
        return redirect(url_for("login"))
    
    my_tutors = TutoringListing.query.filter_by(tutor_id=current_user_id).all()
    my_study_posts = StudyPartnerPost.query.filter_by(user_id=current_user_id).all()
    my_skills = SkillExchange.query.filter_by(user_id=current_user_id).all()
    my_rsvps = EventParticipant.query.filter_by(user_id=current_user_id).all()
    my_reports = Report.query.filter_by(reporter_id=current_user_id).order_by(Report.id.desc()).all()
    my_notifications = (
        Notification.query
        .filter_by(user_id=current_user_id)
        .order_by(Notification.id.desc())
        .limit(5)
        .all()
    )
    unread_count = Notification.query.filter_by(user_id=current_user_id, is_read=False).count()
    all_notes = Note.query.order_by(Note.created_at.desc()).all()
    my_items = Item.query.filter(func.lower(Item.seller_email) == current_user.email.lower()).order_by(Item.created_at.desc()).limit(5).all()
    my_rides = Ride.query.filter(func.lower(Ride.user_id) == current_user.username.lower()).order_by(Ride.travel_date.asc(), Ride.travel_time.asc()).limit(5).all()
    incoming_tutor_requests = (
        TutoringBooking.query
        .join(TutoringListing)
        .filter(TutoringListing.tutor_id == current_user_id, TutoringBooking.status == "Pending")
        .order_by(TutoringBooking.id.desc())
        .all()
    )
    incoming_proposals = (
        SkillProposal.query
        .join(SkillExchange)
        .filter(SkillExchange.user_id == current_user_id, SkillProposal.status == "Pending")
        .all()
    )
    message_identities = [value.lower() for value in (current_user.email, current_user.username, current_user.full_name) if value]
    direct_messages = (
        DirectMessage.query
        .filter(func.lower(DirectMessage.receiver).in_(message_identities))
        .order_by(DirectMessage.created_at.desc())
        .limit(5)
        .all()
    )
    booked_ride_ids = [
        ride_id for (ride_id,) in (
            db.session.query(Booking.ride_id)
            .filter(func.lower(Booking.user_id) == current_user.username.lower())
            .distinct()
            .all()
        )
    ]
    own_mapped_rides_count = Ride.query.filter(
        Ride.latitude.isnot(None),
        Ride.longitude.isnot(None),
        func.lower(Ride.user_id) == current_user.username.lower(),
    ).count()
    booked_mapped_rides_count = 0
    if booked_ride_ids:
        booked_mapped_rides_count = Ride.query.filter(
            Ride.id.in_(booked_ride_ids),
            Ride.latitude.isnot(None),
            Ride.longitude.isnot(None),
            func.lower(Ride.user_id) != current_user.username.lower(),
        ).count()
    map_counts = {
        "items": 0,
        "rides": own_mapped_rides_count + booked_mapped_rides_count,
        "tutors": 0,
    }
    

    stats = {
        "notes": Note.query.filter_by(uploader_id=current_user_id).count(),
        "deadlines": AcademicDeadline.query.filter_by(user_id=current_user_id).count(),
        "completed_deadlines": AcademicDeadline.query.filter_by(user_id=current_user_id, status="completed").count(),
        "upcoming_sessions": ScheduledStudySession.query.filter_by(created_by=current_user_id).count(),
        "items": Item.query.filter(func.lower(Item.seller_email) == current_user.email.lower()).count(),
        "rides": Ride.query.filter(func.lower(Ride.user_id) == current_user.username.lower()).count(),
        "top_tutors": TutoringListing.query.filter_by(tutor_id=current_user_id).count(),
        "messages": len(direct_messages),
    }

    return render_template('dashboard.html', 
                           user=current_user,
                           tutors=my_tutors, 
                           incoming_tutor_requests=incoming_tutor_requests,
                           incoming_proposals=incoming_proposals,
                           study_posts=my_study_posts, 
                           skills=my_skills,
                           rsvps=my_rsvps,
                           reports=my_reports,
                           notifications=my_notifications,
                           unread_count=unread_count,
                           note_cards=build_note_cards(all_notes, viewer_id=current_user_id),
                           stats=stats,
                           items=my_items,
                           rides=my_rides,
                           direct_messages=direct_messages,
                           map_counts=map_counts)

