from pycaw.pycaw import AudioUtilities


def get_device():
    return AudioUtilities.GetSpeakers()


def get_volume_interface():
    device = get_device()
    return device.EndpointVolume


def get_volume():

    volume = get_volume_interface()

    current = volume.GetMasterVolumeLevelScalar()

    return round(current * 100)


def set_volume(level):

    volume = get_volume_interface()

    level = max(
        0,
        min(100, int(level))
    )

    volume.SetMasterVolumeLevelScalar(
        level / 100,
        None
    )

    return f"Volume set to {level} percent."


def volume_up(step=10):

    current = get_volume()

    return set_volume(min(100, current+step))


def volume_down(step=10):

    current = get_volume()

    return set_volume(max(0, current-step))


def mute():

    volume = get_volume_interface()

    volume.SetMute(
        1,
        None
    )

    return "Volume muted."


def unmute():

    volume = get_volume_interface()

    volume.SetMute(
        0,
        None
    )

    return "Volume unmuted."


def is_muted():

    volume = get_volume_interface()

    return bool(
        volume.GetMute()
    )


if __name__ == "__main__":

    try:

        print(
            f"Current volume: {get_volume()}%"
        )

        print(
            f"Muted: {is_muted()}"
        )

    except Exception as error:

        print(
            f"❌ Volume system error: {error}"
        )