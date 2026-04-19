import sqlite3
from flask import *
import uuid

app = Flask(__name__)

# Database Setup
def connect_db():
    c = sqlite3.connect("campus_hub.db").cursor()
    c.execute("CREATE TABLE IF NOT EXISTS TUTORS(id TEXT, name TEXT, subject TEXT, rate TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS EVENTS(id TEXT, title TEXT, location TEXT)")
    c.connection.close()

connect_db()

# Feature 1: Peer Tutoring (POST API)
@app.route('/api/tutors', methods=['POST'])
def add_tutor():
    db = sqlite3.connect("campus_hub.db")
    c = db.cursor()
    req_json = request.json
    tutor_id = uuid.uuid4().hex
    c.execute("INSERT INTO TUTORS VALUES(?,?,?,?)", 
             (tutor_id, req_json['name'], req_json['subject'], req_json['rate']))
    db.commit()
    return jsonify({"response": "Tutor Listing Created Successfully", "id": tutor_id}), 201

# Feature 2: Campus Event Board (GET API)
@app.route('/api/events', methods=['GET'])
def get_events():
    db = sqlite3.connect("campus_hub.db")
    c = db.cursor()
    # Inserting a dummy event for testing output
    c.execute("INSERT INTO EVENTS VALUES('1', 'CSE471 Viva Prep', 'Room 12D')")
    db.commit()
    
    c.execute("SELECT * FROM EVENTS")
    data = c.fetchall()
    return jsonify({"events": data}), 200

if __name__ == '__main__':
    app.run(debug=True, port=1311)