import os

from flask import Flask
from sqlalchemy import inspect, text

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

from models import db
from routes import register_routes

if load_dotenv:
    load_dotenv(override=False)


def clean_env_value(value):
    if value is None:
        return None
    return value.strip().strip('"').strip("'")


def env_or_default(name, default):
    value = clean_env_value(os.environ.get(name))
    return default if value is None else value


def build_database_uri():
    database_url = clean_env_value(os.environ.get("DATABASE_URL"))
    if database_url:
        return database_url

    db_user = env_or_default("DB_USER", "root")
    db_password = env_or_default("DB_PASS", "12345")
    db_host = env_or_default("DB_HOST", "localhost")
    db_port = env_or_default("DB_PORT", "3306")
    db_name = env_or_default("DB_NAME", "smart_campus_service_hub_s")
    return f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?charset=utf8mb4"


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
STATIC_UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(STATIC_UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "bracu_smart_campus_secure_key_2026")
app.config["SQLALCHEMY_DATABASE_URI"] = build_database_uri()
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["ITEM_UPLOAD_FOLDER"] = STATIC_UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

db.init_app(app)
register_routes(app)

_database_ready = False


def sync_database_schema():
    inspector = inspect(db.engine)
    expected_columns = {
        "users": {
            "department": "ALTER TABLE users ADD COLUMN department VARCHAR(100) NULL",
            "major": "ALTER TABLE users ADD COLUMN major VARCHAR(100) NULL",
            "is_admin": "ALTER TABLE users ADD COLUMN is_admin BOOLEAN NULL DEFAULT 0",
            "is_banned": "ALTER TABLE users ADD COLUMN is_banned BOOLEAN NULL DEFAULT 0",
            "trust_penalty": "ALTER TABLE users ADD COLUMN trust_penalty INTEGER NULL DEFAULT 0",
            "created_at": "ALTER TABLE users ADD COLUMN created_at DATETIME NULL",
        },
        "study_partner_posts": {
            "goals": "ALTER TABLE study_partner_posts ADD COLUMN goals TEXT NULL",
            "preferred_study_time": "ALTER TABLE study_partner_posts ADD COLUMN preferred_study_time VARCHAR(150) NULL",
            "current_topic": "ALTER TABLE study_partner_posts ADD COLUMN current_topic VARCHAR(150) NULL",
            "prep_goal": "ALTER TABLE study_partner_posts ADD COLUMN prep_goal VARCHAR(50) NULL",
            "study_style": "ALTER TABLE study_partner_posts ADD COLUMN study_style VARCHAR(50) NULL",
            "group_size": "ALTER TABLE study_partner_posts ADD COLUMN group_size INTEGER NOT NULL DEFAULT 2",
            "status": "ALTER TABLE study_partner_posts ADD COLUMN status VARCHAR(50) NOT NULL DEFAULT 'open'",
        },
        "study_sessions": {
            "description": "ALTER TABLE study_sessions ADD COLUMN description TEXT NULL",
            "location_text": "ALTER TABLE study_sessions ADD COLUMN location_text VARCHAR(255) NULL",
            "status": "ALTER TABLE study_sessions ADD COLUMN status VARCHAR(50) NOT NULL DEFAULT 'scheduled'",
        },
        "tutoring_listings": {
            "teaching_style": "ALTER TABLE tutoring_listings ADD COLUMN teaching_style TEXT NULL",
            "availability_text": "ALTER TABLE tutoring_listings ADD COLUMN availability_text VARCHAR(255) NULL",
            "mode": "ALTER TABLE tutoring_listings ADD COLUMN mode VARCHAR(50) NOT NULL DEFAULT 'both'",
            "location_text": "ALTER TABLE tutoring_listings ADD COLUMN location_text VARCHAR(255) NULL",
            "latitude": "ALTER TABLE tutoring_listings ADD COLUMN latitude FLOAT NULL",
            "longitude": "ALTER TABLE tutoring_listings ADD COLUMN longitude FLOAT NULL",
            "rate_type": "ALTER TABLE tutoring_listings ADD COLUMN rate_type VARCHAR(50) NOT NULL DEFAULT 'Paid'",
            "hourly_rate": "ALTER TABLE tutoring_listings ADD COLUMN hourly_rate DECIMAL(10, 2) NOT NULL DEFAULT 0.00",
            "free_consult": "ALTER TABLE tutoring_listings ADD COLUMN free_consult VARCHAR(10) NOT NULL DEFAULT 'No'",
            "status": "ALTER TABLE tutoring_listings ADD COLUMN status VARCHAR(50) NOT NULL DEFAULT 'Active'",
        },
        "tutoring_bookings": {
            "session_date": "ALTER TABLE tutoring_bookings ADD COLUMN session_date VARCHAR(50) NULL",
            "start_time": "ALTER TABLE tutoring_bookings ADD COLUMN start_time VARCHAR(50) NULL",
            "note": "ALTER TABLE tutoring_bookings ADD COLUMN note TEXT NULL",
            "status": "ALTER TABLE tutoring_bookings ADD COLUMN status VARCHAR(50) NOT NULL DEFAULT 'pending'",
        },
        "tutor_profile_bookings": {
            "session_date": "ALTER TABLE tutor_profile_bookings ADD COLUMN session_date VARCHAR(50) NULL",
            "start_time": "ALTER TABLE tutor_profile_bookings ADD COLUMN start_time VARCHAR(50) NULL",
            "note": "ALTER TABLE tutor_profile_bookings ADD COLUMN note TEXT NULL",
            "status": "ALTER TABLE tutor_profile_bookings ADD COLUMN status VARCHAR(50) NOT NULL DEFAULT 'pending'",
            "created_at": "ALTER TABLE tutor_profile_bookings ADD COLUMN created_at DATETIME NULL",
        },
        "campus_events": {
            "target_audience": "ALTER TABLE campus_events ADD COLUMN target_audience VARCHAR(100) NOT NULL DEFAULT 'Open to all'",
            "capacity_limit": "ALTER TABLE campus_events ADD COLUMN capacity_limit INTEGER NOT NULL DEFAULT 0",
            "recap_text": "ALTER TABLE campus_events ADD COLUMN recap_text TEXT NULL",
            "status": "ALTER TABLE campus_events ADD COLUMN status VARCHAR(50) NOT NULL DEFAULT 'upcoming'",
        },
        "event_participants": {
            "attendance_status": "ALTER TABLE event_participants ADD COLUMN attendance_status VARCHAR(50) NOT NULL DEFAULT 'interested'",
        },
        "conversations": {
            "conversation_type": "ALTER TABLE conversations ADD COLUMN conversation_type VARCHAR(50) NOT NULL DEFAULT 'private'",
            "participant1_id": "ALTER TABLE conversations ADD COLUMN participant1_id INTEGER NULL",
            "participant2_id": "ALTER TABLE conversations ADD COLUMN participant2_id INTEGER NULL",
            "context_type": "ALTER TABLE conversations ADD COLUMN context_type VARCHAR(50) NULL",
            "context_id": "ALTER TABLE conversations ADD COLUMN context_id INTEGER NULL",
        },
        "messages": {
            "message_text": "ALTER TABLE messages ADD COLUMN message_text TEXT NULL",
            "is_seen": "ALTER TABLE messages ADD COLUMN is_seen INTEGER NOT NULL DEFAULT 0",
        },
        "notifications": {
            "related_table": "ALTER TABLE notifications ADD COLUMN related_table VARCHAR(100) NULL",
            "related_id": "ALTER TABLE notifications ADD COLUMN related_id INTEGER NULL",
            "is_read": "ALTER TABLE notifications ADD COLUMN is_read BOOLEAN NOT NULL DEFAULT 0",
            "created_at": "ALTER TABLE notifications ADD COLUMN created_at DATETIME NULL",
        },
        "items": {
            "latitude": "ALTER TABLE items ADD COLUMN latitude FLOAT NULL",
            "longitude": "ALTER TABLE items ADD COLUMN longitude FLOAT NULL",
        },
        "rides": {
            "destination_latitude": "ALTER TABLE rides ADD COLUMN destination_latitude FLOAT NULL",
            "destination_longitude": "ALTER TABLE rides ADD COLUMN destination_longitude FLOAT NULL",
            "updated_at": "ALTER TABLE rides ADD COLUMN updated_at DATETIME NULL",
        },
        "direct_messages": {
            "context_type": "ALTER TABLE direct_messages ADD COLUMN context_type VARCHAR(80) NULL",
            "created_at": "ALTER TABLE direct_messages ADD COLUMN created_at DATETIME NULL",
        },
        "tutors": {
            "latitude": "ALTER TABLE tutors ADD COLUMN latitude FLOAT NULL",
            "longitude": "ALTER TABLE tutors ADD COLUMN longitude FLOAT NULL",
            "review_count": "ALTER TABLE tutors ADD COLUMN review_count INTEGER NOT NULL DEFAULT 0",
            "location": "ALTER TABLE tutors ADD COLUMN location VARCHAR(255) NULL",
        },
    }

    with db.engine.begin() as conn:
        for table_name, column_sql in expected_columns.items():
            if not inspector.has_table(table_name):
                continue

            existing = {column["name"] for column in inspector.get_columns(table_name)}
            for column_name, ddl in column_sql.items():
                if column_name not in existing:
                    conn.execute(text(ddl))

def initialize_database():
    global _database_ready
    with app.app_context():
        try:
            db.create_all()
        except Exception as error:
            app.logger.warning("Automatic table creation skipped for one or more tables: %s", error)

        try:
            sync_database_schema()
            _database_ready = True
            return True
        except Exception as error:
            app.logger.warning("Database schema sync skipped: %s", error)
            return False


@app.before_request
def ensure_database_ready():
    global _database_ready
    if _database_ready:
        return None
    initialize_database()
    return None


if __name__ == "__main__":
    initialize_database()
    app.run(debug=True, port=int(env_or_default("APP_PORT", "5001")))
