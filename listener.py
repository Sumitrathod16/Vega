import speech_recognition as sr
import threading

from brain import (
    ask_vega,
    ask_vega_with_web,
    should_use_web
)

from speaker import (
    speak,
    stop_voice,
    shutdown_audio
)

from apps import open_application

from system_control import (
    volume_up,
    volume_down,
    mute,
    unmute,
    set_volume,
    get_volume
)

from web_search import search_web
from screen_reader import analyze_screen


recognizer = sr.Recognizer()
interrupt_listener_stop = threading.Event()


# Listening
def listen(timeout=10, phrase_time_limit=15):

    try:

        with sr.Microphone() as source:

            print("\nListening...")

            recognizer.adjust_for_ambient_noise(
                source,
                duration=0.3
            )

            audio = recognizer.listen(
                source,
                timeout=timeout,
                phrase_time_limit=phrase_time_limit
            )

            print("Processing voice...")

            text = recognizer.recognize_google(
                audio
            )

            return text.lower().strip()

    except sr.WaitTimeoutError:
        return None

    except sr.UnknownValueError:

        print("Couldn't understand.")
        return None

    except sr.RequestError as error:

        print(
            f"Speech recognition error: {error}"
        )

        return None

    except OSError as error:

        print(
            f"Microphone error: {error}"
        )

        print(
            "Retrying microphone..."
        )

        return None

    except Exception as error:

        print(
            f"Unexpected microphone error: {error}"
        )

        return None


# Voice Interruption
def listen_for_interruption():

    interrupt_phrases = [
        "stop",
        "stop vega",
        "vega stop",
        "pause",
        "pause vega",
        "wait",
        "wait vega",
        "hold on",
        "hold on vega",
        "stop talking",
        "pause talking",
        "wait a moment",
        "hold on a second",
        "enough"
    ]

    while not interrupt_listener_stop.is_set():

        command = listen(
            timeout=1,
            phrase_time_limit=2
        )

        if interrupt_listener_stop.is_set():
            return

        if not command:
            continue

        print(
            f"Interrupt listener heard: {command}"
        )

        if any(
            phrase in command
            for phrase in interrupt_phrases
        ):

            print(
                "\nVEGA speech interrupted."
            )

            stop_voice()

            interrupt_listener_stop.set()

            return


# Interruptible Speech
def speak_with_interrupt(text):

    interrupt_listener_stop.clear()

    speech_thread = threading.Thread(
        target=speak,
        args=(text,)
    )

    interrupt_thread = threading.Thread(
        target=listen_for_interruption
    )

    speech_thread.start()
    interrupt_thread.start()

    speech_thread.join()

    interrupt_listener_stop.set()

    interrupt_thread.join(
        timeout=3
    )

    print(
        "\nVEGA ready for next command."
    )


# Wake Word
def wait_for_wake_word():

    print(
        "\nVEGA sleeping..."
    )

    print(
        "Say 'Hey VEGA' to wake me."
    )

    wake_words = [
        "hey vega",
        "hello vega",
        "ok vega",
        "okay vega",
        "vega"
    ]

    while True:

        text = listen(
            timeout=5,
            phrase_time_limit=4
        )

        if not text:
            continue

        print(
            f"Heard: {text}"
        )

        if any(
            wake_word in text
            for wake_word in wake_words
        ):

            print(
                "VEGA activated."
            )

            return


# Sleep Commands
def should_sleep(command):

    sleep_phrases = [
        "go to sleep",
        "go back to sleep",
        "sleep vega",
        "vega go to sleep",
        "you can sleep",
        "take a rest"
    ]

    return any(
        phrase in command
        for phrase in sleep_phrases
    )


# Shutdown Commands
def should_shutdown(command):

    shutdown_phrases = [
        "shutdown vega",
        "shut down vega",
        "exit vega",
        "quit vega",
        "stop vega completely",
        "terminate vega"
    ]

    return any(
        phrase in command
        for phrase in shutdown_phrases
    )


