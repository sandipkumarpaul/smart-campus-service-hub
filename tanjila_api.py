import sqlite3
from flask import *
import uuid

app = Flask(__name__)

# Database Setup
def connect_db():
    c = sqlite3.connect("campus_hub.db").cursor()
    c.execute("CREATE TABLE IF NOT EXISTS PARTNERS(id TEXT, name TEXT, course TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS MESSAGES(id TEXT, sender TEXT, receiver TEXT, msg TEXT)")
    c.connection.close()

connect_db()

# Feature 1: Study Partner Finder (GET API)
@app.route('/api/study-partners', methods=['GET'])
def get_partners():
    db = sqlite3.connect("campus_hub.db")
    c = db.cursor()
    # Inserting dummy data for testing output
    c.execute("INSERT INTO PARTNERS VALUES('1', 'Alice', 'CSE471')")
    db.commit()
    
    c.execute("SELECT * FROM PARTNERS")
    data = c.fetchall()
    return jsonify({"study_partners": data}), 200

# Feature 2: Real-Time Messaging API (POST API)
@app.route('/api/messages', methods=['POST'])
def send_message():
    db = sqlite3.connect("campus_hub.db")
    c = db.cursor()
    req_json = request.json
    msg_id = uuid.uuid4().hex
    c.execute("INSERT INTO MESSAGES VALUES(?,?,?,?)", 
             (msg_id, req_json['sender'], req_json['receiver'], req_json['message']))
    db.commit()
    return jsonify({"response": "Message Sent Successfully", "id": msg_id}), 201

if __name__ == '__main__':
    app.run(debug=True, port=1310)