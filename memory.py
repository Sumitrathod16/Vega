import os
import sqlite3

from datetime import datetime


DB_NAME = "vega_memory.db"

DB_PATH = os.path.join(
    os.path.dirname(__file__),
    DB_NAME
)


# Connection
def get_connection():

    return sqlite3.connect(
        DB_PATH
    )


# Database Initialization
def init_db():

    try:

        with get_connection() as conn:

            cursor = conn.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT NOT NULL,
                    category TEXT DEFAULT 'general',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS interaction_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_input TEXT NOT NULL,
                    assistant_response TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
                """
            )

            conn.commit()

    except Exception as error:

        print(
            f"Memory database initialization error: {error}"
        )


# Save Memory
def save_fact(
    key,
    value,
    category="general"
):

    key_clean = key.strip().lower()
    value_clean = value.strip()
    category_clean = category.strip().lower()

    if not key_clean or not value_clean:

        return (
            "Memory key and value cannot be empty."
        )

    now = datetime.now().isoformat()

    try:

        with get_connection() as conn:

            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO facts (
                    key,
                    value,
                    category,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?)

                ON CONFLICT(key)
                DO UPDATE SET
                    value = excluded.value,
                    category = excluded.category,
                    updated_at = excluded.updated_at
                """,
                (
                    key_clean,
                    value_clean,
                    category_clean,
                    now,
                    now
                )
            )

            conn.commit()

            return (
                f"Remembered {key_clean}: "
                f"{value_clean}"
            )

    except Exception as error:

        print(
            f"Save memory error: {error}"
        )

        return (
            "I couldn't save that memory."
        )


# Get Memory
def get_fact(key):

    key_clean = key.strip().lower()

    if not key_clean:
        return None

    try:

        with get_connection() as conn:

            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT value
                FROM facts
                WHERE key = ?
                """,
                (
                    key_clean,
                )
            )

            row = cursor.fetchone()

            if row:
                return row[0]

            return None

    except Exception as error:

        print(
            f"Get memory error: {error}"
        )

        return None


# Get Full Fact
def get_fact_details(key):

    key_clean = key.strip().lower()

    try:

        with get_connection() as conn:

            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    key,
                    value,
                    category,
                    created_at,
                    updated_at
                FROM facts
                WHERE key = ?
                """,
                (
                    key_clean,
                )
            )

            row = cursor.fetchone()

            if not row:
                return None

            return {
                "key": row[0],
                "value": row[1],
                "category": row[2],
                "created_at": row[3],
                "updated_at": row[4]
            }

    except Exception as error:

        print(
            f"Get fact details error: {error}"
        )

        return None