# Search Query
def extract_search_query(command):

    command = command.lower().strip()

    command = command.replace(
        "vega",
        ""
    ).strip()

    search_phrases = [
        "search the web for",
        "search internet for",
        "search the internet for",
        "search web for",
        "search for",
        "look up",
        "find online",
        "google"
    ]

    for phrase in search_phrases:

        if phrase in command:

            query = command.replace(
                phrase,
                "",
                1
            ).strip()

            if query:
                return query

    return None


# App Name
def extract_app_name(command):

    command = command.lower().strip()

    command = command.replace(
        "vega",
        ""
    ).strip()

    if command.startswith(
        "open "
    ):

        return command.replace(
            "open ",
            "",
            1
        ).strip()

    return None


# Screen Command
def is_screen_command(command):

    screen_phrases = [
        "what is on my screen",
        "what's on my screen",
        "what do you see",
        "what can you see",
        "read my screen",
        "look at my screen",
        "check my screen",
        "analyze my screen",
        "analyse my screen",
        "describe my screen",
        "explain my screen"
    ]

    return any(
        phrase in command
        for phrase in screen_phrases
    )


# Number Extraction
def extract_number(command):

    command = command.replace(
        "%",
        " "
    )

    words = command.split()

    for word in words:

        if word.isdigit():
            return int(word)

    return None


# Volume Level
def extract_volume_level(command):

    level = extract_number(
        command
    )

    if level is None:
        return None

    if 0 <= level <= 100:
        return level

    return None


