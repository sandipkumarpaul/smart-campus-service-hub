import io

import pytest

from app import (
    AcademicDeadline,
    CampusEvent,
    Item,
    Note,
    Notification,
    Report,
    ScheduledStudySession,
    TutoringListing,
    User,
    db,
)
from conftest import login


# ---------------------------------------------------------------- auth

def test_protected_pages_redirect_to_login(app):
    client = app.test_client()
    for path in ("/", "/dashboard", "/tutors", "/events", "/messages", "/deadlines"):
        response = client.get(path)
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]


def test_register_login_and_logout(app):
    client = app.test_client()
    form = {"email": "New@Example.com", "username": "newbie", "full_name": "New Student",
            "department": "CSE", "password": "s3cret-pass"}
    response = client.post("/register", data=form)
    assert response.headers["Location"].endswith("/dashboard")
    assert User.query.filter_by(email="new@example.com").one().password_hash != "s3cret-pass"

    client.get("/logout")
    assert client.get("/dashboard").status_code == 302

    duplicate = app.test_client().post("/register", data=form, follow_redirects=True)
    assert b"already registered" in duplicate.data

    assert login(app.test_client(), "new@example.com", "wrong").status_code == 200
    assert login(app.test_client(), "new@example.com", "s3cret-pass").status_code == 302


# ---------------------------------------------------------------- pages

PAGES = [
    "/dashboard", "/academic-dashboard", "/deadlines", "/upload", "/search", "/tutors",
    "/top-rated-tutors", "/events", "/study-partners", "/skill_exchange", "/messages",
    "/messages/1", "/browse", "/browse?q=calculator", "/post", "/my-listings", "/item/1",
    "/item/2/edit", "/rides", "/rides?route=Uttara&min_seats=1", "/rides/post", "/rides/1",
    "/rides/1/edit", "/map", "/all_notifications", "/api/events", "/api/study-partners",
    "/api/study-sessions",
]


@pytest.mark.parametrize("path", PAGES)
def test_pages_render_with_seed_data(demo_client, path):
    assert demo_client.get(path).status_code == 200


def test_seeded_note_is_downloadable(demo_client):
    note = Note.query.first()
    response = demo_client.get(f"/download/{note.file_path}")
    assert response.status_code == 200
    assert response.data.startswith(b"%PDF")


def test_db_health_does_not_leak_details(app):
    response = app.test_client().get("/db-health")
    assert response.get_json() == {"status": "ok", "database": "reachable"}


# ---------------------------------------------------------------- ownership & authorization

def test_only_uploader_can_edit_or_delete_note(demo_client):
    note = Note.query.first()  # uploaded by another demo user
    demo_client.post(f"/edit/{note.id}", data={"title": "Hijacked", "course": "X", "term": "Y", "year": "Z"})
    demo_client.post(f"/delete/{note.id}")
    db.session.expire_all()
    note = db.session.get(Note, note.id)
    assert note is not None and note.title == "Balanced Trees Cheat Sheet"


def test_only_owner_can_delete_deadline(demo_client, other_client):
    deadline = AcademicDeadline.query.filter_by(status="pending").first()
    other_client.post(f"/deadlines/delete/{deadline.id}")
    assert db.session.get(AcademicDeadline, deadline.id) is not None

    demo_client.post(f"/deadlines/delete/{deadline.id}")
    db.session.expire_all()
    assert db.session.get(AcademicDeadline, deadline.id) is None


def test_item_edit_cannot_be_bypassed_with_email_parameter(seeded):
    item = Item.query.filter_by(seller_email="demo@campushub.test").first()
    anonymous = seeded.test_client()
    response = anonymous.post(f"/item/{item.id}/edit?email=demo@campushub.test", data={"title": "Hacked"})
    assert "/login" in response.headers["Location"]
    anonymous.post(f"/item/{item.id}/delete", data={"email": "demo@campushub.test"})
    db.session.expire_all()
    assert db.session.get(Item, item.id).title != "Hacked"