# Get All Memories
def get_all_facts():

    try:

        with get_connection() as conn:

            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    key,
                    value,
                    category,
                    created_at,
                    updated_at
                FROM facts
                ORDER BY updated_at DESC
                """
            )

            rows = cursor.fetchall()

            memories = []

            for row in rows:

                memories.append(
                    {
                        "key": row[0],
                        "value": row[1],
                        "category": row[2],
                        "created_at": row[3],
                        "updated_at": row[4]
                    }
                )

            return memories

    except Exception as error:

        print(
            f"Get all memories error: {error}"
        )

        return []


# Delete Memory
def delete_fact(key):

    key_clean = key.strip().lower()

    if not key_clean:

        return (
            "Tell me what memory to forget."
        )

    try:

        with get_connection() as conn:

            cursor = conn.cursor()

            cursor.execute(
                """
                DELETE FROM facts
                WHERE key = ?
                """,
                (
                    key_clean,
                )
            )

            deleted = cursor.rowcount

            conn.commit()

            if deleted:

                return (
                    f"Forgot memory for {key_clean}."
                )

            return (
                f"I don't have a memory named "
                f"{key_clean}."
            )

    except Exception as error:

        print(
            f"Delete memory error: {error}"
        )

        return (
            "I couldn't delete that memory."
        )


# Clear All Memories
def clear_all_facts():

    try:

        with get_connection() as conn:

            cursor = conn.cursor()

            cursor.execute(
                """
                DELETE FROM facts
                """
            )

            conn.commit()

            return (
                "All stored memories have been cleared."
            )

    except Exception as error:

        print(
            f"Clear memory error: {error}"
        )

        return (
            "I couldn't clear the memories."
        )


# Search Memory
def search_memory(query):

    query = query.strip().lower()

    if not query:
        return []

    words = [
        word
        for word in query.split()
        if len(word) >= 3
    ]

    try:

        facts = get_all_facts()

        matches = []

        for fact in facts:

            searchable_text = (
                f"{fact['key']} "
                f"{fact['value']} "
                f"{fact['category']}"
            ).lower()

            score = 0

            if query in searchable_text:
                score += 10

            for word in words:

                if word in searchable_text:
                    score += 1

            if score > 0:

                matches.append(
                    {
                        "key": fact["key"],
                        "value": fact["value"],
                        "category": fact["category"],
                        "score": score
                    }
                )

        matches.sort(
            key=lambda item: item["score"],
            reverse=True
        )

        return matches

    except Exception as error:

        print(
            f"Memory search error: {error}"
        )

        return []


# Relevant Memory Context
def get_relevant_memory_context(
    query,
    limit=10
):

    matches = search_memory(
        query
    )

    if not matches:
        return ""

    matches = matches[
        :limit
    ]

    memory_lines = []

    for memory in matches:

        memory_lines.append(
            f"- {memory['key']}: "
            f"{memory['value']}"
        )

    return (
        "Relevant stored memories:\n"
        + "\n".join(memory_lines)
    )


# Full Memory Context
def get_formatted_memory_context():

    facts = get_all_facts()

    if not facts:
        return ""

    memory_lines = []

    for fact in facts:

        memory_lines.append(
            f"- {fact['key']}: "
            f"{fact['value']}"
        )

    return (
        "Stored memories and preferences:\n"
        + "\n".join(memory_lines)
    )


# Interaction Log
def log_interaction(
    user_input,
    assistant_response
):

    if not user_input:
        return

    if not assistant_response:
        return

    timestamp = datetime.now().isoformat()

    try:

        with get_connection() as conn:

            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO interaction_log (
                    user_input,
                    assistant_response,
                    timestamp
                )
                VALUES (?, ?, ?)
                """,
                (
                    user_input.strip(),
                    assistant_response.strip(),
                    timestamp
                )
            )

            conn.commit()

    except Exception as error:

        print(
            f"Interaction log error: {error}"
        )


# Recent Interactions
def get_recent_interactions(
    limit=10
):

    try:

        with get_connection() as conn:

            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    user_input,
                    assistant_response,
                    timestamp
                FROM interaction_log
                ORDER BY id DESC
                LIMIT ?
                """,
                (
                    limit,
                )
            )

            rows = cursor.fetchall()

            interactions = []

            for row in rows:

                interactions.append(
                    {
                        "user_input": row[0],
                        "assistant_response": row[1],
                        "timestamp": row[2]
                    }
                )

            interactions.reverse()

            return interactions

    except Exception as error:

        print(
            f"Recent interaction error: {error}"
        )

        return []


# Recent Conversation Context
def get_recent_interaction_context(
    limit=5
):

    interactions = get_recent_interactions(
        limit
    )

    if not interactions:
        return ""

    lines = []

    for interaction in interactions:

        lines.append(
            f"User: {interaction['user_input']}"
        )

        lines.append(
            f"VEGA: {interaction['assistant_response']}"
        )

    return (
        "Recent conversation history:\n"
        + "\n".join(lines)
    )


# Clear Interaction History
def clear_interaction_history():

    try:

        with get_connection() as conn:

            cursor = conn.cursor()

            cursor.execute(
                """
                DELETE FROM interaction_log
                """
            )

            conn.commit()

            return (
                "Interaction history cleared."
            )

    except Exception as error:

        print(
            f"Clear interaction history error: {error}"
        )

        return (
            "I couldn't clear interaction history."
        )


init_db()


# Test
if __name__ == "__main__":

    print(
        save_fact(
            "favorite browser",
            "Google Chrome",
            "preference"
        )
    )

    print(
        save_fact(
            "current project",
            "VEGA AI Assistant",
            "project"
        )
    )

    print(
        get_fact(
            "current project"
        )
    )

    print(
        search_memory(
            "what project am I working on"
        )
    )

    print(
        get_formatted_memory_context()
    )