from app import app, db, User, TutoringListing, StudyPartnerPost, CampusEvent, SkillExchange, Review, Report
from werkzeug.security import generate_password_hash

def seed_database():
    with app.app_context():
        print("🧹 Clearing old database tables...")
        db.drop_all()  # Wipes the database clean
        db.create_all() # Rebuilds the fresh tables

        print("🌱 Planting new users...")
        default_password = generate_password_hash("password123", method='pbkdf2:sha256')

        # User 1: The Administrator
        admin = User(full_name="Sandip Kumar Paul", student_id="21101001", email="sandip@g.bracu.ac.bd", password_hash=default_password, department="CSE", is_admin=True)
        # User 2: Standard Student
        student1 = User(full_name="Tanjila Afsari", student_id="22101002", email="tanjila@g.bracu.ac.bd", password_hash=default_password, department="CSE", is_admin=False)
        # User 3: Standard Student
        student2 = User(full_name="Riya Rahman", student_id="23101003", email="riya@g.bracu.ac.bd", password_hash=default_password, department="BBA", is_admin=False)
        # User 4: Standard Student
        student3 = User(full_name="Abrar Khan", student_id="23101004", email="abrar@g.bracu.ac.bd", password_hash=default_password, department="EEE", is_admin=False)

        db.session.add_all([admin, student1, student2, student3])
        db.session.commit() # Commit to generate IDs

        print("📚 Adding Tutoring Listings & Study Groups...")
        tutor1 = TutoringListing(tutor_id=admin.id, subject_title="CSE471: System Analysis", teaching_style="I use real-world startup examples to explain design patterns.", availability_text="Mon/Wed Evenings", mode="Online", location_text="Discord", rate_type="Paid", hourly_rate=500.00, free_consult="Yes")
        tutor2 = TutoringListing(tutor_id=student3.id, subject_title="EEE201: Circuits", teaching_style="I break down complex math into simple steps.", availability_text="Fridays", mode="offline", location_text="UB2 Library", rate_type="Free", hourly_rate=0.00, free_consult="No")
        
        study1 = StudyPartnerPost(user_id=student1.id, title="CSE221 Data Structures", current_topic="Graph Algorithms (Dijkstra)", prep_goal="Exam Cram", study_style="Quiz Each Other", preferred_study_time="Weekends", group_size=3, goals="Need to practice tracing algorithms on whiteboard.")
        
        db.session.add_all([tutor1, tutor2, study1])

        print("🤝 Adding Skill Exchanges...")
        skill1 = SkillExchange(user_id=student1.id, offering_skill="Python Basics", seeking_skill="Figma / UI Design", credibility="Aced CSE111, built 3 side projects.", description="I can teach you the basics of Python if you help me design the UI for my new app!", availability="Tuesday Afternoons", status="Active")
        skill2 = SkillExchange(user_id=student2.id, offering_skill="Presentation & Public Speaking", seeking_skill="Advanced Excel", credibility="Won 2 national debate tournaments.", description="BBA student here looking to trade presentation coaching for some heavy Excel formula training.", availability="Flexible", status="Active")
        
        db.session.add_all([skill1, skill2])

        print("🎟️ Adding Campus Events...")
        event1 = CampusEvent(created_by=admin.id, title="BRACU Hackathon 2026 Info Session", category="Academic", event_date="2026-05-15", location_text="Auditorium", target_audience="All Depts", capacity_limit=100, description="Come learn about the upcoming campus-wide hackathon!")
        db.session.add(event1)

        print("⭐ Adding Reviews & 🚩 Reports...")
        # Tanjila reviews Sandip's Tutoring
        review1 = Review(reviewer_id=student1.id, reviewee_id=admin.id, service_type="Tutoring", knowledge=5, communication=5, punctuality=4, best_for="Exam Prep", feedback="Incredible tutor. Explained the whole syllabus in 2 hours!")
        # Abrar reviews Sandip
        review2 = Review(reviewer_id=student3.id, reviewee_id=admin.id, service_type="Tutoring", knowledge=5, communication=4, punctuality=5, best_for="Exam Prep", feedback="Saved my life before the midterm.")
        
        # Someone reports a post so you can see it in the Admin Panel
        report1 = Report(reporter_id=student2.id, reported_type="Skill Exchange", reported_id=1, reason="Inappropriate Content")

        db.session.add_all([review1, review2, report1])
        db.session.commit()

        print("✅ Database successfully seeded! You can now log in.")

if __name__ == "__main__":
    seed_database()