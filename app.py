from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import random
import os
import sqlite3
from datetime import datetime

# --- App setup ---
app = Flask(__name__, static_folder="web")
CORS(app)

DB_PATH = "chat_logs.db"

# --- Knowledge base and quick options ---
OPTIONS = [
    {"id":"admission", "label":"Admissions"},
    {"id":"timetable", "label":"Timetable"},
    {"id":"fees", "label":"Fees"},
    {"id":"contact", "label":"Contact"},
    {"id":"scholarship", "label":"Scholarships"}
]

DATA = {
    "admission": [
        "Admissions open every June. Apply online from the admissions page.",
        "You need your 10th and 12th marks and a scanned photo to apply."
    ],
    "timetable": [
        "Timetable is available on the student portal — check under 'Timetable'.",
        "If your timetable is missing, contact your department office with roll no."
    ],
    "fees": [
        "Fee structure is on the Accounts Office page. Installments may be available.",
        "For scholarship-linked fee concessions, speak with the Finance Office."
    ],
    "contact": [
    "Contact Number: +91 90836 40444\nEmail: admissions@gimt-india.com\nAlternate Email: admission@gimt-india.com"
],
    "scholarship": [
        "Scholarships depend on merit and need — check the scholarships page or contact finance.",
        "Apply early; deadlines are usually before July."
    ],
    "default": [
        "Sorry, I didn't understand. Try one of the quick options below or ask another question.",
        "You can ask: admissions, timetable, fees, contact, scholarships."
    ]
}

# --- Database helpers ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
      CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_message TEXT,
        bot_response TEXT,
        intent TEXT,
        created_at TEXT
      )
    ''')
    conn.commit()
    conn.close()

def log_message(user_message, bot_response, intent):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO logs (user_message, bot_response, intent, created_at) VALUES (?, ?, ?, ?)',
              (user_message, bot_response, intent, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

# --- Intent detection ---
def detect_intent(message):
    if not message:
        return "empty"
    msg = message.lower()
    for intent in DATA:
        if intent in msg:
            return intent
    # word-based fallback
    words = msg.split()
    for w in words:
        for intent in DATA:
            if w in intent:
                return intent
    return "default"

def choose_reply(intent):
    if intent in DATA:
        return random.choice(DATA[intent])
    return random.choice(DATA["default"])

# --- API endpoints ---
@app.route('/options', methods=['GET'])
def get_options():
    # returns quick-reply options for the UI
    return jsonify({"options": OPTIONS})

@app.route('/chat', methods=['POST'])
def chat():
    payload = request.get_json(silent=True) or {}
    user_msg = payload.get("message", "").strip()
    # if the UI sends an `option_id`, prefer that
    option_id = payload.get("option_id")
    if option_id:
        intent = option_id
    else:
        intent = detect_intent(user_msg)
    reply = choose_reply(intent)
    log_message(user_msg or f"[option:{option_id}]", reply, intent)
    return jsonify({"reply": reply, "intent": intent})

# serve index.html and static files
@app.route('/', methods=['GET'])
def index():
    web_dir = os.path.join(os.getcwd(), app.static_folder)
    return send_from_directory(web_dir, 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    web_dir = os.path.join(os.getcwd(), app.static_folder)
    return send_from_directory(web_dir, filename)

if __name__ == '__main__':
    init_db()
    app.run(port=5000)