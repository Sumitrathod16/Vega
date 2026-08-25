import json
import os
import sqlite3
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from ollama import chat


MEMORY_DB = os.getenv(
    "VEGA_MEMORY_DB",
    os.path.join(
        os.path.expanduser("~"),
        ".vega",
        "memory.db"
    )
)
MEMORY_URL = os.getenv("VEGA_MEMORY_URL", "").rstrip("/")
USER_ID = os.getenv("VEGA_USER_ID", "sumit").strip() or "sumit"
MAX_HISTORY_MESSAGES = 40


def _ensure_memory_db():

    memory_directory = os.path.dirname(MEMORY_DB)

    if memory_directory:

        os.makedirs(
            memory_directory,
            exist_ok=True
        )

    with sqlite3.connect(MEMORY_DB) as database:

        database.execute(
            """
            CREATE TABLE IF NOT EXISTS conversation_messages (
                user_id TEXT NOT NULL,
                message_index INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                PRIMARY KEY (user_id, message_index)
            )
            """
        )


def _load_local_history():

    _ensure_memory_db()

    with sqlite3.connect(MEMORY_DB) as database:

        rows = database.execute(
            """
            SELECT role, content
            FROM conversation_messages
            WHERE user_id = ?
            ORDER BY message_index
            """,
            (USER_ID,)
        ).fetchall()

    return [
        {
            "role": role,
            "content": content
        }
        for role, content in rows
    ]


def _save_local_history(messages):

    _ensure_memory_db()

    with sqlite3.connect(MEMORY_DB) as database:

        database.execute(
            "DELETE FROM conversation_messages WHERE user_id = ?",
            (USER_ID,)
        )

        database.executemany(
            """
            INSERT INTO conversation_messages
                (user_id, message_index, role, content)
            VALUES (?, ?, ?, ?)
            """,
            [
                (USER_ID, index, message["role"], message["content"])
                for index, message in enumerate(messages)
            ]
        )


def _load_shared_history():

    if not MEMORY_URL:
        return None

    try:

        query = urlencode({"user_id": USER_ID})
        request = Request(
            f"{MEMORY_URL}/memory?{query}",
            headers={"Accept": "application/json"}
        )

        with urlopen(request, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))

        messages = data.get("messages")

        if isinstance(messages, list):
            return messages

    except (OSError, URLError, ValueError, KeyError) as error:

        print(f"Shared memory unavailable: {error}")

    return None


def _save_shared_history(messages):

    if not MEMORY_URL:
        return

    try:

        payload = json.dumps(
            {
                "user_id": USER_ID,
                "messages": messages
            }
        ).encode("utf-8")

        request = Request(
            f"{MEMORY_URL}/memory",
            data=payload,
            method="POST",
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
        )

        with urlopen(request, timeout=5):
            pass

    except (OSError, URLError, ValueError) as error:

        print(f"Could not save shared memory: {error}")


def _load_conversation():

    shared_history = _load_shared_history()
    history = (
        _load_local_history()
        if shared_history is None
        else shared_history
    )

    valid_history = [
        message
        for message in history
        if isinstance(message, dict)
        and message.get("role") in {"user", "assistant"}
        and isinstance(message.get("content"), str)
    ]

    conversation_history = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ] + valid_history[-MAX_HISTORY_MESSAGES:]

    if shared_history:
        _save_local_history(conversation_history)

    return conversation_history


def should_use_web(user_message):

    prompt = f"""
You are a routing system for VEGA.

Decide whether the user's question requires current or real-time internet information.

Use web search for:
- latest news
- current events
- today's information
- weather
- sports scores/results
- current prices
- current software versions
- current jobs/hiring
- current company information
- current political figures
- recent releases
- anything that may have changed recently

Do NOT use web search for:
- programming explanations
- general knowledge
- definitions
- mathematics
- casual conversation
- coding help
- historical facts that are unlikely to change

User message:
{user_message}

Reply with ONLY one word:

WEB

or

LOCAL
"""

    response = chat(
        model="llama3.2:3b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    decision = response.message.content.strip().upper()

    return decision.startswith("WEB")

SYSTEM_PROMPT = """
You are VEGA, a personal AI assistant.

Personality:
- Intelligent
- Calm
- Friendly
- Casual
- Slightly witty
- Natural and conversational
- Helpful but not robotic

The user's name is Sumit.

You can naturally call the user:
- Sumit
- bro
- boss

Do not use the user's name in every sentence.

If the user speaks Hindi or Hinglish,
respond naturally in Hinglish.

IMPORTANT:
Your responses will be spoken aloud.

Therefore:
- Do not use markdown unless absolutely necessary.
- Avoid headings.
- Avoid bullet points in normal conversation.
- Speak naturally.
- Use normal sentences.
- Keep everyday answers around 2 to 5 sentences.
- Give longer answers only when the user asks for details.
"""


conversation = _load_conversation()


def ask_vega(user_message):

    conversation.append(
        {
            "role": "user",
            "content": user_message
        }
    )

    response = chat(
        model="llama3.2:3b",
        messages=conversation
    )

    answer = response.message.content.strip()

    conversation.append(
        {
            "role": "assistant",
            "content": answer
        }
    )

    conversation[:] = [
        conversation[0]
    ] + conversation[1:][-MAX_HISTORY_MESSAGES:]

    _save_local_history(conversation)
    _save_shared_history(conversation[1:])

    return answer
    

def ask_vega_with_web(
    question,
    search_results
):

    web_prompt = f"""
The user asked:

{question}

I searched the internet and found these results:

{search_results}

Answer the user's question using the search results above.

Important rules:

1. Base current facts on the supplied search results.
2. Do not invent information that is not supported by them.
3. If the results don't contain enough information, say so.
4. Give a concise natural spoken answer.
5. Do not read URLs aloud.
6. Do not use markdown unless necessary.
7. Mention the source/site name naturally when useful.
8. Your answer will be spoken aloud by VEGA.
"""

    return ask_vega(
        web_prompt
    )    