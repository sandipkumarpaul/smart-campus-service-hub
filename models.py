from datetime import datetime
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(50), unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    department = db.Column(db.String(100))
    major = db.Column(db.String(100))
    is_admin = db.Column(db.Boolean, default=False)
    is_banned = db.Column(db.Boolean, default=False)
    trust_penalty = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def review_count(self):
        return len(self.received_reviews)

    @property
    def average_rating(self):
        if self.review_count == 0:
            return 0
        total_score = sum((review.knowledge + review.communication + review.punctuality) / 3 for review in self.received_reviews)
        return round(total_score / self.review_count, 1)

    @property
    def top_tag(self):
        tags = [review.best_for for review in self.received_reviews if review.best_for]
        return max(set(tags), key=tags.count) if tags else None

    @property
    def reputation_score(self):
        score = 0
        if self.review_count:
            score += self.average_rating * 10
            score += self.review_count * 5
        score += len(self.skill_posts) * 10
        score += len(self.tutoring_posts) * 10
        return int(score) - (self.trust_penalty or 0)

    @property
    def trust_badge(self):
        score = self.reputation_score
        if score < 0:
            return "Restricted User"
        if score >= 100:
            return "Campus Ambassador"
        if score >= 50:
            return "Trusted Peer"
        if score >= 20:
            return "Active Contributor"
        return "New Member"

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


# Compatibility name used by the 24_april_final_scsh tests/modules.
StudyPartner = StudyPartnerPost

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
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    rate_type = db.Column(db.String(50), default='Paid') 
    hourly_rate = db.Column(db.Numeric(10, 2), default=0.00)
    free_consult = db.Column(db.String(10), default='No')
    status = db.Column(db.String(50), default='Active')
    
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
    status = db.Column(db.String(50), default='Pending')

    student = db.relationship('User', foreign_keys=[student_id])

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
    participant1_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    participant2_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    context_type = db.Column(db.String(50)) 
    context_id = db.Column(db.Integer)      
    p1 = db.relationship('User', foreign_keys=[participant1_id])
    p2 = db.relationship('User', foreign_keys=[participant2_id])
    messages = db.relationship('Message', backref='conversation', lazy=True, cascade="all, delete-orphan")

    def get_other_user(self, current_user_id):
        return self.p2 if self.participant1_id == current_user_id else self.p1

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
    related_table = db.Column(db.String(100))
    related_id = db.Column(db.Integer)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Report(db.Model):
    __tablename__ = 'reports'
    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reported_type = db.Column(db.String(50), nullable=False)
    reported_id = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='Pending')
    reporter = db.relationship('User', backref='submitted_reports')


class SkillExchange(db.Model):
    __tablename__ = 'skill_exchanges'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    offering_skill = db.Column(db.String(150), nullable=False)
    seeking_skill = db.Column(db.String(150), nullable=False)
    credibility = db.Column(db.String(255))
    description = db.Column(db.Text, nullable=False)
    availability = db.Column(db.String(100))
    status = db.Column(db.String(50), default='Active')
    user = db.relationship('User', backref='skill_posts')


class SkillProposal(db.Model):
    __tablename__ = 'skill_proposals'
    id = db.Column(db.Integer, primary_key=True)
    skill_id = db.Column(db.Integer, db.ForeignKey('skill_exchanges.id'), nullable=False)
    proposer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(50), default='Pending')
    skill = db.relationship('SkillExchange', backref='proposals')
    proposer = db.relationship('User', foreign_keys=[proposer_id])


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

class NoteRating(db.Model):
    __tablename__ = "note_ratings"
    __table_args__ = (
        db.UniqueConstraint("note_id", "rater_id", name="uq_note_rating_user"),
        {'mysql_engine': 'InnoDB'},
    )

    id = db.Column(db.Integer, primary_key=True)
    note_id = db.Column(db.Integer, db.ForeignKey("notes.id"), nullable=False)
    rater_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
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
    created_by = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    session_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    mode = db.Column(db.String(20), default="both")
    location_text = db.Column(db.String(255))
    meeting_link = db.Column(db.String(255))
    status = db.Column(db.String(20), default="scheduled")


