import os
import shutil
import subprocess
import sys
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


def generate_code(
    request,
    language="Unknown",
    framework=""
):
    if not request:
        return "Please tell me what code you want."

    framework_context = ""

    if framework:
        framework_context = f"""
Framework / technology:
{framework}
"""

    prompt = f"""
You are VEGA Coding Assistant.

Generate production-quality code for the user's request.

Requested language:
{language}

{framework_context}

User request:
{request}

Rules:

- Return complete usable code.
- Do not omit important parts.
- Use clean structure and readable names.
- Avoid unnecessary comments.
- Follow modern best practices.
- If requirements are ambiguous, make sensible defaults.
- Do not wrap the code in excessive explanation.

After the code, give a short explanation of what it does.
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

        return response["message"]["content"].strip()

    except Exception as error:
        print(f"Code generation error: {error}")
        return "I couldn't generate the code."


def refactor_code(
    code,
    language="Unknown",
    instruction="Improve this code."
):
    if not code:
        return "There is no code to refactor."

    prompt = f"""
You are VEGA Coding Assistant.

Programming language:
{language}

Refactor the provided code according to the user's instruction.

Instruction:
{instruction}

Requirements:

- Preserve intended behavior unless the instruction asks for a behavior change.
- Fix obvious bugs when safe.
- Improve readability.
- Improve structure.
- Remove unnecessary duplication.
- Use appropriate naming.
- Keep the implementation practical.
- Return the COMPLETE corrected/refactored code.
- Do not return only snippets or diffs.

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

        return response["message"]["content"].strip()

    except Exception as error:
        print(f"Code refactor error: {error}")
        return "I couldn't refactor the code."


def convert_code(
    code,
    source_language="Unknown",
    target_language="Unknown"
):
    if not code:
        return "There is no code to convert."

    prompt = f"""
You are VEGA Coding Assistant.

Convert this code from:
{source_language}

to:
{target_language}

Rules:

- Preserve functionality.
- Use idiomatic patterns of the target language.
- Return complete usable code.
- Do not omit required imports or setup.
- Avoid unnecessary explanation.

Source code:

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

        return response["message"]["content"].strip()

    except Exception as error:
        print(f"Code conversion error: {error}")
        return "I couldn't convert the code."


def refactor_file(
    path,
    instruction="Improve this code."
):
    file_data = get_code_from_file(path)

    if not file_data["success"]:
        return file_data["message"]

    return refactor_code(
        file_data["code"],
        file_data["language"],
        instruction
    )


def refactor_screen(
    instruction="Improve this code."
):
    screen_data = get_code_from_screen()

    if not screen_data["success"]:
        return screen_data["message"]

    content = screen_data["content"]
    language = detect_language_from_code(content)

    return refactor_code(
        content,
        language,
        instruction
    )

# ============================================================
# Phase 3 - Safe File Editing
# ============================================================

import ast
import hashlib
import shutil
import tempfile
from datetime import datetime


EDITABLE_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".cpp", ".c",
    ".cs", ".php", ".html", ".css", ".json", ".sql", ".go", ".rs",
    ".kt", ".swift", ".sh", ".ps1", ".md", ".xml", ".yaml", ".yml"
}

MAX_EDIT_CHARACTERS = 60000


def _resolve_existing_code_path(path):
    try:
        target = Path(path).expanduser()

        if not target.is_absolute():
            target = (Path.cwd() / target).resolve()
        else:
            target = target.resolve()

        if not target.exists():
            return None, f"File does not exist: {target}"

        if not target.is_file():
            return None, f"That path is not a file: {target}"

        if target.suffix.lower() not in EDITABLE_EXTENSIONS:
            return None, (
                f"VEGA safe editing does not support {target.suffix or 'this file type'} yet."
            )

        return target, ""

    except Exception as error:
        return None, f"Invalid file path: {error}"


def read_complete_code_file(path):
    target, error = _resolve_existing_code_path(path)

    if not target:
        return {
            "success": False,
            "path": "",
            "code": "",
            "language": "Unknown",
            "message": error
        }

    try:
        code = target.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            code = target.read_text(encoding="utf-8-sig")
        except Exception as read_error:
            return {
                "success": False,
                "path": str(target),
                "code": "",
                "language": "Unknown",
                "message": f"I couldn't read the file: {read_error}"
            }
    except Exception as read_error:
        return {
            "success": False,
            "path": str(target),
            "code": "",
            "language": "Unknown",
            "message": f"I couldn't read the file: {read_error}"
        }

    if not code.strip():
        return {
            "success": False,
            "path": str(target),
            "code": "",
            "language": detect_language_from_path(str(target)),
            "message": "The file is empty, so I won't overwrite it automatically."
        }

    if len(code) > MAX_EDIT_CHARACTERS:
        return {
            "success": False,
            "path": str(target),
            "code": "",
            "language": detect_language_from_path(str(target)),
            "message": (
                f"The file is too large for safe automatic editing "
                f"({len(code)} characters)."
            )
        }

    return {
        "success": True,
        "path": str(target),
        "code": code,
        "language": detect_language_from_path(str(target)),
        "message": "File loaded for safe editing."
    }


def _extract_code_payload(model_output):
    if not model_output:
        return ""

    text = model_output.strip()

    start_marker = "BEGIN_CODE"
    end_marker = "END_CODE"

    start = text.find(start_marker)
    end = text.rfind(end_marker)

    if start != -1 and end != -1 and end > start:
        text = text[start + len(start_marker):end].strip()

    if text.startswith("```"):
        lines = text.splitlines()

        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        text = "\n".join(lines).strip()

    return text


def generate_file_edit(code, language, instruction, file_path=""):
    if not code:
        return {
            "success": False,
            "code": "",
            "message": "There is no source code to edit."
        }

    prompt = f"""
