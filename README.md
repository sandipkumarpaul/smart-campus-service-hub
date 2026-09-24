<p align="center">
  <img src="static/images/logo.jpeg" alt="Smart Campus Service Hub" width="440">
</p>

<p align="center">
  <b>One place for students to find tutors, study partners, events, rides and second-hand gear.</b><br>
  A full-stack Flask web app built as a university team project.
</p>

<p align="center">
  <a href="https://github.com/sandipkumarpaul/smart-campus-service-hub/actions/workflows/ci.yml"><img src="https://github.com/sandipkumarpaul/smart-campus-service-hub/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <img src="https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/flask-3.0-000000?logo=flask" alt="Flask 3">
  <img src="https://img.shields.io/badge/database-MySQL%20%7C%20SQLite-4479A1?logo=mysql&logoColor=white" alt="MySQL or SQLite">
  <img src="https://img.shields.io/badge/deploy-Vercel-000000?logo=vercel" alt="Vercel">
</p>

---

## Overview

Campus services are usually scattered across Facebook groups, chats and notice boards. **Smart Campus Service Hub** brings them into a single web app with one account, one dashboard and one inbox:

- A student can **book a peer tutor**, chat once the tutor accepts, and leave a **verified review** afterwards.
- The same account can **RSVP to events**, **find a study group**, **trade skills**, **sell a used textbook**, or **share a ride** to campus.
- **Reputation scores and moderation tools** keep the community trustworthy: reports go to admins, confirmed abusers are banned, and false reporters are penalised.

## Features

| Area | What you can do |
| --- | --- |
| 🎓 **Peer tutoring** | Publish tutoring listings (paid, free or skill barter), book sessions, accept or decline requests, and browse a **Top Rated Tutors** leaderboard filtered by department, subject and rating. |
| ⭐ **Reviews & trust** | Leave multi-criteria reviews (knowledge, communication, punctuality). Only students who actually completed a session or skill trade can review. Each user gets a live **trust score and badge**. |
| 🛡️ **Moderation** | Report listings, study groups, skill posts or events. Admins approve (content hidden, user banned) or reject (reporter penalised) from an admin panel. Restricted users can't post. |
| 🤝 **Study partners** | Post study cards with course, topic, goal, study style and group size. Chat with the poster or turn a match into a scheduled study session. |
| 🔁 **Skill exchange** | Offer one skill in exchange for another, send trade proposals and open a chat when one is accepted. |
| 📅 **Campus events** | Publish events with capacity limits, RSVP as *going* or *interested*, and notify the organiser when an event fills up. |
| 📚 **Notes & deadlines** | Upload PDF/DOCX notes, search by course and semester, rate other students' notes, and track deadlines. Deadlines and study sessions optionally sync to **Google Calendar** (with a Meet link). |
| 🛒 **Marketplace** | Buy and sell used items with photos, conditions and categories. |
| 🚗 **Ride sharing** | Offer or book seats on rides. Addresses are geocoded and shown on an interactive **Leaflet / OpenStreetMap** map, with road routes from **OpenRouteService**. |
| 💬 **Messaging & notifications** | 1-to-1 conversations linked to the listing they started from, unread badges, and a notification centre for bookings, reviews, RSVPs and moderation decisions. |

## Screenshots

| Unified dashboard | Top rated tutors |
| --- | --- |
| ![Dashboard](docs/screenshots/dashboard.png) | ![Top rated tutors](docs/screenshots/tutors.png) |
| **Campus events** | **Messaging** |
| ![Events](docs/screenshots/events.png) | ![Messages](docs/screenshots/messages.png) |
| **Ride share map** | **Academic dashboard** |
| ![Ride share map](docs/screenshots/ride-map.jpg) | ![Academic dashboard](docs/screenshots/academic-dashboard.png) |

## Tech stack

- **Backend:** Python, Flask, Flask-SQLAlchemy (SQLAlchemy 2), Werkzeug password hashing (PBKDF2)
- **Database:** MySQL in production (PyMySQL driver), SQLite for local development and tests
- **Frontend:** Jinja2 templates, Bootstrap 5, Bootstrap Icons, vanilla JavaScript
- **Maps & APIs:** Leaflet + OpenStreetMap tiles, OpenRouteService (geocoding and directions), Google Calendar API (OAuth 2.0)
- **Tooling:** pytest, GitHub Actions CI, Vercel serverless deployment

## Getting started

You need Python 3.10 or newer. With no configuration the app uses a local SQLite database, so a first run takes about a minute.

```bash
git clone https://github.com/sandipkumarpaul/smart-campus-service-hub.git
cd smart-campus-service-hub

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python seed.py                   # creates the tables and fictional demo data
python app.py                    # http://127.0.0.1:5000
```

