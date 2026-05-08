import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'clock_ai.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS workspaces (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workspace_id TEXT,
            title TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            duration INTEGER DEFAULT 30,
            priority TEXT DEFAULT 'medium',
            status TEXT DEFAULT 'active',
            FOREIGN KEY (workspace_id) REFERENCES workspaces (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern TEXT NOT NULL,
            resolution_type TEXT NOT NULL,
            count INTEGER DEFAULT 1,
            last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    
    try:
        cursor.execute("ALTER TABLE schedules ADD COLUMN priority TEXT DEFAULT 'medium'")
    except:
        pass
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern TEXT NOT NULL,
            resolution_type TEXT NOT NULL,
            count INTEGER DEFAULT 1,
            last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print("Database Initialized: clock_ai.db created with Workspaces, Schedules, and User_Preferences tables.")

if __name__ == "__main__":
    init_db()

def get_existing_schedules(date, workspace_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT time, title, priority FROM schedules WHERE date = ? AND workspace_id = ? AND status = 'active'", (date, workspace_id))
    rows = cursor.fetchall()
    conn.close()
    return [{"time": row[0], "title": row[1], "priority": row[2]} for row in rows]

def get_all_schedules(date):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT time, title, workspace_id, priority FROM schedules WHERE date = ? AND status = 'active'", (date,))
    rows = cursor.fetchall()
    conn.close()
    return [{"time": row[0], "title": row[1], "workspace_id": row[2], "priority": row[3]} for row in rows]

def add_schedule(workspace_id, title, date, time, duration=30, priority='medium', force=False):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR IGNORE INTO workspaces (id, name) VALUES (?, ?)", (workspace_id, workspace_id))
        
        if force:
            cursor.execute("DELETE FROM schedules WHERE date = ? AND time = ? AND workspace_id = ?", (date, time, workspace_id))
        
        cursor.execute('''
            INSERT INTO schedules (workspace_id, title, date, time, duration, priority)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (workspace_id, title, date, time, duration, priority))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving to DB: {e}")
        return False
    finally:
        conn.close()

def record_user_pattern(pattern, resolution_type):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, count FROM user_preferences WHERE pattern = ? AND resolution_type = ?", (pattern, resolution_type))
    existing = cursor.fetchone()
    
    if existing:
        cursor.execute("UPDATE user_preferences SET count = count + 1, last_used = ? WHERE id = ?", (datetime.now().isoformat(), existing[0]))
    else:
        cursor.execute("INSERT INTO user_preferences (pattern, resolution_type, count) VALUES (?, ?, 1)", (pattern, resolution_type))
    
    conn.commit()
    conn.close()

def get_suggested_resolution(pattern):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT resolution_type FROM user_preferences WHERE pattern = ? ORDER BY count DESC LIMIT 1", (pattern,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None