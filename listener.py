import speech_recognition as sr

from brain import ask_vega
from speaker import speak


recognizer = sr.Recognizer()


# =====================================
# LISTEN
# =====================================

def listen(
    timeout=10,
    phrase_time_limit=15
):

    with sr.Microphone() as source:

        print(
            "\nListening..."
        )

        try:

            recognizer.adjust_for_ambient_noise(
                source,
                duration=0.3
            )

            audio = recognizer.listen(
                source,
                timeout=timeout,
                phrase_time_limit=phrase_time_limit
            )

            print(
                "Processing voice..."
            )

            text = recognizer.recognize_google(
                audio
            )

            return text.lower().strip()

        except sr.WaitTimeoutError:

            return None

        except sr.UnknownValueError:

            print(
                "Couldn't understand."
            )

            return None

        except sr.RequestError as error:

            print(
                f"Speech recognition error: {error}"
            )

            return None


# =====================================
# WAKE WORD
# =====================================

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
            f"👂 Heard: {text}"
        )

        if any(
            wake_word in text
            for wake_word in wake_words
        ):

            print(
                "VEGA activated."
            )

            return


# =====================================
# COMMAND CHECKS
# =====================================

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


# =====================================
# ACTIVE CONVERSATION
# =====================================

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
            f"\n You: {command}"
        )

        # -----------------------------
        # SHUTDOWN JARVIS COMPLETELY
        # -----------------------------

        if should_shutdown(
            command
        ):

            speak(
                "Alright boss. "
                "Shutting down VEGA. "
                "See you later."
            )

            return "shutdown"

        # -----------------------------
        # SLEEP
        # -----------------------------

        if should_sleep(
            command
        ):

            speak(
                "Alright boss. "
                "I'll go to sleep. "
                "Just call me when you need me."
            )

            return "sleep"

        # -----------------------------
        # SEND COMMAND TO AI
        # -----------------------------

        try:

            print(
                "VEGA is thinking..."
            )

            response = ask_vega(
                command
            )

            # Speak complete response
            speak(
                response
            )

            print(
                "\n Still active..."
            )

        except Exception as error:

            print(
                f"\nVEGA Error: {error}"
            )

            speak(
                "Sorry boss. "
                "I ran into a problem while processing that."
            )


# =====================================
# MAIN VEGA LOOP
# =====================================

def main():

    print(
        "\n=============================="
    )

    print(
        "        VEGA SYSTEM"
    )

    print(
        "=============================="
    )

    print(
        "\n AI Brain: Ollama"
    )

    print(
        " Voice recognition: Ready"
    )

    print(
        " Voice output: Ready"
    )

    print(
        "\nVEGA online."
    )

    try:

        while True:

            # First wait for wake word
            wait_for_wake_word()

            # Once awake, remain awake
            # until user explicitly says sleep
            result = conversation_mode()

            if result == "shutdown":

                print(
                    "\n VEGA OFFLINE"
                )

                break

            # If result == sleep,
            # while loop starts again
            # and waits for wake word


    except KeyboardInterrupt:

        print(
            "\n\n VEGA manually stopped."
        )


# =====================================
# START
# =====================================

if __name__ == "__main__":

    main()