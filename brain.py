from ollama import chat
from config import config
from memory import get_formatted_memory_context, log_interaction

MODEL = config.get("models", {}).get("chat_model", "llama3.2:3b")
USER_NAME = config.get("user_name", "Sumit")
ASSISTANT_NAME = config.get("assistant_name", "VEGA")

# Language Rules
LANGUAGE_RULES = """
Language rules:
- If the user asks in English, respond only in English.
- If the user writes in Hindi using Devanagari script, respond in Hindi.
- If the user explicitly says "in Hindi", "Hindi me", or "Hindi mein", respond in Hindi.
- If the user explicitly says "in English", "English me", or "English mein", respond only in English.
- If the user naturally speaks Hinglish, you may respond in Hinglish.
- Never switch an English question into Hindi unless the user requests Hindi.
- Keep the response in the same language throughout unless the user asks to switch.
- Technical terms, code, filenames, library names and error names may remain in English.
"""


def build_system_prompt():
    memory_context = get_formatted_memory_context()
    prompt = f"""
You are {ASSISTANT_NAME}, a personal AI desktop assistant.

Personality:
- Intelligent
- Calm
- Friendly
- Casual
- Slightly witty
- Natural and conversational
- Helpful without sounding robotic

The user's name is {USER_NAME}.

You may naturally call the user:
- {USER_NAME}
- bro
- boss

Do not use the user's name in every response.

{LANGUAGE_RULES}

{memory_context}

Your responses will be spoken aloud.

Therefore:
- Speak naturally.
- Avoid unnecessary markdown.
- Avoid headings unless required.
- Avoid bullet points in normal conversation.
- Use normal conversational sentences.
- Keep everyday answers around 2 to 5 sentences.
- Give longer answers only when the user asks for detail.
"""
    return prompt


conversation = [
    {
        "role": "system",
        "content": build_system_prompt()
    }
]


# Web Routing
def should_use_web(user_message):
    prompt = f"""
You are the routing system for {ASSISTANT_NAME}.

Decide whether this user request requires current or real-time internet information.

Use WEB for:
- latest news
- current events
- today's information
- weather
- current sports scores or results
- current prices
- current software versions
- current jobs or hiring
- current company information
- current political figures
- recent releases
- live information
- anything likely to have changed recently

Use LOCAL for:
- programming explanations
- coding help
- general knowledge
- definitions
- mathematics
- casual conversation
- writing help
- historical facts unlikely to change

User request:
{user_message}

Reply with exactly one word:
WEB
or
LOCAL
"""

    response = chat(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}]
    )

    decision = response.message.content.strip().upper()
    return decision.startswith("WEB")


# Normal Conversation
def ask_vega(user_message):
    # Dynamically update system prompt with current memory context
    conversation[0]["content"] = build_system_prompt()

    conversation.append({"role": "user", "content": user_message})

    response = chat(
        model=MODEL,
        messages=conversation
    )

    answer = response.message.content.strip()
    conversation.append({"role": "assistant", "content": answer})

    # Log interaction to persistent DB
    log_interaction(user_message, answer)

    return answer


# Web Conversation
def ask_vega_with_web(question, search_results):
    prompt = f"""
You are {ASSISTANT_NAME}, a personal AI desktop assistant.

{LANGUAGE_RULES}

The user asked:
{question}

Current web search results:
{search_results}

Answer the user's actual question using the web results.

Rules:
- Use the search results for current facts.
- Do not invent facts that are not supported by the supplied results.
- If the search results are insufficient, clearly say so.
- Do not read URLs aloud.
- Mention source or website names only when useful.
- Keep the answer natural and concise.
- Do not unnecessarily use markdown.
- The response will be spoken aloud.
"""

    response = chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": build_system_prompt()},
            {"role": "user", "content": prompt}
        ]
    )

    answer = response.message.content.strip()
    log_interaction(question, answer)
    return answer


# Clear Conversation
def clear_conversation():
    global conversation
    conversation = [
        {
            "role": "system",
            "content": build_system_prompt()
        }
    ]