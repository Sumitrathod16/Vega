import json
import re

import ollama

from apps import open_application
from web_search import search_web

from system_control import (
    set_volume,
    volume_up,
    volume_down,
    mute,
    unmute
)

from screen_reader import analyze_screen

from browser_control import (
    open_url,
    browser_search,
    browser_back,
    browser_forward,
    refresh_page,
    new_tab,
    close_tab,
    next_tab,
    previous_tab
)


MODEL = "llama3.2:3b"


TOOLS = {
    "open_app": open_application,
    "web_search": search_web,

    "set_volume": set_volume,
    "volume_up": volume_up,
    "volume_down": volume_down,
    "mute": mute,
    "unmute": unmute,

    "screen_check": analyze_screen,

    "browser_open": open_url,
    "browser_search": browser_search,
    "browser_back": browser_back,
    "browser_forward": browser_forward,
    "browser_refresh": refresh_page,
    "browser_new_tab": new_tab,
    "browser_close_tab": close_tab,
    "browser_next_tab": next_tab,
    "browser_previous_tab": previous_tab
}


NO_ARGUMENT_TOOLS = {
    "mute",
    "unmute",
    "browser_back",
    "browser_forward",
    "browser_refresh",
    "browser_new_tab",
    "browser_close_tab",
    "browser_next_tab",
    "browser_previous_tab"
}


FAILURE_KEYWORDS = [
    "failed",
    "couldn't",
    "could not",
    "unable",
    "error",
    "not found",
    "doesn't exist",
    "does not exist",
    "invalid",
    "unavailable",
    "timed out",
    "timeout"
]


SUCCESS_KEYWORDS = [
    "opened",
    "success",
    "completed",
    "done",
    "executed",
    "created",
    "started",
    "searched",
    "loaded",
    "refreshed",
    "closed",
    "switched",
    "muted",
    "unmuted",
    "volume"
]