You are VEGA Coding Assistant operating in SAFE FILE EDITING mode.

File:
{file_path}

Programming language:
{language}

Requested change:
{instruction}

Rules:
- Return the COMPLETE updated file, not a diff and not a partial snippet.
- Preserve working behavior unless the requested change requires otherwise.
- Do not remove unrelated features.
- Do not omit imports, functions, classes, configuration, or existing logic unnecessarily.
- Fix obvious syntax problems that are directly related to the requested change.
- Never include Markdown fences inside the code payload.
- Do not include explanation inside the code payload.
- Output exactly this structure:

BEGIN_CODE
<complete updated file contents>
END_CODE

Original file:

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

        raw_output = response["message"]["content"].strip()
        updated_code = _extract_code_payload(raw_output)

        if not updated_code:
            return {
                "success": False,
                "code": "",
                "message": "The model returned an empty edit, so the file was not changed."
            }

        if updated_code.strip() == code.strip():
            return {
                "success": False,
                "code": "",
                "message": "The generated version did not contain any changes."
            }

        return {
            "success": True,
            "code": updated_code,
            "message": "Updated code generated successfully."
        }

    except Exception as error:
        print(f"Safe edit generation error: {error}")

        return {
            "success": False,
            "code": "",
            "message": f"I couldn't generate the file update: {error}"
        }


def validate_edited_code(path, code):
    if not code or not code.strip():
        return False, "Generated code is empty."

    extension = Path(path).suffix.lower()

    if extension == ".py":
        try:
            ast.parse(code, filename=str(path))
        except SyntaxError as error:
            line = error.lineno or "unknown"
            return False, (
                f"Generated Python code has a syntax error near line {line}: "
                f"{error.msg}"
            )

    if extension == ".json":
        try:
            json.loads(code)
        except json.JSONDecodeError as error:
            return False, (
                f"Generated JSON is invalid near line {error.lineno}: {error.msg}"
            )

    return True, "Generated code passed pre-write validation."


def create_code_backup(path):
    target, error = _resolve_existing_code_path(path)

    if not target:
        return {
            "success": False,
            "backup_path": "",
            "message": error
        }

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = target.with_name(
        f"{target.name}.vega_backup_{timestamp}"
    )

    try:
        shutil.copy2(target, backup_path)

        return {
            "success": True,
            "backup_path": str(backup_path),
            "message": f"Backup created: {backup_path.name}"
        }

    except Exception as error:
        return {
            "success": False,
            "backup_path": "",
            "message": f"Backup failed: {error}"
        }


def _sha256_text(text):
    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()