# Conversation Mode
def conversation_mode():

    speak(
        "Yes boss?"
    )

    print(
        "\nVEGA ACTIVE"
    )

    print(
        "You can now talk normally."
    )

    while True:

        command = listen(
            timeout=15,
            phrase_time_limit=20
        )

        if not command:
            continue

        print(
            f"\nYou: {command}"
        )

        # Shutdown
        if should_shutdown(
            command
        ):

            speak(
                "Alright boss. "
                "Shutting down VEGA. "
                "See you later."
            )

            return "shutdown"

        # Sleep
        if should_sleep(
            command
        ):

            speak(
                "Alright boss. "
                "I'll go to sleep. "
                "Just call me when you need me."
            )

            return "sleep"

        # Set Volume
        if (
            "set volume to" in command
            or
            "set the volume to" in command
        ):

            try:

                level = extract_volume_level(
                    command
                )

                if level is None:

                    speak(
                        "Boss, tell me a volume level "
                        "between zero and one hundred."
                    )

                else:

                    message = set_volume(
                        level
                    )

                    speak(
                        message
                    )

            except Exception as error:

                print(
                    f"Volume Error: {error}"
                )

                speak(
                    "Sorry boss. "
                    "I couldn't change the volume."
                )

            continue

        # Volume Up
        if any(
            phrase in command
            for phrase in [
                "volume up",
                "increase volume",
                "increase the volume",
                "raise volume",
                "raise the volume",
                "turn volume up",
                "turn the volume up"
            ]
        ):

            try:

                amount = extract_number(
                    command
                )

                if amount is None:
                    amount = 10

                message = volume_up(
                    amount
                )

                speak(
                    message
                )

            except Exception as error:

                print(
                    f"Volume Error: {error}"
                )

                speak(
                    "Sorry boss. "
                    "I couldn't increase the volume."
                )

            continue

        # Volume Down
        if any(
            phrase in command
            for phrase in [
                "volume down",
                "decrease volume",
                "decrease the volume",
                "lower volume",
                "lower the volume",
                "turn volume down",
                "turn the volume down"
            ]
        ):

            try:

                amount = extract_number(
                    command
                )

                if amount is None:
                    amount = 10

                message = volume_down(
                    amount
                )

                speak(
                    message
                )

            except Exception as error:

                print(
                    f"Volume Error: {error}"
                )

                speak(
                    "Sorry boss. "
                    "I couldn't decrease the volume."
                )

            continue

        # Unmute
        if any(
            phrase in command
            for phrase in [
                "unmute",
                "unmute volume",
                "unmute the volume",
                "turn sound on",
                "turn the sound on"
            ]
        ):

            try:

                speak(
                    unmute()
                )

            except Exception as error:

                print(
                    f"Volume Error: {error}"
                )

            continue

        # Mute
        if any(
            phrase in command
            for phrase in [
                "mute",
                "mute volume",
                "mute the volume",
                "turn sound off",
                "turn the sound off"
            ]
        ):

            try:

                speak(
                    mute()
                )

            except Exception as error:

                print(
                    f"Volume Error: {error}"
                )

            continue

        # Current Volume
        if any(
            phrase in command
            for phrase in [
                "current volume",
                "what is the volume",
                "what's the volume",
                "volume level",
                "what is my volume",
                "what's my volume"
            ]
        ):

            try:

                level = get_volume()

                speak(
                    f"Current volume is "
                    f"{level} percent."
                )

            except Exception as error:

                print(
                    f"Volume Error: {error}"
                )

            continue

        # Manual Web Search
        search_query = extract_search_query(
            command
        )

        if search_query:

            try:

                speak(
                    "Sure boss. "
                    "Let me check the web."
                )

                search_results = search_web(
                    search_query
                )

                if not search_results:

                    speak(
                        "Sorry boss. "
                        "I couldn't find useful results."
                    )

                    continue

                print(
                    "VEGA is analyzing web results..."
                )

                response = ask_vega_with_web(
                    command,
                    search_results
                )

                speak_with_interrupt(
                    response
                )

            except Exception as error:

                print(
                    f"Web Search Error: {error}"
                )

                speak(
                    "Sorry boss. "
                    "I couldn't process the web search."
                )

            continue

        # Application Control
        app_name = extract_app_name(
            command
        )

        if app_name:

            try:

                success, message = open_application(
                    app_name
                )

                speak(
                    message
                )

            except Exception as error:

                print(
                    f"App Error: {error}"
                )

                speak(
                    "Sorry boss. "
                    "I couldn't open that application."
                )

            continue

        # Screen Awareness
        if is_screen_command(
            command
        ):

            try:

                speak(
                    "Let me take a look."
                )

                print(
                    "VEGA is analyzing the screen..."
                )

                response = analyze_screen(
                    command
                )

                speak_with_interrupt(
                    response
                )

            except Exception as error:

                print(
                    f"Screen Analysis Error: {error}"
                )

                speak(
                    "Sorry boss. "
                    "I couldn't analyze the screen."
                )

            continue

        # Automatic Web Detection
        try:

            use_web = should_use_web(
                command
            )

            if use_web:

                print(
                    "VEGA detected that current information is required."
                )

                speak(
                    "Let me check the latest information."
                )

                search_results = search_web(
                    command
                )

                if search_results:

                    response = ask_vega_with_web(
                        command,
                        search_results
                    )

                    speak_with_interrupt(
                        response
                    )

                else:

                    speak(
                        "I couldn't find reliable current information."
                    )

                continue

        except Exception as error:

            print(
                f"Automatic web detection error: {error}"
            )

        # AI Conversation
        try:

            print(
                "VEGA is thinking..."
            )

            response = ask_vega(
                command
            )

            speak_with_interrupt(
                response
            )

            print(
                "\nVEGA is still active..."
            )

        except Exception as error:

            print(
                f"\nVEGA Error: {error}"
            )

            speak(
                "Sorry boss. "
                "I ran into a problem while processing that."
            )


# Main System
def main():

    print(
        "\n================================"
    )

    print(
        "           VEGA SYSTEM"
    )

    print(
        "================================"
    )

    print(
        "\nAI Brain: Ollama"
    )

    print(
        "Voice Recognition: Ready"
    )

    print(
        "Voice Output: Ready"
    )

    print(
        "Application Control: Ready"
    )

    print(
        "Volume Control: Ready"
    )

    print(
        "Web Search: Ready"
    )

    print(
        "Screen Awareness: Ready"
    )

    print(
        "Automatic Web Detection: Ready"
    )

    print(
        "Voice Interruption: Ready"
    )

    print(
        "\nVEGA online."
    )

    try:

        while True:

            wait_for_wake_word()

            result = conversation_mode()

            if result == "shutdown":
                break

    except KeyboardInterrupt:

        print(
            "\n\nVEGA manually stopped."
        )

    finally:

        interrupt_listener_stop.set()

        stop_voice()

        shutdown_audio()

        print(
            "\nVEGA OFFLINE"
        )


# Startup
if __name__ == "__main__":

    main()