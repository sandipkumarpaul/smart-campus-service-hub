from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
# Connected to XAMPP MySQL Database
app.config['SECRET_KEY'] = 'bracu_smart_campus_secure_key_2026' 
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/smart_campus_service_hub'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

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

# ==========================================
# ROUTES
# ==========================================

@app.route('/')
def home():
    return render_template('base.html')

# ==========================================
# AUTHENTICATION ROUTES
# ==========================================

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        hashed_pw = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
        
        new_user = User(
            full_name=request.form['full_name'],
            username=request.form['username'],
            email=request.form['email'],
            password_hash=hashed_pw,
            department=request.form['department']
        )
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for('login'))
        
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
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    current_user_id = session['user_id']
    
    my_tutors = TutoringListing.query.filter_by(tutor_id=current_user_id).all()
    my_study_posts = StudyPartnerPost.query.filter_by(user_id=current_user_id).all()
    my_rsvps = EventParticipant.query.filter_by(user_id=current_user_id).all()
    my_notifications = Notification.query.filter_by(user_id=current_user_id).order_by(Notification.id.desc()).limit(5).all()
    
    return render_template('dashboard.html', 
                           tutors=my_tutors, 
                           study_posts=my_study_posts, 
                           rsvps=my_rsvps,
                           notifications=my_notifications)

if __name__ == '__main__':
    app.run(debug=True)