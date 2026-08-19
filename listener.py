import speech_recognition as sr

from brain import ask_vega
from speaker import speak
from apps import open_application


recognizer = sr.Recognizer()


# =====================================
# LISTEN
# =====================================

def listen(
    timeout=10,
    phrase_time_limit=15
):

    with sr.Microphone() as source:

        print("\n Listening...")

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

            print("Processing voice...")

            text = recognizer.recognize_google(audio)

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


# =====================================
# WAKE WORD
# =====================================

def wait_for_wake_word():

    print("\n VEGA sleeping...")
    print("Say 'Hey VEGA' to wake me.")

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
                "⚡ VEGA activated."
            )

            return


# =====================================
# SLEEP COMMAND
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


# =====================================
# SHUTDOWN COMMAND
# =====================================

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
# APP NAME CLEANER
# =====================================

def extract_app_name(command):

    command = command.lower().strip()

    # Remove "vega" if user says:
    # "vega open chrome"

    command = command.replace(
        "vega",
        ""
    ).strip()

    if command.startswith("open "):

        return command.replace(
            "open ",
            "",
            1
        ).strip()

    return None


# =====================================
# ACTIVE CONVERSATION MODE
# =====================================

def conversation_mode():

    speak("Yes boss?")

    print("\n VEGA ACTIVE")
    print("You can now talk normally.")

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

        # =================================
        # SHUTDOWN VEGA COMPLETELY
        # =================================

        if should_shutdown(command):

            speak(
                "Alright boss. "
                "Shutting down VEGA. "
                "See you later."
            )

            return "shutdown"


        # =================================
        # GO TO SLEEP
        # =================================

        if should_sleep(command):

            speak(
                "Alright boss. "
                "I'll go to sleep. "
                "Just call me when you need me."
            )

            return "sleep"


        # =================================
        # OPEN APPLICATION
        # =================================

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
                    f" App Error: {error}"
                )

                speak(
                    "Sorry boss. "
                    "I couldn't open that application."
                )

            # IMPORTANT:
            # VEGA remains active after opening app

            continue


        # =================================
        # NORMAL AI CONVERSATION
        # =================================

        try:

            print(
                " VEGA is thinking..."
            )

            response = ask_vega(
                command
            )

            speak(
                response
            )

            print(
                "\n VEGA is still active..."
            )

        except Exception as error:

            print(
                f"\n VEGA Error: {error}"
            )

            speak(
                "Sorry boss. "
                "I ran into a problem while processing that."
            )


# =====================================
# MAIN
# =====================================

def main():

    print(
        "\n================================"
    )

    print(
        "          VEGA SYSTEM"
    )

    print(
        "================================"
    )

    print(
        "\n🧠 AI Brain: Ollama"
    )

    print(
        "🎤 Voice Recognition: Ready"
    )

    print(
        "🔊 Voice Output: Ready"
    )

    print(
        "💻 Application Control: Ready"
    )

    print(
        "\n VEGA online."
    )


    try:

        while True:

            # -------------------------
            # SLEEP MODE
            # -------------------------

            wait_for_wake_word()


            # -------------------------
            # ACTIVE MODE
            # -------------------------

            result = conversation_mode()


            # -------------------------
            # FULL SHUTDOWN
            # -------------------------

            if result == "shutdown":

                print(
                    "\n VEGA OFFLINE"
                )

                break


            # If result is "sleep",
            # loop starts again and waits
            # for "Hey VEGA"


    except KeyboardInterrupt:

        print(
            "\n\n VEGA manually stopped."
        )


# =====================================
# START PROGRAM
# =====================================

if __name__ == "__main__":

    main()