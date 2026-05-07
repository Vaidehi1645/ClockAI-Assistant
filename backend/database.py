import sqlite3

def init_db():
    conn = sqlite3.connect('clock_ai.db')
    cursor = conn.cursor()

    # 1. Create Workspaces Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS workspaces (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 2. Create Schedules Table (Linked to Workspace)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workspace_id TEXT,
            title TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            duration INTEGER,
            status TEXT DEFAULT 'active',
            FOREIGN KEY (workspace_id) REFERENCES workspaces (id)
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ Database Initialized: clock_ai.db created with Workspaces and Schedules tables.")

if __name__ == "__main__":
    init_db()


def get_existing_schedules(date):
    """Fetch all schedules for a specific date to check for conflicts."""
    conn = sqlite3.connect('clock_ai.db')
    cursor = conn.cursor()
    cursor.execute("SELECT time, title FROM schedules WHERE date = ?", (date,))
    rows = cursor.fetchall()
    conn.close()
    # Convert to list of dicts to match our Brain logic
    return [{"time": row[0], "title": row[1]} for row in rows]

def add_schedule(workspace_id, title, date, time, duration):
    """Save a new schedule to the database."""
    conn = sqlite3.connect('clock_ai.db')
    cursor = conn.cursor()
    try:
        # Ensure the workspace exists first (Simple auto-create for now)
        cursor.execute("INSERT OR IGNORE INTO workspaces (id, name) VALUES (?, ?)", 
                       (workspace_id, workspace_id))
        
        cursor.execute('''
            INSERT INTO schedules (workspace_id, title, date, time, duration)
            VALUES (?, ?, ?, ?, ?)
        ''', (workspace_id, title, date, time, duration))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving to DB: {e}")
        return False
    finally:
        conn.close()