# Dipto's merged modules from 24_april_final_scsh
class Item(db.Model):
    __tablename__ = "items"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    condition = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    image_filename = db.Column(db.String(255))
    seller_name = db.Column(db.String(100), nullable=False)
    seller_email = db.Column(db.String(120), nullable=False)
    seller_phone = db.Column(db.String(20))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Ride(db.Model):
    __tablename__ = "rides"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False)
    start_location = db.Column(db.String(255), nullable=False)
    destination = db.Column(db.String(255), nullable=False)
    travel_date = db.Column(db.Date, nullable=False)
    travel_time = db.Column(db.Time, nullable=False)
    available_seats = db.Column(db.Integer, nullable=False)
    cost_share = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text)
    contact_info = db.Column(db.String(150), nullable=False)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    destination_latitude = db.Column(db.Float)
    destination_longitude = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Booking(db.Model):
    __tablename__ = "bookings"
    id = db.Column(db.Integer, primary_key=True)
    ride_id = db.Column(db.Integer, db.ForeignKey("rides.id"), nullable=False)
    user_id = db.Column(db.String(100), nullable=False)
    seats_booked = db.Column(db.Integer, nullable=False, default=1)
    contact_info = db.Column(db.String(150))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    ride = db.relationship("Ride", backref=db.backref("bookings", lazy=True))


class DirectMessage(db.Model):
    __tablename__ = "direct_messages"
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(100), nullable=False)
    receiver = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    context_type = db.Column(db.String(80))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Review(db.Model):
    __tablename__ = "reviews"
    id = db.Column(db.Integer, primary_key=True)
    reviewer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    reviewee_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    service_type = db.Column(db.String(50))
    knowledge = db.Column(db.Integer, nullable=False, default=5)
    communication = db.Column(db.Integer, nullable=False, default=5)
    punctuality = db.Column(db.Integer, nullable=False, default=5)
    best_for = db.Column(db.String(100))
    feedback = db.Column(db.Text)
    is_anonymous = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    reviewer = db.relationship("User", foreign_keys=[reviewer_id], backref="given_reviews")
    reviewee = db.relationship("User", foreign_keys=[reviewee_id], backref="received_reviews")


class Tutor(db.Model):
    __tablename__ = "tutors"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    major = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Float, nullable=False, default=0.0)
    review_count = db.Column(db.Integer, nullable=False, default=0)
    bio = db.Column(db.Text)
    location = db.Column(db.String(255))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    contact_info = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class TutorMessage(db.Model):
    __tablename__ = "tutor_messages"
    id = db.Column(db.Integer, primary_key=True)
    tutor_id = db.Column(db.Integer, db.ForeignKey("tutors.id"), nullable=False)
    student_id = db.Column(db.String(120), nullable=False)
    student_contact = db.Column(db.String(150))
    subject = db.Column(db.String(200))
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    tutor = db.relationship("Tutor", backref=db.backref("messages", lazy=True))


class TutorReview(db.Model):
    __tablename__ = "tutor_reviews"
    id = db.Column(db.Integer, primary_key=True)
    tutor_id = db.Column(db.Integer, db.ForeignKey("tutors.id"), nullable=False)
    student_id = db.Column(db.String(120), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    review = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    tutor = db.relationship("Tutor", backref=db.backref("reviews", lazy=True))


class TutorProfileBooking(db.Model):
    __tablename__ = "tutor_profile_bookings"
    id = db.Column(db.Integer, primary_key=True)
    tutor_id = db.Column(db.Integer, nullable=False)
    student_id = db.Column(db.Integer, nullable=False)
    session_date = db.Column(db.String(50))
    start_time = db.Column(db.String(50))
    note = db.Column(db.Text)
    status = db.Column(db.String(50), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