def write_code_file_safely(path, updated_code):
    target, error = _resolve_existing_code_path(path)

    if not target:
        return {
            "success": False,
            "message": error
        }

    temp_path = None

    try:
        fd, temp_name = tempfile.mkstemp(
            prefix=f".{target.name}.vega_",
            suffix=".tmp",
            dir=str(target.parent)
        )

        temp_path = Path(temp_name)

        with os.fdopen(fd, "w", encoding="utf-8", newline="") as temp_file:
            temp_file.write(updated_code)
            temp_file.flush()
            os.fsync(temp_file.fileno())

        written_content = temp_path.read_text(encoding="utf-8")

        if _sha256_text(written_content) != _sha256_text(updated_code):
            return {
                "success": False,
                "message": "Temporary-file verification failed. Original file was not changed."
            }

        os.replace(temp_path, target)
        temp_path = None

        final_content = target.read_text(encoding="utf-8")

        if _sha256_text(final_content) != _sha256_text(updated_code):
            return {
                "success": False,
                "message": "The saved file could not be verified."
            }

        return {
            "success": True,
            "message": f"Updated and verified: {target}"
        }

    except Exception as error:
        return {
            "success": False,
            "message": f"I couldn't save the edited file: {error}"
        }

    finally:
        if temp_path and temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass


def safe_edit_file(path, instruction="Improve and fix this code."):
    file_data = read_complete_code_file(path)

    if not file_data["success"]:
        return {
            "success": False,
            "path": file_data.get("path", str(path)),
            "backup_path": "",
            "message": file_data["message"]
        }

    edit_result = generate_file_edit(
        file_data["code"],
        file_data["language"],
        instruction,
        file_data["path"]
    )

    if not edit_result["success"]:
        return {
            "success": False,
            "path": file_data["path"],
            "backup_path": "",
            "message": edit_result["message"]
        }

    valid, validation_message = validate_edited_code(
        file_data["path"],
        edit_result["code"]
    )

    if not valid:
        return {
            "success": False,
            "path": file_data["path"],
            "backup_path": "",
            "message": (
                f"I did not modify the original file. {validation_message}"
            )
        }

    backup_result = create_code_backup(
        file_data["path"]
    )

    if not backup_result["success"]:
        return {
            "success": False,
            "path": file_data["path"],
            "backup_path": "",
            "message": (
                "I refused to overwrite the file because a backup could not be created. "
                + backup_result["message"]
            )
        }

    write_result = write_code_file_safely(
        file_data["path"],
        edit_result["code"]
    )

    if not write_result["success"]:
        return {
            "success": False,
            "path": file_data["path"],
            "backup_path": backup_result["backup_path"],
            "message": write_result["message"]
        }

    return {
        "success": True,
        "path": file_data["path"],
        "backup_path": backup_result["backup_path"],
        "message": (
            "File updated successfully. "
            f"Backup: {backup_result['backup_path']}"
        )
    }


RUNNABLE_EXTENSIONS = {
    ".py",
    ".js",
    ".mjs",
    ".cjs",
    ".php",
    ".ps1",
    ".sh"
}


def _trim_process_output(text, limit=12000):
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[:limit] + "\n... output truncated ..."


def _resolve_run_command(path):
    target = Path(path).expanduser().resolve()
    extension = target.suffix.lower()

    if extension == ".py":
        return [sys.executable, str(target)]

    if extension in {".js", ".mjs", ".cjs"}:
        node = shutil.which("node")
        if not node:
            return None
        return [node, str(target)]

    if extension == ".php":
        php = shutil.which("php")
        if not php:
            return None
        return [php, str(target)]

    if extension == ".ps1":
        powershell = shutil.which("powershell") or shutil.which("pwsh")
        if not powershell:
            return None
        return [
            powershell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(target)
        ]

    if extension == ".sh":
        bash = shutil.which("bash")
        if not bash:
            return None
        return [bash, str(target)]

    return None


