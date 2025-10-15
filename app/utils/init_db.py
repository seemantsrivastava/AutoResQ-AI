import os, sqlite3, datetime
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DATABASE_PATH")

# Make sure directory exists
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

SCHEMA = '''
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  received_at TEXT,
  event_type TEXT,
  summary TEXT,
  service TEXT,
  details TEXT,
  raw_json TEXT,
  ai_plan TEXT,
  status TEXT DEFAULT 'NEW'
);
CREATE TABLE IF NOT EXISTS actions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_id INTEGER,
  action TEXT,
  created_at TEXT
);
'''

def init_db():
    """Initialize DB schema if not present."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    with conn:
        for stmt in SCHEMA.strip().split(';'):
            s = stmt.strip()
            if s:
                conn.execute(s + ';')
    print("✅ Database initialized with schema.")
    return conn

def seed_sample_data(conn):
    """Insert some mock incidents for testing."""
    sample_events = [
        ("ALERT", "CPU usage > 90% on Mule Node 1", "Mule Runtime", "CPU spike detected", '{"cpu":95}', "Restart node and check JVM heap"),
        ("ALERT", "Queue depth high on WMQ_IN", "IBM MQ", "Queue depth exceeded 5000", '{"queue":"WMQ_IN"}', "Check consumer logs and restart Mule flow"),
        ("INCIDENT", "Salesforce API timeout", "Salesforce", "Timeout errors in integration flow", '{"error":"ReadTimeout"}', "Increase timeout and retry failed messages")
    ]

    now = datetime.datetime.utcnow().isoformat()
    with conn:
        for ev in sample_events:
            conn.execute("""
                INSERT INTO events (received_at, event_type, summary, service, details, raw_json, ai_plan, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (now, *ev, "NEW"))
    print("🌟 Sample events inserted successfully!")

if __name__ == "__main__":
    conn = init_db()
    seed_sample_data(conn)
    print("🎯 Ready! Now run: streamlit run app/dashboard_app.py")
