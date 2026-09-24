"""Populate the database with fictional demo data.

Usage:
    python seed.py           # seed an empty database
    python seed.py --reset   # drop all tables, recreate them and seed again

Every demo account uses the password ``demo1234``.
"""
import os
import sys
from datetime import datetime, time, timedelta

from werkzeug.security import generate_password_hash

from app import (
    AcademicDeadline,
    Booking,
    CampusEvent,
    Conversation,
    EventParticipant,
    Item,
    Message,
    Note,
    NoteRating,
    Notification,
    Review,
    Ride,
    ScheduledStudySession,
    SkillExchange,
    SkillProposal,
    StudyPartnerPost,
    TutoringBooking,
    TutoringListing,
    User,
    app,
    db,
    initialize_database,
)

DEMO_PASSWORD = "demo1234"

USERS = [
    # (full_name, username, email, department, is_admin)
    ("Campus Admin", "admin", "admin@campushub.test", "Administration", True),
    ("Ayesha Rahman", "ayesha", "demo@campushub.test", "CSE", False),
    ("Tanvir Hasan", "tanvir", "tanvir@campushub.test", "CSE", False),
    ("Nusrat Jahan", "nusrat", "nusrat@campushub.test", "BBA", False),
    ("Rafiq Islam", "rafiq", "rafiq@campushub.test", "Mathematics", False),
    ("Maliha Chowdhury", "maliha", "maliha@campushub.test", "CSE", False),
]


def _sample_pdf(title):
    """Build a tiny one-page PDF so the demo note can be downloaded."""
    text = title.replace("(", "[").replace(")", "]")
    stream = f"BT /F1 20 Tf 72 720 Td ({text}) Tj ET".encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"
    xref_at = len(pdf)
    pdf += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    for offset in offsets:
        pdf += f"{offset:010d} 00000 n \n".encode()
    pdf += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_at}\n%%EOF\n".encode()
    return bytes(pdf)


