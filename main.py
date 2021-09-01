"""
Resources that I used for this code:
    * How to create ASCII banners (for the timer): https://www.devdungeon.com/content/create-ascii-art-text-banners-python
    * Writing colored text on console: https://towardsdatascience.com/prettify-your-terminal-text-with-termcolor-and-pyfiglet-880de83fda6b
    * Listening on keyboard inputs on seperate thread: https://stackoverflow.com/a/43106497
    * Finding the focused application (the app that runs at foreground):
        -> Windows: https://stackoverflow.com/questions/65362756/getting-process-name-of-focused-window-with-python/65363087
        -> Linux: https://stackoverflow.com/questions/10266281/obtain-active-window-using-python
"""


from pyfiglet import Figlet
from termcolor import colored
from pynput import keyboard
import os
import time
import sys
import threading

if os.name == "posix":
    import wnck
else:
    import win32gui
    import win32process


def active_window_process_name():
    try:
        pid = None
        # TODO: TEST IT ON LINUX OS
        if os.name == "posix":
            screen = wnck.screen_get_default()
            screen.force_update()
            window = screen.get_active_window()
            if window is not None:
                pid = window.get_pid()
        else:
            pid = win32process.GetWindowThreadProcessId(
                win32gui.GetForegroundWindow())
            pid = int(pid[-1])
        return pid
    except Exception as e:
        # Probably because user has a different os than Linux or Windows
        print(e)
        sys.exit()


os.system("color")
WIDTH = 150
FIG = Figlet(font="6x10", width=WIDTH, justify="center")
PID = active_window_process_name()

# Global variables
running = True
terminated = False
start = time.time()
end = start
duration = 0


def clear():
    if os.name == "posix":
        _ = os.system("clear")
    else:
        _ = os.system("cls")


def printTopBanner():
    title = "Utku's Chronometer"
    # Center the title and fill remaining places
    placeholder = "_" * ((WIDTH - len(title)) // 2 - 1) + " "

    print(colored(placeholder + title +
          placeholder[::-1], "red", None, ["bold"]))
    print("\n" * 2)


def getControls():
    controls = {"s": "start/stop", "r": "reset", "q": "quit"}

    # Print the bottom line
    bottom = colored("_" * WIDTH + '\n', "red", None, ["bold"])

    # For each control
    for key, value in controls.items():
        # Center the information and print the text in next line
        text = "{}: {}".format(key, value)
        placeholder = " " * ((WIDTH - len(text)) // 2)
        bottom += colored(placeholder + text +
                          placeholder[::-1] + '\n', "red", None, ["bold"])

    return bottom


def renderDuration(duration: int):
    # Duration -> time passed in ms
    times = []
    """
    Calculate how many hours, minutes, seconds has passed.
        1. hours = duration // (60 * 60 * 1000)
        2. duration -= hours * (60 * 60 * 1000)
        3. minutes = duration // (60 * 1000)
        4. duration -= minutes * (60 * 1000)
        5. seconds = duration // 1000
        6. duration -= seconds * 1000
        7. milliseconds = duration
    """
    for i, key in enumerate(["hours", "minutes", "seconds"]):
        factor = (60 ** (2-i)) * 1000
        t = duration // factor
        times.append("{:02d}".format(t))
        duration -= t * factor

    times.append("{:03d}".format(duration))
    return FIG.renderText(" : ".join(times))


"""
    Control logic:
        If stopped, dont update the end time and the duration (end-start)
        If started, move end to the current time and start to the (end-duration)
        If reset, move start to end and reset duration
"""


def detectKeyPress(key: keyboard.Key):
    global running, terminated, start, end, duration

    try:
        keystr = key.char
    except:
        keystr = key.name

    # Only detect commands when the app is running on foreground
    if active_window_process_name() != PID:
        return

    # Start/Stop
    if keystr == 's':
        if not running:
            end = time.time()
            start = end - (duration / 1000)

        running = not running

    # Reset
    if keystr == 'r':
        start = end
        duration = 0

    # Quit
    if keystr == "q":
        terminated = True
        return False


def timerThreadFunc():
    global running, terminated, start, end, duration

    d_text = colored(renderDuration(0), "green", None, ["bold"])
    bottom_message = getControls()

    printTopBanner()
    print(d_text)
    print(bottom_message)
    print("\033[{}A".format(len(bottom_message.split('\n')) + 1))

    while True:
        if terminated:
            break
        if running:
            end = time.time()
            duration = int((end - start) * 1000)

        d_text = colored(renderDuration(duration), "cyan", None, ["bold"])
        height = len(d_text.split("\n"))

        print(("\033[A" + "\033[K") * (height) + d_text)


if __name__ == "__main__":
    clear()
    os.system('mode con: cols=151 lines=22')

    listener = keyboard.Listener(on_press=detectKeyPress)
    listener.setDaemon(False)
    timer = threading.Thread(target=timerThreadFunc)

    listener.start()
    timer.start()

    listener.join()
    timer.join()

    clear()