def test_item_upload_rejects_non_images(demo_client):
    form = {"title": "Sketchy", "description": "d", "price": "10", "condition": "Used", "category": "Other",
            "image": (io.BytesIO(b"<script>alert(1)</script>"), "evil.html")}
    demo_client.post("/post", data=form, content_type="multipart/form-data")
    assert Item.query.filter_by(title="Sketchy").first() is None


def test_admin_panel_is_admin_only(seeded, demo_client):
    assert demo_client.get("/admin/reports").status_code == 302
    admin = seeded.test_client()
    login(admin, "admin@campushub.test")
    assert admin.get("/admin/reports").status_code == 200


@pytest.mark.parametrize("action, listing_status, owner_banned, reporter_penalty", [
    ("approve", "Banned", True, 0),
    ("reject", "Active", False, 20),
])
def test_moderation_outcomes(seeded, other_client, action, listing_status, owner_banned, reporter_penalty):
    listing = TutoringListing.query.filter_by(subject_title="CSE220: Data Structures").one()
    other_client.post("/report", data={"reported_type": "Tutor", "reported_id": listing.id, "reason": "spam"})

    admin = seeded.test_client()
    login(admin, "admin@campushub.test")
    report = Report.query.one()
    admin.post(f"/admin/resolve/{report.id}/{action}")

    db.session.expire_all()
    assert db.session.get(TutoringListing, listing.id).status == listing_status
    assert bool(listing.user.is_banned) is owner_banned
    assert User.query.filter_by(username="maliha").one().trust_penalty == reporter_penalty


def test_review_requires_a_completed_service(other_client):
    tutor = User.query.filter_by(username="tanvir").one()
    other_client.post(f"/submit_review/{tutor.id}", data={"knowledge": "1", "communication": "1", "punctuality": "1"})
    assert all(review.reviewer.username != "maliha" for review in tutor.received_reviews)


# ---------------------------------------------------------------- features

def test_deleted_events_are_hidden(demo_client):
    event = CampusEvent.query.filter_by(title="Campus Tech Fest").one()
    event.status = "Deleted"
    db.session.commit()
    assert b"Campus Tech Fest" not in demo_client.get("/events").data
    titles = [e["title"] for e in demo_client.get("/api/events").get_json()["events"]]
    assert "Campus Tech Fest" not in titles


def test_rsvp_rejects_unknown_status(demo_client):
    event = CampusEvent.query.first()
    response = demo_client.post(f"/rsvp/{event.id}/hacked", follow_redirects=True)
    assert b"Invalid RSVP option" in response.data


def test_booking_a_tutor_notifies_them(other_client):
    listing = TutoringListing.query.filter_by(subject_title="CSE220: Data Structures").one()
    other_client.post(f"/book_tutor/{listing.id}", data={"session_date": "2030-01-01", "start_time": "10:00", "note": "hi"})
    assert len(listing.bookings) == 2
    assert Notification.query.filter_by(user_id=listing.tutor_id, title="New Tutoring Request").count() == 1


def test_study_session_is_saved_without_google_calendar(demo_client):
    payload = {"title": "Group revision", "date": "2030-01-01", "start_time": "10:00", "end_time": "11:00"}
    response = demo_client.post("/api/study-sessions/create", json=payload)
    assert response.status_code == 201
    assert response.get_json()["calendar_synced"] is False
    assert ScheduledStudySession.query.filter_by(title="Group revision").count() == 1


# ---------------------------------------------------------------- JSON API

def test_write_apis_require_login(seeded):
    client = seeded.test_client()
    assert client.post("/api/tutors", json={"subject": "X"}).status_code == 401
    assert client.post("/api/messages", json={"conversation_id": 1, "message": "hi"}).status_code == 401


def test_api_creates_tutoring_listing_for_current_user(demo_client):
    response = demo_client.post("/api/tutors", json={"subject": "CSE221: Algorithms", "rate": 300})
    assert response.status_code == 201
    listing = db.session.get(TutoringListing, response.get_json()["id"])
    assert listing.user.email == "demo@campushub.test"


def test_api_messages_only_for_participants(demo_client, other_client):
    assert demo_client.post("/api/messages", json={"conversation_id": 1, "message": "hello"}).status_code == 201
    assert other_client.post("/api/messages", json={"conversation_id": 1, "message": "sneaky"}).status_code == 404