def seed():
    today = datetime.now().replace(second=0, microsecond=0)
    password_hash = generate_password_hash(DEMO_PASSWORD, method="pbkdf2:sha256")

    users = {}
    for full_name, username, email, department, is_admin in USERS:
        user = User(
            full_name=full_name,
            username=username,
            email=email,
            password_hash=password_hash,
            department=department,
            major=department,
            is_admin=is_admin,
        )
        db.session.add(user)
        users[username] = user
    db.session.flush()
    ayesha, tanvir, nusrat, rafiq, maliha = (users[name] for name in ("ayesha", "tanvir", "nusrat", "rafiq", "maliha"))

    # Peer tutoring
    listings = [
        TutoringListing(tutor_id=tanvir.id, subject_title="CSE220: Data Structures",
                        teaching_style="Visual tracing of every algorithm before we write a single line of code.",
                        availability_text="Mon/Wed 4:00 PM - 6:00 PM", mode="Both", location_text="Library Study Room 3",
                        latitude=23.7730, longitude=90.4250, rate_type="Paid", hourly_rate=500, free_consult="Yes"),
        TutoringListing(tutor_id=nusrat.id, subject_title="FIN254: Introduction to Finance",
                        teaching_style="Practical examples with real market data and spreadsheets.",
                        availability_text="Tue/Thu 2:00 PM - 5:00 PM", mode="Online", location_text="Google Meet",
                        rate_type="Paid", hourly_rate=400, free_consult="No"),
        TutoringListing(tutor_id=rafiq.id, subject_title="MAT110: Differential Calculus",
                        teaching_style="Patient, step-by-step problem solving until the core idea clicks.",
                        availability_text="Friday mornings", mode="Offline", location_text="Campus Cafeteria",
                        rate_type="Barter", hourly_rate=0, free_consult="Yes"),
        TutoringListing(tutor_id=ayesha.id, subject_title="CSE110: Programming Language I (Python)",
                        teaching_style="Hands-on coding from the first minute, with small weekly projects.",
                        availability_text="Weekends 10:00 AM - 1:00 PM", mode="Both", location_text="Computer Lab 2",
                        rate_type="Free", hourly_rate=0, free_consult="Yes"),
    ]
    db.session.add_all(listings)
    db.session.flush()

    db.session.add_all([
        TutoringBooking(tutoring_listing_id=listings[0].id, student_id=ayesha.id,
                        session_date=(today + timedelta(days=3)).strftime("%Y-%m-%d"), start_time="16:00",
                        note="Struggling with AVL tree rotations.", status="Accepted"),
        TutoringBooking(tutoring_listing_id=listings[3].id, student_id=maliha.id,
                        session_date=(today + timedelta(days=5)).strftime("%Y-%m-%d"), start_time="10:30",
                        note="Need help with loops and functions before the quiz.", status="Pending"),
        TutoringBooking(tutoring_listing_id=listings[3].id, student_id=tanvir.id,
                        session_date=(today - timedelta(days=4)).strftime("%Y-%m-%d"), start_time="11:00",
                        note="Quick recap of recursion.", status="Accepted"),
    ])
    db.session.add_all([
        Review(reviewer_id=ayesha.id, reviewee_id=tanvir.id, service_type="Tutoring", knowledge=5, communication=5,
               punctuality=4, best_for="Exam Prep", feedback="Explained rotations with drawings. Super clear!"),
        Review(reviewer_id=tanvir.id, reviewee_id=ayesha.id, service_type="Tutoring", knowledge=5, communication=4,
               punctuality=5, best_for="Beginners", feedback="Patient and well prepared.", is_anonymous=True),
    ])

    # Campus events
    events = [
        CampusEvent(created_by=nusrat.id, title="Campus Tech Fest",
                    description="A day of project showcases, lightning talks and networking with alumni.",
                    category="Social", event_date=f"{(today + timedelta(days=12)):%Y-%m-%d} at 10:00",
                    location_text="Multipurpose Hall", target_audience="All Students", capacity_limit=150),
        CampusEvent(created_by=tanvir.id, title="Python for Beginners Workshop",
                    description="A hands-on two-hour crash course. Bring your laptop!",
                    category="Workshop", event_date=f"{(today + timedelta(days=6)):%Y-%m-%d} at 14:00",
                    location_text="Computer Lab 2", target_audience="Freshmen", capacity_limit=30),
        CampusEvent(created_by=rafiq.id, title="Calculus Survival Seminar",
                    description="Tips, tricks and past-paper walkthroughs for first-year math courses.",
                    category="Seminar", event_date=f"{(today + timedelta(days=9)):%Y-%m-%d} at 16:30",
                    location_text="Online (Zoom)", target_audience="Engineering Students", capacity_limit=0),
    ]
    db.session.add_all(events)
    db.session.flush()
    db.session.add_all([
        EventParticipant(event_id=events[0].id, user_id=ayesha.id, attendance_status="going"),
        EventParticipant(event_id=events[0].id, user_id=maliha.id, attendance_status="interested"),
        EventParticipant(event_id=events[1].id, user_id=maliha.id, attendance_status="going"),
    ])

    # Study partners
    study_posts = [
        StudyPartnerPost(user_id=tanvir.id, title="CSE471 Final Prep", current_topic="Software Design Patterns",
                         goals="Looking for two people to work through past finals together.",
                         preferred_study_time="Weekends 10 AM", prep_goal="Deep Understanding",
                         study_style="Active Discussion", group_size=3),
        StudyPartnerPost(user_id=maliha.id, title="CSE370 Midterm Cram", current_topic="Normalization & ER Diagrams",
                         goals="I have the practice sheets - need someone to quiz me.",
                         preferred_study_time="Thursday evenings", prep_goal="Exam Cram",
                         study_style="Quiz Each Other", group_size=2),
        StudyPartnerPost(user_id=ayesha.id, title="STA201 Study Session", current_topic="Probability Distributions",
                         goals="Quiet co-working: do our own problem sets, ask when stuck.",
                         preferred_study_time="Monday afternoons", prep_goal="Homework Help",
                         study_style="Silent Parallel", group_size=4),
    ]
    db.session.add_all(study_posts)

    # Skill exchange
    skills = [
        SkillExchange(user_id=maliha.id, offering_skill="Figma & UI Design", seeking_skill="Git and GitHub",
                      credibility="Designed the UI for two club websites", availability="Evenings",
                      description="I'll teach you Figma basics if you help me get comfortable with Git workflows."),
        SkillExchange(user_id=rafiq.id, offering_skill="Guitar (beginner level)", seeking_skill="Public Speaking",
                      credibility="5 years of playing", availability="Weekends",
                      description="Happy to swap guitar lessons for presentation practice."),
    ]
    db.session.add_all(skills)
    db.session.flush()
    db.session.add(SkillProposal(skill_id=skills[0].id, proposer_id=ayesha.id, status="Pending"))

    # Messaging
    conversation = Conversation(participant1_id=ayesha.id, participant2_id=tanvir.id,
                                context_type="Tutor", context_id=listings[0].id)
    db.session.add(conversation)
    db.session.flush()
    db.session.add_all([
        Message(conversation_id=conversation.id, sender_id=ayesha.id, is_seen=1,
                message_text="Hi Tanvir! Are you free for a CSE220 session this week?"),
        Message(conversation_id=conversation.id, sender_id=tanvir.id, is_seen=1,
                message_text="Sure - Wednesday at 4 PM in the library works for me."),
        Message(conversation_id=conversation.id, sender_id=tanvir.id, is_seen=0,
                message_text="Bring your lab code and we'll trace the rotations together."),
    ])

    # Notes (with a small generated PDF so downloads work)
    note_file = "sample_cse220_notes.pdf"
    upload_path = os.path.join(app.config["UPLOAD_FOLDER"], note_file)
    try:
        with open(upload_path, "wb") as handle:
            handle.write(_sample_pdf("CSE220 - Balanced Trees Cheat Sheet"))
    except OSError:
        pass
    note = Note(uploader_id=tanvir.id, title="Balanced Trees Cheat Sheet", description="Course: CSE220",
                semester="Fall 2026", file_path=note_file, file_type="pdf")
    db.session.add(note)
    db.session.flush()
    db.session.add(NoteRating(note_id=note.id, rater_id=ayesha.id, rating=5))

    # Deadlines & scheduled sessions for the main demo account
    db.session.add_all([
        AcademicDeadline(user_id=ayesha.id, title="CSE220 Lab Assignment 4", priority="high",
                         description="Implement AVL insertion and deletion.",
                         deadline_datetime=(today + timedelta(days=2)).replace(hour=23, minute=59)),
        AcademicDeadline(user_id=ayesha.id, title="STA201 Quiz 3", priority="medium",
                         description="Chapters 5-6.", deadline_datetime=(today + timedelta(days=6)).replace(hour=9, minute=0)),
        AcademicDeadline(user_id=ayesha.id, title="ENG102 Essay Draft", priority="low", status="completed",
                         deadline_datetime=(today - timedelta(days=3)).replace(hour=17, minute=0)),
        ScheduledStudySession(created_by=ayesha.id, title="STA201 group revision",
                              description="Work through the practice sheet together.",
                              session_date=(today + timedelta(days=4)).date(), start_time=time(15, 0),
                              end_time=time(17, 0), mode="offline", location_text="Library Study Room 1"),
    ])

    # Marketplace
    db.session.add_all([
        Item(title="Introduction to Algorithms (3rd Edition)", price=1200, condition="Unused", category="Textbooks",
             description="Barely used, no highlights. Perfect for CSE220/CSE221.",
             seller_name=tanvir.full_name, seller_email=tanvir.email, seller_phone="01700-000001"),
        Item(title="Casio fx-991EX Scientific Calculator", price=1500, condition="Used", category="Electronics",
             description="Works perfectly, comes with the original cover.",
             seller_name=ayesha.full_name, seller_email=ayesha.email, seller_phone="01700-000002"),
        Item(title="Lab Coat (Size M)", price=350, condition="Used", category="Other",
             description="Used for one semester of physics lab.",
             seller_name=maliha.full_name, seller_email=maliha.email),
    ])

    # Ride sharing (coordinates around Dhaka so the map works without an API key)
    rides = [
        Ride(user_id=ayesha.username, start_location="Campus Main Gate, Merul Badda", destination="Uttara Sector 7",
             travel_date=(today + timedelta(days=1)).date(), travel_time=time(17, 30), available_seats=3,
             cost_share=120, notes="Leaving right after the last class.", contact_info=ayesha.email,
             latitude=23.7730, longitude=90.4250, destination_latitude=23.8715, destination_longitude=90.3960),
        Ride(user_id=tanvir.username, start_location="Dhanmondi 27", destination="Campus Main Gate, Merul Badda",
             travel_date=(today + timedelta(days=2)).date(), travel_time=time(8, 15), available_seats=2,
             cost_share=150, notes="Morning ride, AC car.", contact_info=tanvir.email,
             latitude=23.7561, longitude=90.3740, destination_latitude=23.7730, destination_longitude=90.4250),
        Ride(user_id=rafiq.username, start_location="Mirpur 10", destination="Campus Main Gate, Merul Badda",
             travel_date=(today + timedelta(days=3)).date(), travel_time=time(9, 0), available_seats=1,
             cost_share=100, contact_info=rafiq.email,
             latitude=23.8069, longitude=90.3687, destination_latitude=23.7730, destination_longitude=90.4250),
    ]
    db.session.add_all(rides)
    db.session.flush()
    db.session.add(Booking(ride_id=rides[1].id, user_id=ayesha.username, seats_booked=1, contact_info=ayesha.email))
    rides[1].available_seats -= 1

    # Notifications
    db.session.add_all([
        Notification(user_id=ayesha.id, type="booking", title="New Tutoring Request",
                     message="Maliha Chowdhury requested a session for CSE110: Programming Language I (Python)!"),
        Notification(user_id=ayesha.id, type="message", title="New Message",
                     message="Tanvir Hasan sent you a message!"),
        Notification(user_id=tanvir.id, type="review", title="Detailed Review Received!",
                     message="Someone just left you a verified review!", is_read=True),
    ])

    db.session.commit()


def main():
    reset = "--reset" in sys.argv
    with app.app_context():
        if reset:
            db.drop_all()
        initialize_database()
        if User.query.first():
            print("Database already has users; skipping. Run `python seed.py --reset` to start fresh.")
            return
        seed()
        print(f"Seeded demo data. Log in with demo@campushub.test / {DEMO_PASSWORD} "
              f"(admin: admin@campushub.test / {DEMO_PASSWORD}).")


if __name__ == "__main__":
    main()