def clean_json_response(text):

    if not text:
        return ""

    text = text.strip()

    text = re.sub(
        r"```json",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = text.replace(
        "```",
        ""
    )

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        return text

    return text[
        start:end + 1
    ]


def validate_plan(plan):

    if not isinstance(
        plan,
        dict
    ):
        return False

    if "goal" not in plan:
        return False

    if "steps" not in plan:
        return False

    if not isinstance(
        plan["steps"],
        list
    ):
        return False

    for step in plan["steps"]:

        if not isinstance(
            step,
            dict
        ):
            return False

        tool_name = step.get(
            "tool"
        )

        if tool_name not in TOOLS:
            return False

    return True


def create_plan(goal):

    available_tools = "\n".join(
        f"- {tool}"
        for tool in TOOLS
    )

    prompt = f"""
You are VEGA's task planning engine.

Convert the user's goal into a minimal sequence of executable steps.

Available tools:

{available_tools}

For every step you MUST provide:

1. tool
2. argument
3. expected_result

expected_result describes what should be visible or true after the tool executes.

Examples:

Opening Chrome:
expected_result:
"Chrome browser window should be visible."

Searching Google for Python:
expected_result:
"Google search results for Python should be visible."

Opening GitHub:
expected_result:
"GitHub website should be visible in the browser."

Rules:

- Only use tools from the provided list.
- Do not invent tools.
- Keep steps minimal.
- For tools without arguments, use an empty string.
- Return ONLY valid JSON.

Required format:

{{
    "goal": "user goal",
    "steps": [
        {{
            "tool": "tool_name",
            "argument": "argument",
            "expected_result": "expected result"
        }}
    ]
}}

User goal:

{goal}
"""

    response = ollama.chat(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    content = response[
        "message"
    ][
        "content"
    ]

    clean_content = clean_json_response(
        content
    )

    try:

        plan = json.loads(
            clean_content
        )

    except json.JSONDecodeError as error:

        print(
            f"Agent plan JSON error: {error}"
        )

        return None

    if not validate_plan(
        plan
    ):

        print(
            "Agent generated an invalid plan."
        )

        return None

    return plan


def normalize_tool_result(result):

    normalized = {
        "success": None,
        "message": "",
        "raw_result": result
    }

    if result is None:

        normalized["success"] = False
        normalized["message"] = (
            "Tool returned no result."
        )

        return normalized


    if isinstance(
        result,
        tuple
    ):

        if len(result) >= 2:

            first = result[0]
            second = result[1]

            if isinstance(
                first,
                bool
            ):

                normalized["success"] = first
                normalized["message"] = str(
                    second
                )

                return normalized


    if isinstance(
        result,
        dict
    ):

        if "success" in result:

            normalized["success"] = bool(
                result["success"]
            )

        message = (
            result.get("message")
            or result.get("response")
            or result.get("result")
            or str(result)
        )

        normalized["message"] = str(
            message
        )

        return normalized


    if isinstance(
        result,
        bool
    ):

        normalized["success"] = result

        normalized["message"] = (
            "Tool completed successfully."
            if result
            else "Tool reported failure."
        )

        return normalized


    if isinstance(
        result,
        list
    ):

        normalized["success"] = (
            len(result) > 0
        )

        normalized["message"] = (
            f"Tool returned {len(result)} results."
            if result
            else "Tool returned no results."
        )

        return normalized


    if isinstance(
        result,
        str
    ):

        text = result.strip()

        normalized["message"] = text

        lower_text = text.lower()

        if any(
            keyword in lower_text
            for keyword in FAILURE_KEYWORDS
        ):

            normalized["success"] = False
            return normalized

        if any(
            keyword in lower_text
            for keyword in SUCCESS_KEYWORDS
        ):

            normalized["success"] = True
            return normalized

        normalized["success"] = None

        return normalized


    normalized["message"] = str(
        result
    )

    return normalized


def verify_tool_result(
    tool_name,
    argument,
    result
):

    normalized = normalize_tool_result(
        result
    )

    verification = {
        "tool": tool_name,
        "argument": argument,
        "status": "unknown",
        "success": False,
        "message": normalized["message"],
        "raw_result": normalized[
            "raw_result"
        ]
    }

    if normalized[
        "success"
    ] is True:

        verification["status"] = (
            "success"
        )

        verification["success"] = True

        return verification


    if normalized[
        "success"
    ] is False:

        verification["status"] = (
            "failed"
        )

        verification["success"] = False

        return verification


    return verification


def execute_tool(
    tool_name,
    argument=None
):

    tool = TOOLS.get(
        tool_name
    )

    if not tool:

        return {
            "success": False,
            "result": None,
            "error": (
                f"Unknown tool: "
                f"{tool_name}"
            )
        }

    try:

        if tool_name in NO_ARGUMENT_TOOLS:

            result = tool()

        else:

            result = tool(
                argument
            )

        return {
            "success": True,
            "result": result,
            "error": None
        }

    except Exception as error:

        print(
            f"Agent tool error "
            f"[{tool_name}]: "
            f"{error}"
        )

        return {
            "success": False,
            "result": None,
            "error": str(error)
        }


# Phase 2 Screen Verification
def verify_with_screen(
    tool_name,
    argument,
    expected_result
):

    print(
        "Running screen verification..."
    )

    try:

        verification_question = (
            "Check the current screen and describe what is visible. "
            "Focus only on information useful for verifying this action. "
            f"The action performed was: {tool_name}. "
            f"The argument was: {argument}. "
            f"The expected result is: {expected_result}"
        )

        screen_context = analyze_screen(
            verification_question
        )

    except Exception as error:

        print(
            f"Screen verification error: {error}"
        )

        return {
            "status": "unknown",
            "success": False,
            "message": (
                "Screen analysis failed."
            ),
            "screen_context": ""
        }


    if not screen_context:

        return {
            "status": "unknown",
            "success": False,
            "message": (
                "Screen analysis returned no information."
            ),
            "screen_context": ""
        }


    prompt = f"""
You are VEGA's verification engine.

Determine whether the performed computer action succeeded.

Action:
{tool_name}

Argument:
{argument}

Expected result:
{expected_result}

Current screen description:
{screen_context}

You must return ONLY JSON.

Possible statuses:

success
failed
unknown

Use:

success:
The screen clearly confirms the expected result.

failed:
The screen clearly contradicts the expected result or shows an error.

unknown:
There is not enough evidence to decide.

Required JSON:

{{
    "status": "success",
    "reason": "short explanation"
}}
"""

    try:

        response = ollama.chat(
            model=MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        result_text = response[
            "message"
        ][
            "content"
        ]

        result_text = clean_json_response(
            result_text
        )

        result = json.loads(
            result_text
        )

    except Exception as error:

        print(
            f"Verification reasoning error: {error}"
        )

        return {
            "status": "unknown",
            "success": False,
            "message": (
                "I couldn't interpret the screen verification."
            ),
            "screen_context": screen_context
        }


    status = (
        result.get(
            "status",
            "unknown"
        )
        .strip()
        .lower()
    )

    if status not in {
        "success",
        "failed",
        "unknown"
    }:

        status = "unknown"


    reason = result.get(
        "reason",
        "No verification reason provided."
    )


    return {
        "status": status,
        "success": status == "success",
        "message": reason,
        "screen_context": screen_context
    }


def format_step_result(
    step_number,
    tool_name,
    verification
):

    return {
        "step": step_number,
        "tool": tool_name,
        "status": verification[
            "status"
        ],
        "message": verification[
            "message"
        ]
    }


def summarize_execution(
    goal,
    execution_log
):

    total = len(
        execution_log
    )

    if total == 0:

        return (
            "I couldn't execute the task."
        )


    failed_steps = [
        step
        for step in execution_log
        if step["status"] == "failed"
    ]


    unknown_steps = [
        step
        for step in execution_log
        if step["status"] == "unknown"
    ]


    successful_steps = [
        step
        for step in execution_log
        if step["status"] == "success"
    ]


    if len(successful_steps) == total:

        return (
            "Task completed successfully. "
            f"I verified all {total} steps."
        )


    if failed_steps:

        step = failed_steps[0]

        return (
            f"I stopped at step "
            f"{step['step']} because verification failed. "
            f"{step['message']}"
        )


    if unknown_steps:

        step = unknown_steps[0]

        return (
            f"I completed step "
            f"{step['step']}, but I couldn't verify "
            f"the result confidently. "
            f"{step['message']}"
        )


    return (
        "The task finished, but verification "
        "was incomplete."
    )


def execute_goal(goal):

    print(
        "\nVEGA AGENT MODE"
    )

    print(
        f"Goal: {goal}"
    )


    plan = create_plan(
        goal
    )

    if not plan:

        return (
            "I couldn't create a valid plan "
            "for that task."
        )


    steps = plan.get(
        "steps",
        []
    )


    if not steps:

        return (
            "The task plan contains "
            "no executable steps."
        )


    print(
        "\nAgent Plan:"
    )


    for index, step in enumerate(
        steps,
        start=1
    ):

        print(
            f"{index}. "
            f"{step.get('tool')} "
            f"-> {step.get('argument', '')}"
        )

        print(
            f"   Expected: "
            f"{step.get('expected_result', '')}"
        )


    execution_log = []


    for index, step in enumerate(
        steps,
        start=1
    ):

        tool_name = step.get(
            "tool"
        )

        argument = step.get(
            "argument",
            ""
        )

        expected_result = step.get(
            "expected_result",
            ""
        )


        print(
            f"\nExecuting step "
            f"{index}: "
            f"{tool_name}"
        )


        execution = execute_tool(
            tool_name,
            argument
        )


        if not execution[
            "success"
        ]:

            verification = {
                "status": "failed",
                "success": False,
                "message": (
                    execution["error"]
                    or
                    "Tool execution failed."
                )
            }

        else:

            verification = verify_tool_result(
                tool_name,
                argument,
                execution["result"]
            )


        print(
            f"Tool verification: "
            f"{verification['status']}"
        )


        # Phase 2
        # If normal verification is unknown,
        # check the actual screen.
        if (
            verification["status"]
            == "unknown"
        ):

            screen_verification = verify_with_screen(
                tool_name,
                argument,
                expected_result
            )

            verification = (
                screen_verification
            )

            print(
                f"Screen verification: "
                f"{verification['status']}"
            )

            print(
                f"Reason: "
                f"{verification['message']}"
            )


        step_result = format_step_result(
            index,
            tool_name,
            verification
        )

        execution_log.append(
            step_result
        )


        if verification[
            "status"
        ] == "failed":

            print(
                "Agent stopped because "
                "verification failed."
            )

            break


        if verification[
            "status"
        ] == "unknown":

            print(
                "Agent stopped because "
                "the result is still uncertain."
            )

            break


        print(
            f"Step {index} verified successfully."
        )


    print(
        "\nAgent Execution Log:"
    )


    for item in execution_log:

        print(
            f"Step {item['step']} | "
            f"{item['tool']} | "
            f"{item['status']} | "
            f"{item['message']}"
        )


    return summarize_execution(
        goal,
        execution_log
    )