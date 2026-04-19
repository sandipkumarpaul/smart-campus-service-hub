from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
# Connected to XAMPP MySQL Database
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
    email = db.Column(db.String(120), nullable=False)

# Queenw's Feature 1: Study Partner Finder
class StudyPartnerPost(db.Model):
    __tablename__ = 'study_partner_posts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    goals = db.Column(db.Text, nullable=True)
    preferred_study_time = db.Column(db.String(150), nullable=True)
    status = db.Column(db.String(50), default='open')
    user = db.relationship('User', backref='study_posts')

# Sandip's Feature 1: Tutoring Listings
class TutoringListing(db.Model):
    __tablename__ = 'tutoring_listings'
    id = db.Column(db.Integer, primary_key=True)
    tutor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject_title = db.Column(db.String(150), nullable=False)
    availability_text = db.Column(db.String(255))
    hourly_rate = db.Column(db.Numeric(10, 2), default=0.00)
    contact_info = db.Column(db.String(255))
    
    # ADD THIS LINE BACK IN:
    free_consult = db.Column(db.String(10), default='No')
    
    user = db.relationship('User', backref='tutoring_posts')

# Sandip's Feature 2: Campus Events
class CampusEvent(db.Model):
    __tablename__ = 'campus_events'
    id = db.Column(db.Integer, primary_key=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    event_date = db.Column(db.String(50), nullable=False) 
    location_text = db.Column(db.String(255))
    creator = db.relationship('User', backref='events')

# Queenw's Feature 2: Real-Time Messaging
class Conversation(db.Model):
    __tablename__ = 'conversations'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150))

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message_text = db.Column(db.Text)
    sender = db.relationship('User', backref='sent_messages')

# ==========================================
# ROUTES
# ==========================================

@app.route('/')
def home():
    return render_template('base.html')

# --- Sandip's Routes ---
@app.route('/tutors', methods=['GET', 'POST'])
def tutors():
    if request.method == 'POST':
        is_free = 'Yes' if request.form.get('free_consult') else 'No' 
        
        new_listing = TutoringListing(
            tutor_id=1, 
            subject_title=request.form['subject'],
            availability_text=request.form['availability'],
            hourly_rate=request.form['rate'],
            contact_info=request.form['contact'],
            free_consult=is_free # ADD THIS LINE
        )
        db.session.add(new_listing)
        db.session.commit()
        return redirect(url_for('tutors'))
    
    all_tutors = TutoringListing.query.all()
    return render_template('tutors.html', tutors=all_tutors)

@app.route('/events', methods=['GET', 'POST'])
def events():
    if request.method == 'POST':
        new_event = CampusEvent(
            created_by=1, # Hardcoded to Admin User
            title=request.form['title'],
            event_date=request.form['date'],
            location_text=request.form['location'],
            description=request.form['description']
        )
        db.session.add(new_event)
        db.session.commit()
        return redirect(url_for('events'))
    
    all_events = CampusEvent.query.all()
    return render_template('events.html', events=all_events)

# --- Queenw's Routes ---
@app.route('/study_partners', methods=['GET', 'POST'])
def study_partners():
    if request.method == 'POST':
        new_post = StudyPartnerPost(
            user_id=1, # Hardcoded to Admin User
            title=request.form['course'] + " Study Session",
            goals=request.form['goals'],
            preferred_study_time=request.form['schedule'],
            status='open'
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('study_partners'))
    
    all_posts = StudyPartnerPost.query.all()
    return render_template('study_partners.html', partners=all_posts)

@app.route('/messages', methods=['GET', 'POST'])
def messages():
    # A workaround to ensure a conversation exists since the DB requires it
    if not Conversation.query.first():
        new_conv = Conversation(title="General Chat")
        db.session.add(new_conv)
        db.session.commit()
        
    if request.method == 'POST':
        general_conv = Conversation.query.first()
        new_msg = Message(
            conversation_id=general_conv.id,
            sender_id=1, # Hardcoded to Admin User
            message_text=request.form['content']
        )
        db.session.add(new_msg)
        db.session.commit()
        return redirect(url_for('messages'))
    
    all_messages = Message.query.all()
    return render_template('messages.html', messages=all_messages)

if __name__ == '__main__':
    app.run(debug=True)