Log in with one of the demo accounts (every account's password is `demo1234`):

| Role | Email |
| --- | --- |
| Student with tutoring, rides, deadlines and chats | `demo@campushub.test` |
| Admin (moderation panel) | `admin@campushub.test` |
| Other students | `tanvir@`, `nusrat@`, `rafiq@`, `maliha@campushub.test` |

Run `python seed.py --reset` any time to wipe the database and start fresh.

### Configuration

Copy `.env.example` to `.env` and set what you need. Every variable is optional locally.

| Variable | Purpose |
| --- | --- |
| `SECRET_KEY` | Signs session cookies. **Required in production**; a random key is used (sessions reset on restart) if it's missing. |
| `DATABASE_URL` | Any SQLAlchemy URL, e.g. `mysql+pymysql://user:pass@host:3306/campus_hub?charset=utf8mb4`. |
| `DB_USER`, `DB_PASS`, `DB_HOST`, `DB_PORT`, `DB_NAME` | An alternative to `DATABASE_URL` for MySQL. |
| `OPENROUTESERVICE_API_KEY` | Enables address geocoding and road routes on the ride map ([free key](https://openrouteservice.org/dev/#/signup)). |
| `FLASK_DEBUG` | Set to `1` for the debugger and auto-reload. |

**MySQL:** create an empty database, point `DATABASE_URL` (or the `DB_*` variables) at it, then run `python seed.py`. Tables are created automatically, and missing columns are added on startup, so no SQL dump is needed.

**Google Calendar (optional):** create an OAuth client in Google Cloud, save it as `credentials.json` in the project root, and visit `/auth` once. New deadlines and study sessions will then be added to that calendar, and study sessions get a Google Meet link. Without it, everything is still saved in the app.

### Running the tests

```bash
pip install -r requirements-dev.txt
pytest
```

The suite runs against a temporary SQLite database and covers authentication, page rendering with the seed data, ownership and permission checks, and the JSON API. GitHub Actions runs it on every push.

## JSON API

| Method | Endpoint | Auth | Description |
| --- | --- | --- | --- |
| `GET` | `/api/events` | — | Campus events |
| `GET` | `/api/study-partners` | — | Open study-partner posts |
| `GET` | `/api/study-sessions` | Session | The current user's scheduled study sessions |
| `POST` | `/api/study-sessions/create` | Session | Schedule a study session (`title`, `date`, `start_time`, `end_time`) |
| `POST` | `/api/tutors` | Session | Create a tutoring listing (`subject`, `rate`, optional `mode`, `availability`, `location`) |
| `POST` | `/api/messages` | Session | Send a message to a conversation you belong to (`conversation_id`, `message`) |
| `GET` | `/api/geocode?q=` | — | Geocode an address with OpenRouteService |
| `GET` | `/api/rides/<id>/route` | Session | Road route for a ride you posted or booked |
| `GET` | `/db-health` | — | Database connectivity check |

## Project structure

```
├── app.py                 # Flask app: config, SQLAlchemy models and all routes
├── seed.py                # Fictional demo data (python seed.py [--reset])
├── templates/             # Jinja2 pages (Bootstrap 5)
├── static/                # Logo and uploaded item photos (static/uploads)
├── uploads/               # Uploaded notes (PDF/DOCX)
├── tests/                 # pytest suite
├── docs/screenshots/      # README images
├── vercel.json            # Vercel serverless configuration
└── .env.example           # Configuration template
```

## Deployment

The project deploys to **Vercel** as a Python serverless function (`vercel.json` sends every route to `app.py`) with a hosted MySQL database. Set `SECRET_KEY`, `DATABASE_URL` (or the `DB_*` variables) and `OPENROUTESERVICE_API_KEY` as environment variables in the Vercel project.

Serverless file systems are read-only, so uploaded notes and item photos only persist on a regular server. A production version would store them in object storage such as S3 or Cloudinary.

## Security notes

- Passwords are stored as salted PBKDF2 hashes; nothing sensitive is committed (see `.env.example`).
- Every edit and delete checks ownership on the server. Admin actions require an admin session.
- Session cookies are `HttpOnly` and `SameSite=Lax`, which blocks cross-site form posts.
- Uploads are restricted by file type and saved under unique, sanitised names.

## Team

Smart Campus Service Hub was built by a team of four students at BRAC University, with each member owning a set of modules that were integrated into a single application.

**My contributions:** the peer tutoring module (listings, bookings, top-rated tutors and verified reviews), the campus event board, user authentication, the unified student dashboard, and integrating the team's modules into one app deployed on Vercel with a cloud MySQL database.