def check_code_file(path, timeout=15):
    target = Path(path).expanduser().resolve()

    if not target.exists() or not target.is_file():
        return {
            "success": False,
            "path": str(target),
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "message": "The code file does not exist."
        }

    extension = target.suffix.lower()

    if extension == ".py":
        command = [sys.executable, "-m", "py_compile", str(target)]
    elif extension in {".js", ".mjs", ".cjs"}:
        node = shutil.which("node")
        if not node:
            return {
                "success": False,
                "path": str(target),
                "returncode": None,
                "stdout": "",
                "stderr": "",
                "message": "Node.js is not available on this system."
            }
        command = [node, "--check", str(target)]
    elif extension == ".php":
        php = shutil.which("php")
        if not php:
            return {
                "success": False,
                "path": str(target),
                "returncode": None,
                "stdout": "",
                "stderr": "",
                "message": "PHP is not available on this system."
            }
        command = [php, "-l", str(target)]
    else:
        return {
            "success": False,
            "path": str(target),
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "message": (
                "Compile checking is currently supported for Python, "
                "JavaScript, and PHP files."
            )
        }

    try:
        process = subprocess.run(
            command,
            cwd=str(target.parent),
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
            timeout=timeout,
            shell=False
        )

        stdout = _trim_process_output(process.stdout)
        stderr = _trim_process_output(process.stderr)
        success = process.returncode == 0

        return {
            "success": success,
            "path": str(target),
            "returncode": process.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "message": (
                "Code check passed."
                if success
                else "Code check failed."
            )
        }

    except subprocess.TimeoutExpired as error:
        return {
            "success": False,
            "path": str(target),
            "returncode": None,
            "stdout": _trim_process_output(error.stdout),
            "stderr": _trim_process_output(error.stderr),
            "message": f"Code check timed out after {timeout} seconds."
        }
    except Exception as error:
        return {
            "success": False,
            "path": str(target),
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "message": f"I couldn't check the code: {error}"
        }


def run_code_file(path, timeout=20):
    target = Path(path).expanduser().resolve()

    if not target.exists() or not target.is_file():
        return {
            "success": False,
            "path": str(target),
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "message": "The code file does not exist."
        }

    command = _resolve_run_command(target)

    if not command:
        return {
            "success": False,
            "path": str(target),
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "message": (
                f"I can't run {target.suffix or 'this'} files yet, "
                "or the required runtime is not installed."
            )
        }

    try:
        process = subprocess.run(
            command,
            cwd=str(target.parent),
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
            timeout=timeout,
            shell=False
        )

        stdout = _trim_process_output(process.stdout)
        stderr = _trim_process_output(process.stderr)
        success = process.returncode == 0

        return {
            "success": success,
            "path": str(target),
            "returncode": process.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "message": (
                "Program completed successfully."
                if success
                else f"Program exited with code {process.returncode}."
            )
        }

    except subprocess.TimeoutExpired as error:
        return {
            "success": False,
            "path": str(target),
            "returncode": None,
            "stdout": _trim_process_output(error.stdout),
            "stderr": _trim_process_output(error.stderr),
            "message": f"Program timed out after {timeout} seconds."
        }
    except Exception as error:
        return {
            "success": False,
            "path": str(target),
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "message": f"I couldn't run the file: {error}"
        }


def debug_code_file(path, timeout=20, run_program=True):
    target = Path(path).expanduser().resolve()

    file_data = read_complete_code_file(target)
    if not file_data["success"]:
        return {
            "success": False,
            "path": str(target),
            "execution": None,
            "analysis": file_data["message"],
            "message": file_data["message"]
        }

    if run_program:
        execution = run_code_file(target, timeout=timeout)
    else:
        execution = check_code_file(target, timeout=timeout)

    combined_error = "\n".join(
        part
        for part in [
            execution.get("stderr", ""),
            execution.get("stdout", "") if not execution.get("success") else ""
        ]
        if part
    ).strip()

    if execution["success"]:
        output = execution.get("stdout", "").strip()
        analysis = (
            "The program completed successfully."
            + (f"\n\nOutput:\n{output}" if output else "")
        )
    else:
        diagnostic_input = combined_error or execution.get("message", "Execution failed.")
        analysis = explain_error(
            diagnostic_input,
            code=file_data["code"],
            language=file_data["language"]
        )

    return {
        "success": execution["success"],
        "path": str(target),
        "execution": execution,
        "analysis": analysis,
        "message": execution["message"]
    }


