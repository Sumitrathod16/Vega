import os
import subprocess


APP_PATHS = {
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "notepad": r"C:\Windows\System32\notepad.exe",
    "calculator": r"C:\Windows\System32\calc.exe",
    "vscode": r"C:\Users\Sumit\AppData\Local\Programs\Microsoft VS Code\Code.exe",
}


def open_application(app_name):

    app_name = app_name.lower().strip()

    if app_name not in APP_PATHS:
        return False, f"I don't know where {app_name} is installed."

    app_path = APP_PATHS[app_name]

    try:

        if not os.path.exists(app_path):
            return False, f"I couldn't find {app_name} on this computer."

        subprocess.Popen([app_path])

        return True, f"Opening {app_name}."

    except Exception as error:
        return False, f"I couldn't open {app_name}. Error: {error}"


if __name__ == "__main__":

    success, message = open_application("notepad")

    print(message)