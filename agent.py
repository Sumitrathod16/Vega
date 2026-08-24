import json

from ollama import chat

from apps import open_application
from web_search import search_web
from screen_reader import analyze_screen

from system_control import (
    volume_up,
    volume_down,
    set_volume,
    mute,
    unmute
)


MODEL = "llama3.2:3b"


# Tool Registry
AVAILABLE_TOOLS = {
    "open_app": {
        "description": "Open an installed application",
        "example": {
            "tool": "open_app",
            "argument": "chrome"
        }
    },

    "web_search": {
        "description": "Search the internet",
        "example": {
            "tool": "web_search",
            "argument": "React documentation"
        }
    },

    "set_volume": {
        "description": "Set system volume to an exact percentage",
        "example": {
            "tool": "set_volume",
            "argument": 40
        }
    },

    "volume_up": {
        "description": "Increase system volume by a percentage",
        "example": {
            "tool": "volume_up",
            "argument": 10
        }
    },

    "volume_down": {
        "description": "Decrease system volume by a percentage",
        "example": {
            "tool": "volume_down",
            "argument": 10
        }
    },

    "mute": {
        "description": "Mute system audio",
        "example": {
            "tool": "mute",
            "argument": None
        }
    },

    "unmute": {
        "description": "Unmute system audio",
        "example": {
            "tool": "unmute",
            "argument": None
        }
    },

    "screen_check": {
        "description": "Analyze the current computer screen",
        "example": {
            "tool": "screen_check",
            "argument": "What is currently visible?"
        }
    }
}


# Planner
def create_plan(user_goal):

    tools_description = json.dumps(
        AVAILABLE_TOOLS,
        indent=2
    )

    prompt = f"""
You are the task planner for VEGA.

The user gave this goal:

{user_goal}

Available tools:

{tools_description}

Break the goal into the smallest necessary executable steps.

Rules:

- Use only available tools.
- Do not invent tool names.
- Do not perform dangerous actions.
- Keep the number of steps minimal.
- Return valid JSON only.
- Do not include markdown.
- Do not include explanations outside JSON.

Return this exact structure:

{{
    "goal": "user goal",
    "steps": [
        {{
            "tool": "tool_name",
            "argument": "tool argument"
        }}
    ]
}}
"""

    response = chat(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    raw_response = response.message.content.strip()

    raw_response = raw_response.replace(
        "```json",
        ""
    )

    raw_response = raw_response.replace(
        "```",
        ""
    )

    return json.loads(
        raw_response.strip()
    )


# Tool Executor
def execute_tool(tool_name, argument=None):

    if tool_name == "open_app":

        success, message = open_application(
            str(argument)
        )

        return message

    if tool_name == "web_search":

        results = search_web(
            str(argument)
        )

        if not results:
            return "No useful web results were found."

        return results

    if tool_name == "set_volume":

        return set_volume(
            int(argument)
        )

    if tool_name == "volume_up":

        amount = int(
            argument or 10
        )

        return volume_up(
            amount
        )

    if tool_name == "volume_down":

        amount = int(
            argument or 10
        )

        return volume_down(
            amount
        )

    if tool_name == "mute":

        return mute()

    if tool_name == "unmute":

        return unmute()

    if tool_name == "screen_check":

        return analyze_screen(
            str(argument)
        )

    return (
        f"Unknown tool: {tool_name}"
    )


# Agent
def execute_goal(user_goal):

    try:

        print(
            f"Creating task plan for: {user_goal}"
        )

        plan = create_plan(
            user_goal
        )

    except Exception as error:

        return (
            f"I couldn't create a task plan. "
            f"Planner error: {error}"
        )

    steps = plan.get(
        "steps",
        []
    )

    if not steps:

        return (
            "I couldn't determine any executable steps."
        )

    results = []

    for index, step in enumerate(
        steps,
        start=1
    ):

        tool_name = step.get(
            "tool"
        )

        argument = step.get(
            "argument"
        )

        if tool_name not in AVAILABLE_TOOLS:

            results.append(
                f"Step {index} skipped because "
                f"{tool_name} is not an allowed tool."
            )

            continue

        try:

            print(
                f"Executing step {index}: "
                f"{tool_name} -> {argument}"
            )

            result = execute_tool(
                tool_name,
                argument
            )

            results.append(
                f"Step {index}: {result}"
            )

        except Exception as error:

            results.append(
                f"Step {index} failed: {error}"
            )

            break

    return summarize_task(
        user_goal,
        results
    )


# Task Summary
def summarize_task(
    user_goal,
    results
):

    execution_log = "\n".join(
        results
    )

    prompt = f"""
You are VEGA.

The user asked you to complete this task:

{user_goal}

Execution results:

{execution_log}

Give the user a short spoken summary of what was completed.

Rules:

- Do not claim an action succeeded if the execution result says it failed.
- Do not read URLs aloud.
- Keep the response concise.
- Use the same language as the user's request.
"""

    response = chat(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.message.content.strip()


# Test
if __name__ == "__main__":

    result = execute_goal(
        "Open Chrome and increase the volume by 5 percent"
    )

    print(
        f"\nVEGA: {result}"
    )