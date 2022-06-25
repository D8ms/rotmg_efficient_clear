from pynput.keyboard import Key, Listener
from pynput.mouse import Button, Listener as l


def on_press(key):
    print('{0} pressed'.format(
        key))


def on_release(key):
    print('{0} release'.format(
        key))
    if key == Key.esc:
        # Stop listener
        return False


def on_click(x, y, button, pressed):
    print(x, y, button, pressed)
    if button == Button.right:
        return False


with l(on_click=on_click) as L:
    # Collect events until released
    with Listener(
            on_press=on_press,
            on_release=on_release) as listener:
        listener.join()
        L.join()