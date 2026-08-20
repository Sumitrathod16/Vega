from ollama import chat


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


conversation = [
    {
        "role": "system",
        "content": SYSTEM_PROMPT
    }
]


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