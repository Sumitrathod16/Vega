import os
from pathlib import Path

import ollama

from file_control import read_text_file
from screen_reader import analyze_screen


MODEL = "llama3.2:3b"


LANGUAGE_BY_EXTENSION = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "React JSX",
    ".ts": "TypeScript",
    ".tsx": "React TypeScript",
    ".java": "Java",
    ".cpp": "C++",
    ".c": "C",
    ".cs": "C#",
    ".php": "PHP",
    ".html": "HTML",
    ".css": "CSS",
    ".json": "JSON",
    ".sql": "SQL",
    ".go": "Go",
    ".rs": "Rust",
    ".kt": "Kotlin",
    ".swift": "Swift",
    ".sh": "Shell Script",
    ".ps1": "PowerShell"
}


def detect_language_from_path(path):

    try:

        extension = Path(
            path
        ).suffix.lower()

        return LANGUAGE_BY_EXTENSION.get(
            extension,
            "Unknown"
        )

    except Exception:
        return "Unknown"


def detect_language_from_code(code):

    if not code:
        return "Unknown"

    prompt = f"""
Identify the programming language of this code.

Return ONLY the language name.

Code:

{code[:4000]}
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

        language = (
            response["message"]["content"]
            .strip()
        )

        if not language:
            return "Unknown"

        return language

    except Exception as error:

        print(
            f"Language detection error: {error}"
        )

        return "Unknown"


def get_code_from_file(path):

    success, content = read_text_file(
        path,
        max_characters=14000
    )

    if not success:

        return {
            "success": False,
            "code": "",
            "language": "Unknown",
            "message": content
        }

    language = detect_language_from_path(
        path
    )

    if language == "Unknown":

        language = detect_language_from_code(
            content
        )

    return {
        "success": True,
        "code": content,
        "language": language,
        "message": "Code loaded successfully."
    }


def get_code_from_screen():

    prompt = """
Analyze the current screen as a coding assistant.

Extract only the visible source code and coding-related error messages.

Do not explain the code yet.

Include:
- visible code
- visible error text
- relevant terminal output

If code is not visible, clearly say:
NO_CODE_VISIBLE
"""

    try:

        result = analyze_screen(
            prompt
        )

        if not result:

            return {
                "success": False,
                "content": "",
                "message": (
                    "I couldn't read coding content "
                    "from the screen."
                )
            }

        if "NO_CODE_VISIBLE" in result.upper():

            return {
                "success": False,
                "content": "",
                "message": (
                    "I couldn't find visible code "
                    "on the screen."
                )
            }

        return {
            "success": True,
            "content": result,
            "message": (
                "Visible coding context captured."
            )
        }

    except Exception as error:

        print(
            f"Screen code extraction error: {error}"
        )

        return {
            "success": False,
            "content": "",
            "message": (
                "I couldn't analyze the coding screen."
            )
        }


def explain_code(
    code,
    language="Unknown"
):

    if not code:
        return "There is no code to explain."

    prompt = f"""
You are VEGA Coding Assistant.

Programming language:
{language}

Explain the following code clearly.

Focus on:

1. What the code does
2. Main execution flow
3. Important functions/classes
4. Important variables
5. Any notable implementation details

Keep the explanation practical and developer-friendly.

Code:

{code}
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

        return (
            response["message"]["content"]
            .strip()
        )

    except Exception as error:

        print(
            f"Code explanation error: {error}"
        )

        return (
            "I couldn't explain the code."
        )


def analyze_code_for_issues(
    code,
    language="Unknown",
    error_message=""
):

    if not code:
        return "There is no code to analyze."

    error_context = ""

    if error_message:

        error_context = f"""
Reported error:

{error_message}
"""

    prompt = f"""
You are VEGA Coding Assistant.

Programming language:
{language}

Analyze the code for real technical issues.

{error_context}

Check for:

- syntax errors
- runtime errors
- incorrect function calls
- undefined variables
- import problems
- logic bugs
- indentation problems
- wrong argument usage
- type issues
- resource handling issues

Rules:

- Do not invent problems.
- Separate confirmed problems from possible problems.
- If an error message is provided, connect it directly to the relevant code.
- Mention the likely location when possible.
- Give practical fixes.

Code:

{code}
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

        return (
            response["message"]["content"]
            .strip()
        )

    except Exception as error:

        print(
            f"Code analysis error: {error}"
        )

        return (
            "I couldn't analyze the code."
        )


def explain_error(
    error_message,
    code="",
    language="Unknown"
):

    if not error_message:
        return "No error message was provided."

    prompt = f"""
You are VEGA Coding Assistant.

Programming language:
{language}

Explain this programming error.

Error:

{error_message}

Relevant code:

{code}

Explain:

1. What the error means
2. Most likely cause
3. Where the issue probably is
4. How to fix it
5. What to check if the first fix does not work

Do not invent details that are not supported by the error or code.
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

        return (
            response["message"]["content"]
            .strip()
        )

    except Exception as error:

        print(
            f"Error explanation failure: {error}"
        )

        return (
            "I couldn't analyze that error."
        )


def understand_file(
    path,
    mode="explain"
):

    file_data = get_code_from_file(
        path
    )

    if not file_data["success"]:

        return file_data["message"]

    code = file_data["code"]
    language = file_data["language"]

    if mode == "issues":

        return analyze_code_for_issues(
            code,
            language
        )

    return explain_code(
        code,
        language
    )


def understand_screen(
    mode="explain"
):

    screen_data = get_code_from_screen()

    if not screen_data["success"]:

        return screen_data["message"]

    content = screen_data["content"]

    language = detect_language_from_code(
        content
    )

    if mode == "issues":

        return analyze_code_for_issues(
            content,
            language
        )

    return explain_code(
        content,
        language
    )