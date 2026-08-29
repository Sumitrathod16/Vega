import json
from ollama import chat

from apps import open_application
from web_search import search_web
from screen_reader import analyze_screen
from config import config
from memory import save_fact, search_memory, get_all_facts

from system_control import (
    volume_up,
    volume_down,
    set_volume,
    mute,
    unmute,
    media_control,
    lock_pc,
    get_system_status,
    take_screenshot
)

from browser_control import (
    open_url,
    browser_search,
    new_tab,
    close_tab,
    next_tab,
    previous_tab,
    browser_back,
    browser_forward,
    refresh_page
)

MODEL = config.get("models", {}).get("chat_model", "llama3.2:3b")

# Tool Registry
AVAILABLE_TOOLS = {
    "open_app": {
        "description": "Open an installed desktop application",
        "example": {
            "tool": "open_app",
            "argument": "chrome"
        }
    },
    "web_search": {
        "description": "Search the internet for dynamic info",
        "example": {
            "tool": "web_search",
            "argument": "React documentation"
        }
    },
    "open_url": {
        "description": "Open a website URL in the browser",
        "example": {
            "tool": "open_url",
            "argument": "https://github.com"
        }
    },
    "browser_search": {
        "description": "Perform a Google search in browser tab",
        "example": {
            "tool": "browser_search",
            "argument": "latest news"
        }
    },
    "new_tab": {
        "description": "Open a new browser tab",
        "example": {
            "tool": "new_tab",
            "argument": "https://youtube.com"
        }
    },
    "close_tab": {
        "description": "Close current browser tab",
        "example": {
            "tool": "close_tab",
            "argument": None
        }
    },
    "next_tab": {
        "description": "Switch to next browser tab",
        "example": {
            "tool": "next_tab",
            "argument": None
        }
    },
    "previous_tab": {
        "description": "Switch to previous browser tab",
        "example": {
            "tool": "previous_tab",
            "argument": None
        }
    },
    "browser_back": {
        "description": "Go back to previous browser page",
        "example": {
            "tool": "browser_back",
            "argument": None
        }
    },
    "browser_forward": {
        "description": "Go forward in browser history",
        "example": {
            "tool": "browser_forward",
            "argument": None
        }
    },
    "refresh_page": {
        "description": "Refresh current web page",
        "example": {
            "tool": "refresh_page",
            "argument": None
        }
    },
    "set_volume": {
        "description": "Set system volume to exact percentage",
        "example": {
            "tool": "set_volume",
            "argument": 40
        }
    },
    "volume_up": {
        "description": "Increase system volume by percentage",
        "example": {
            "tool": "volume_up",
            "argument": 10
        }
    },
    "volume_down": {
        "description": "Decrease system volume by percentage",
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
    "media_control": {
        "description": "Control media playback (play_pause, next, previous)",
        "example": {
            "tool": "media_control",
            "argument": "play_pause"
        }
    },
    "lock_pc": {
        "description": "Lock computer screen",
        "example": {
            "tool": "lock_pc",
            "argument": None
        }
    },
    "get_system_status": {
        "description": "Get CPU, Memory, and Battery usage status",
        "example": {
            "tool": "get_system_status",
            "argument": None
        }
    },
    "take_screenshot": {
        "description": "Take a full screen screenshot",
        "example": {
            "tool": "take_screenshot",
            "argument": None
        }
    },
    "screen_check": {
        "description": "Analyze current computer screen using visual AI",
        "example": {
            "tool": "screen_check",
            "argument": "What is currently visible?"
        }
    },
    "save_memory": {
        "description": "Save a persistent fact or user preference",
        "example": {
            "tool": "save_memory",
            "argument": "favorite_color=blue"
        }
    },
    "recall_memory": {
        "description": "Search saved persistent memories",
        "example": {
            "tool": "recall_memory",
            "argument": "favorite color"
        }
    }
}


# Planner
def create_plan(user_goal):
    tools_description = json.dumps(AVAILABLE_TOOLS, indent=2)

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
- Do not include markdown or explanations outside JSON.

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
        messages=[{"role": "user", "content": prompt}]
    )

    raw_response = response.message.content.strip()
    raw_response = raw_response.replace("```json", "").replace("```", "")

    return json.loads(raw_response.strip())


# Tool Executor
def execute_tool(tool_name, argument=None):
    if tool_name == "open_app":
        success, message = open_application(str(argument))
        return message

    if tool_name == "web_search":
        results = search_web(str(argument))
        return results if results else "No useful web results were found."

    if tool_name == "open_url":
        return open_url(str(argument))

    if tool_name == "browser_search":
        return browser_search(str(argument))

    if tool_name == "new_tab":
        return new_tab(str(argument) if argument else None)

    if tool_name == "close_tab":
        return close_tab()

    if tool_name == "next_tab":
        return next_tab()

    if tool_name == "previous_tab":
        return previous_tab()

    if tool_name == "browser_back":
        return browser_back()

    if tool_name == "browser_forward":
        return browser_forward()

    if tool_name == "refresh_page":
        return refresh_page()

    if tool_name == "set_volume":
        return set_volume(int(argument))

    if tool_name == "volume_up":
        amount = int(argument or 10)
        return volume_up(amount)

    if tool_name == "volume_down":
        amount = int(argument or 10)
        return volume_down(amount)

    if tool_name == "mute":
        return mute()

    if tool_name == "unmute":
        return unmute()

    if tool_name == "media_control":
        return media_control(str(argument or "play_pause"))

    if tool_name == "lock_pc":
        return lock_pc()

    if tool_name == "get_system_status":
        return get_system_status()

    if tool_name == "take_screenshot":
        return take_screenshot(str(argument) if argument else None)

    if tool_name == "screen_check":
        return analyze_screen(str(argument))

    if tool_name == "save_memory":
        arg_str = str(argument)
        if "=" in arg_str:
            k, v = arg_str.split("=", 1)
            return save_fact(k.strip(), v.strip())
        return save_fact("note", arg_str)

    if tool_name == "recall_memory":
        return search_memory(str(argument))

    return f"Unknown tool: {tool_name}"


# Agent Execution
def execute_goal(user_goal):
    try:
        print(f"Creating task plan for: {user_goal}")
        plan = create_plan(user_goal)
    except Exception as error:
        return f"I couldn't create a task plan. Planner error: {error}"

    steps = plan.get("steps", [])
    if not steps:
        return "I couldn't determine any executable steps."

    results = []
    for index, step in enumerate(steps, start=1):
        tool_name = step.get("tool")
        argument = step.get("argument")

        if tool_name not in AVAILABLE_TOOLS:
            results.append(
                f"Step {index} skipped because {tool_name} is not an allowed tool."
            )
            continue

        try:
            print(f"Executing step {index}: {tool_name} -> {argument}")
            result = execute_tool(tool_name, argument)
            results.append(f"Step {index}: {result}")
        except Exception as error:
            results.append(f"Step {index} failed: {error}")
            break

    return summarize_task(user_goal, results)


# Task Summary
def summarize_task(user_goal, results):
    execution_log = "\n".join(results)
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
        messages=[{"role": "user", "content": prompt}]
    )

    return response.message.content.strip()


if __name__ == "__main__":
    result = execute_goal("Get system status and set volume to 30")
    print(f"\nVEGA: {result}")