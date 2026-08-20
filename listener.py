import speech_recognition as sr

from brain import ask_vega      
from speaker import speak
from apps import open_application

from system_control import (
    volume_up,
    volume_down,
    mute,
    unmute,
    set_volume,
    get_volume
)


recognizer = sr.Recognizer()


# =====================================
# LISTEN
# =====================================

def listen(timeout=10, phrase_time_limit=15):

    with sr.Microphone() as source:

        print("\nListening...")

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

    print("\n😴 VEGA sleeping...")
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

        print(f"Heard: {text}")

        if any(
            wake_word in text
            for wake_word in wake_words
        ):
            print("VEGA activated.")
            return


# =====================================
# SLEEP
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
# SHUTDOWN
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
# APP NAME EXTRACTOR
# =====================================

def extract_app_name(command):

    command = command.lower().strip()

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
# VOLUME VALUE EXTRACTOR
# =====================================

def extract_volume_level(command):

    words = command.replace(
        "%",
        " "
    ).split()

    for word in words:

        if word.isdigit():

            level = int(word)

            if 0 <= level <= 100:
                return level

    return None

def extract_number(command):

    command = command.replace("%", " ")

    words = command.split()

    for word in words:

        if word.isdigit():
            return int(word)

    return None
# =====================================
# ACTIVE CONVERSATION
# =====================================

def conversation_mode():

    speak("Yes boss?")

    print("\nVEGA ACTIVE")
    print("You can now talk normally.")

    while True:

        command = listen(
            timeout=15,
            phrase_time_limit=20
        )

        if not command:
            continue

        print(f"\nYou: {command}")


        # =================================
        # FULL SHUTDOWN
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
        # SET VOLUME
        # =================================

        if (
            "set volume to" in command
            or "set the volume to" in command
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

                    speak(message)

            except Exception as error:

                print(
                    f"Volume Error: {error}"
                )

                speak(
                    "Sorry boss. "
                    "I couldn't change the volume."
                )

            continue


        # =================================
        # VOLUME UP
        # =================================

        if any(
            phrase in command
            for phrase in [
                "volume up",
                "increase volume",
                "increase the volume",
                "raise volume",
                "raise the volume"
            ]
        ):

            try:
                
                amount = extract_number(command)

                if amount is None:
                    amount = 10

                message = volume_up()

                speak(message)

            except Exception as error:

                print(
                    f"❌ Volume Error: {error}"
                )

                speak(
                    "Sorry boss. "
                    "I couldn't increase the volume."
                )

            continue


        # =================================
        # VOLUME DOWN
        # =================================

        if any(
            phrase in command
            for phrase in [
                "volume down",
                "decrease volume",
                "decrease the volume",
                "lower volume",
                "lower the volume"
            ]
        ):

            try:
                amount = extract_number(command)

                if amount is None:
                    amount = 10

                message = volume_down(amount)

                speak(message)

            except Exception as error:

                print(
                    f"❌ Volume Error: {error}"
                )

                speak(
                    "Sorry boss. "
                    "I couldn't decrease the volume."
                )

            continue


        # =================================
        # UNMUTE
        # IMPORTANT: Check before mute,
        # because "unmute" contains "mute"
        # =================================

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

                message = unmute()

                speak(message)

            except Exception as error:

                print(
                    f"❌ Volume Error: {error}"
                )

                speak(
                    "Sorry boss. "
                    "I couldn't unmute the volume."
                )

            continue


        # =================================
        # MUTE
        # =================================

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

                message = mute()

                speak(message)

            except Exception as error:

                print(
                    f"❌ Volume Error: {error}"
                )

                speak(
                    "Sorry boss. "
                    "I couldn't mute the volume."
                )

            continue


        # =================================
        # GET CURRENT VOLUME
        # =================================

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
                    f"Current volume is {level} percent."
                )

            except Exception as error:

                print(
                    f"❌ Volume Error: {error}"
                )

                speak(
                    "Sorry boss. "
                    "I couldn't read the current volume."
                )

            continue


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

                speak(message)

            except Exception as error:

                print(
                    f"❌ App Error: {error}"
                )

                speak(
                    "Sorry boss. "
                    "I couldn't open that application."
                )

            continue


        # =================================
        # NORMAL AI CONVERSATION
        # =================================

        try:

            print(
                "🧠 VEGA is thinking..."
            )

            response = ask_vega(
                command
            )

            speak(
                response
            )

            print(
                "\n🟢 VEGA is still active..."
            )

        except Exception as error:

            print(
                f"\n❌ VEGA Error: {error}"
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

    print("\n🧠 AI Brain: Ollama")
    print("🎤 Voice Recognition: Ready")
    print("🔊 Voice Output: Ready")
    print("💻 Application Control: Ready")
    print("🔉 Volume Control: Ready")

    print("\nVEGA online.")


    try:

        while True:

            wait_for_wake_word()

            result = conversation_mode()

            if result == "shutdown":

                print(
                    "\n🔴 VEGA OFFLINE"
                )

                break


    except KeyboardInterrupt:

        print(
            "\n\n🛑 VEGA manually stopped."
        )


# =====================================
# START
# =====================================

if __name__ == "__main__":

    main()