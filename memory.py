import sqlite3
import os
from datetime import datetime
from config import config

DB_NAME = config.get("storage", {}).get("memory_db_name", "vega_memory.db")
DB_PATH = os.path.join(os.path.dirname(__file__), DB_NAME)


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            # Table for persistent facts and user preferences
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT NOT NULL,
                    category TEXT DEFAULT 'general',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Table for interaction history log
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS interaction_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_input TEXT NOT NULL,
                    assistant_response TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
    except Exception as error:
        print(f"Memory DB init error: {error}")


def save_fact(key, value, category="user_preference"):
    key_clean = key.strip().lower()
    value_clean = value.strip()
    now = datetime.now().isoformat()
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO facts (key, value, category, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value=excluded.value,
                    category=excluded.category,
                    updated_at=excluded.updated_at
            """, (key_clean, value_clean, category, now, now))
            conn.commit()
            return f"Saved memory: {key} = {value}"
    except Exception as error:
        print(f"Save fact error: {error}")
        return f"Couldn't save memory due to error: {error}"


def get_fact(key):
    key_clean = key.strip().lower()
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM facts WHERE key = ?", (key_clean,))
            row = cursor.fetchone()
            if row:
                return row[0]
            return None
    except Exception as error:
        print(f"Get fact error: {error}")
        return None


def get_all_facts():
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value, category FROM facts ORDER BY category, key")
            rows = cursor.fetchall()
            return [{"key": row[0], "value": row[1], "category": row[2]} for row in rows]
    except Exception as error:
        print(f"Get all facts error: {error}")
        return []


def delete_fact(key):
    key_clean = key.strip().lower()
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM facts WHERE key = ?", (key_clean,))
            conn.commit()
            return f"Forgot memory for {key}."
    except Exception as error:
        print(f"Delete fact error: {error}")
        return f"Error deleting memory: {error}"


def log_interaction(user_input, assistant_response):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO interaction_log (user_input, assistant_response) VALUES (?, ?)",
                (user_input, assistant_response)
            )
            conn.commit()
    except Exception as error:
        print(f"Log interaction error: {error}")


def search_memory(query):
    query_clean = f"%{query.strip().lower()}%"
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT key, value FROM facts
                WHERE key LIKE ? OR value LIKE ?
            """, (query_clean, query_clean))
            rows = cursor.fetchall()
            if rows:
                results = [f"{row[0]}: {row[1]}" for row in rows]
                return "\n".join(results)
            return "No matching memories found."
    except Exception as error:
        print(f"Search memory error: {error}")
        return f"Memory search failed: {error}"


def get_formatted_memory_context():
    facts = get_all_facts()
    if not facts:
        return ""
    fact_strings = [f"- {f['key']}: {f['value']}" for f in facts]
    return "Stored Memories & Preferences:\n" + "\n".join(fact_strings)


# Initialize DB on module import
init_db()

if __name__ == "__main__":
    print(save_fact("favorite browser", "Google Chrome"))
    print(save_fact("city", "Mumbai"))
    print("All facts:", get_all_facts())
    print("Formatted memory context:\n", get_formatted_memory_context())
