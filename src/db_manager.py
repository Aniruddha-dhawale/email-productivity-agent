import sqlite3
import pandas as pd
from datetime import datetime

DB_NAME = "data/mock_inbox.db"

def get_connection():
    return sqlite3.connect(DB_NAME)


# Initializes the database with necessary tables.
def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # Table for Emails
    c.execute('''CREATE TABLE IF NOT EXISTS emails (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT,
        subject TEXT,
        body TEXT,
        received_at TEXT,
        is_read INTEGER DEFAULT 0,
        category TEXT,
        action_items TEXT,
        draft_reply TEXT
    )''')

    # Table for User Prompts 
    c.execute('''CREATE TABLE IF NOT EXISTS prompts (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')

    conn.commit()
    conn.close()

# Returns all emails as a DataFrame
def fetch_emails():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM emails ORDER BY received_at DESC", conn)
    conn.close()
    return df

# Fetches a single email
def get_email_by_id(email_id):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM emails WHERE id=?", (email_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

# Updates the email with generated details
def update_email_ai_data(email_id, category, action_items, draft_reply):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''UPDATE emails 
                 SET category=?, action_items=?, draft_reply=? 
                 WHERE id=?''', 
              (category, action_items, draft_reply, email_id))
    conn.commit()
    conn.close()

# Saves or updates a user prompt configuration
def save_prompt(key, value):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO prompts (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

# Retrieves a prompt, returning a default if not set
def get_prompt(key, default_text=""):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT value FROM prompts WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else default_text

# Helper to get text context for the agent
def get_all_emails_for_chat():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, sender, subject, category, action_items FROM emails")
    rows = c.fetchall()
    conn.close()
    context = "INBOX SUMMARY:\n"
    for r in rows:
        context += f"- ID {r[0]}: From {r[1]}, Subject '{r[2]}', Category: {r[3]}, Actions: {r[4]}\n"
    return context

# Marks an email as read in the database
def mark_as_read(email_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE emails SET is_read=1 WHERE id=?", (email_id,))
    conn.commit()
    conn.close()

# Updates the shadow calendar column and marks as scheduled
def schedule_with_shadow_summary(email_id, summary_text):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("ALTER TABLE emails ADD COLUMN is_scheduled INTEGER DEFAULT 0")
    except: pass
    try:
        c.execute("ALTER TABLE emails ADD COLUMN calendar_summary TEXT")
    except: pass
    c.execute("UPDATE emails SET is_scheduled=1, calendar_summary=? WHERE id=?", (summary_text, email_id))
    conn.commit()
    conn.close()
