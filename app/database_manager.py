
import os, sqlite3

DB_PATH = os.getenv("DATABASE_PATH", "../data/autoresq.db")

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

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    with conn:
        for stmt in SCHEMA.strip().split(';'):
            s = stmt.strip()
            if s:
                conn.execute(s + ';')
    return conn