# ============================================================
# Phase 5 - Autonomous Coding Loop
# ============================================================

MAX_AUTONOMOUS_ATTEMPTS = 3


def autonomous_coding_loop(
    path,
    goal="Fix the file so it runs successfully while preserving intended behavior.",
    max_attempts=MAX_AUTONOMOUS_ATTEMPTS,
    timeout=20
):
    try:
        max_attempts = max(1, min(int(max_attempts), 5))
    except (TypeError, ValueError):
        max_attempts = MAX_AUTONOMOUS_ATTEMPTS

    original = read_complete_code_file(path)

    if not original["success"]:
        return {
            "success": False,
            "path": original.get("path", str(path)),
            "attempts": 0,
            "history": [],
            "backup_paths": [],
            "message": original["message"]
        }

    target_path = original["path"]
    original_code = original["code"]
    history = []
    backup_paths = []

    for attempt in range(1, max_attempts + 1):
        execution = run_code_file(
            target_path,
            timeout=timeout
        )

        history.append({
            "attempt": attempt,
            "stage": "run",
            "success": execution["success"],
            "message": execution["message"],
            "stdout": execution.get("stdout", ""),
            "stderr": execution.get("stderr", "")
        })

        if execution["success"]:
            return {
                "success": True,
                "path": target_path,
                "attempts": attempt,
                "history": history,
                "backup_paths": backup_paths,
                "stdout": execution.get("stdout", ""),
                "message": (
                    f"Autonomous coding completed successfully in {attempt} attempt"
                    f"{'s' if attempt != 1 else ''}."
                )
            }

        current_file = read_complete_code_file(target_path)

        if not current_file["success"]:
            break

        error_text = "\n".join(
            part
            for part in [
                execution.get("stderr", ""),
                execution.get("stdout", ""),
                execution.get("message", "")
            ]
            if part
        ).strip()

        diagnosis = explain_error(
            error_text,
            code=current_file["code"],
            language=current_file["language"]
        )

        history.append({
            "attempt": attempt,
            "stage": "diagnosis",
            "success": True,
            "message": diagnosis
        })

        edit_instruction = f"""
Goal:
{goal}

The latest execution failed.

Execution error:
{error_text}

Diagnosis:
{diagnosis}

Make the smallest safe correction needed to solve the failure.
Preserve unrelated behavior and existing features.
Return a complete working file.
""".strip()

        edit_result = safe_edit_file(
            target_path,
            edit_instruction
        )

        if edit_result.get("backup_path"):
            backup_paths.append(
                edit_result["backup_path"]
            )

        history.append({
            "attempt": attempt,
            "stage": "edit",
            "success": edit_result["success"],
            "message": edit_result["message"],
            "backup_path": edit_result.get("backup_path", "")
        })

        if not edit_result["success"]:
            return {
                "success": False,
                "path": target_path,
                "attempts": attempt,
                "history": history,
                "backup_paths": backup_paths,
                "message": (
                    "The autonomous coding loop stopped because VEGA could not "
                    f"apply a safe edit. {edit_result['message']}"
                )
            }

    final_execution = run_code_file(
        target_path,
        timeout=timeout
    )

    history.append({
        "attempt": max_attempts + 1,
        "stage": "final_run",
        "success": final_execution["success"],
        "message": final_execution["message"],
        "stdout": final_execution.get("stdout", ""),
        "stderr": final_execution.get("stderr", "")
    })

    if final_execution["success"]:
        return {
            "success": True,
            "path": target_path,
            "attempts": max_attempts,
            "history": history,
            "backup_paths": backup_paths,
            "stdout": final_execution.get("stdout", ""),
            "message": (
                "Autonomous coding completed successfully after the final verification run."
            )
        }

    restore_result = write_code_file_safely(
        target_path,
        original_code
    )

    restore_message = (
        "The original file was restored."
        if restore_result["success"]
        else "VEGA could not automatically restore the original file."
    )

    return {
        "success": False,
        "path": target_path,
        "attempts": max_attempts,
        "history": history,
        "backup_paths": backup_paths,
        "stderr": final_execution.get("stderr", ""),
        "message": (
            f"VEGA could not make the program pass after {max_attempts} repair attempts. "
            f"{restore_message}"
        )
    }
