import sqlite3
from config import DB_NAME


def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        is_allowed INTEGER DEFAULT 0
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS vps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT,
        host TEXT,
        username TEXT,
        password TEXT,
        active INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()


def allow_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO users (user_id, is_allowed) VALUES (?,1)", (user_id,))
    conn.commit()
    conn.close()


def is_allowed(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT is_allowed FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row and row[0] == 1


def add_vps(user_id, name, host, username, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE vps SET active=0 WHERE user_id=?", (user_id,))
    c.execute("INSERT INTO vps (user_id,name,host,username,password,active) VALUES (?,?,?,?,?,1)",
              (user_id,name,host,username,password))
    conn.commit()
    conn.close()


def get_active_vps(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT host,username,password FROM vps WHERE user_id=? AND active=1", (user_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"host":row[0],"user":row[1],"password":row[2]}
    return None


def list_vps(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id,name FROM vps WHERE user_id=?", (user_id,))
    rows = c.fetchall()
    conn.close()
    return rows


def set_active(user_id, vps_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE vps SET active=0 WHERE user_id=?", (user_id,))
    c.execute("UPDATE vps SET active=1 WHERE id=?", (vps_id,))
    conn.commit()
    conn.close()


def delete_vps(vps_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM vps WHERE id=?", (vps_id,))
    conn.commit()
    conn.close()
