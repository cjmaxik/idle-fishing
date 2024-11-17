from PIL import ImageGrab
import cv2
import numpy as np
import win32gui
import win32api
import win32con
import time

# Constants
DEBUG = False
THRESHOLD = 0.9
TEMPLATE_FOLDER = "./patterns/%s.png"
WINDOW_NAME = "HoloCure"
ACTIVE_AREA = (740, 510, 840, 560)
KEY_TO_PATTERN = {
    "up": 0x57,
    "down": 0x53,
    "center": 0x20,
    "left": 0x41,
    "right": 0x44,
    "window": 0x0D,
}

# Variable to cache bounding boxes
bbox_cache = {}


def generate_patterns() -> list:
    """
    Generates a list of patterns for template matching.

    The function reads monochrome images from the template folder for each key in `KEY_TO_PATTERN`.
    Each pattern is read using OpenCV's `cv2.imread`, with the monochrome flag, and adds
    an extra dimension to the image to match the expected input format for template matching.

    Returns:
        A list of tuples where each tuple contains a key and the
        corresponding pattern image as a numpy array.
    """
    return [
        (i, cv2.imread(TEMPLATE_FOLDER % i, cv2.IMREAD_GRAYSCALE))
        for i in KEY_TO_PATTERN.keys()
    ]


def get_bbox(rect: tuple[int, int, int, int]) -> tuple:
    """
    Gets the bounding box of the active area of the window specified by the `rect` parameter.
    The bounding box is the area of the window that is used to detect the patterns.
    The function caches the bounding box for a given window position to avoid recalculating it multiple times.

    Args:
        rect: A tuple of four integers representing the top-left and bottom-right coordinates of the window.

    Returns:
        A tuple of four integers representing the top-left and bottom-right coordinates of the bounding box.
    """
    key = tuple(rect)
    if key in bbox_cache:
        return bbox_cache[key]

    result = (
        rect[0] + ACTIVE_AREA[0],
        rect[1] + ACTIVE_AREA[1],
        rect[0] + ACTIVE_AREA[0] + (ACTIVE_AREA[2] - ACTIVE_AREA[0]),
        rect[1] + ACTIVE_AREA[1] + (ACTIVE_AREA[3] - ACTIVE_AREA[1]),
    )

    print("New bbox:", result)
    bbox_cache[key] = result
    return result


def grab_frame(hwnd: int) -> np.ndarray | None:
    """
    Grabs a frame from the HoloCure window specified by the handle `hwnd`.
    If the window specified by `hwnd` does not exist, returns `None`.
    The frame is taken from the active area of the screen, which is obtained by calling `get_bbox` with the window's rectangle.
    The frame is then converted to grayscale and thresholded to make the dark areas black and the light areas white.
    If `DEBUG` is `True`, the frame is also displayed on the screen.

    Returns:
        The frame as a numpy array.
    """
    if not win32gui.IsWindow(hwnd):
        return None

    bbox = get_bbox(win32gui.GetWindowRect(hwnd))

    img = ImageGrab.grab(bbox, all_screens=True).convert("L")
    img = np.array(img)
    img[img <= 248] = 0

    # debug: show imagegrab result
    if DEBUG:
        cv2.imshow("Main Image", img)
        cv2.waitKey(1)
    return img


def press_key(hwnd: int, key: str) -> None:
    """
    Simulates a key press event on the window specified by `hwnd`.

    Args:
        hwnd (int): Handle to the window where the key press should be simulated.
        key (str): The key to be pressed, mapped from `KEY_TO_PATTERN`.

    If the `key` is "window", sends the key press twice with a short delay between.
    """
    input = KEY_TO_PATTERN.get(key)

    if key == "window":
        # Send Space two times
        win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, input, 0)
        time.sleep(0.05)
        win32api.PostMessage(hwnd, win32con.WM_KEYUP, input, 0)

        time.sleep(0.5)

        win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, input, 0)
        time.sleep(0.05)
        win32api.PostMessage(hwnd, win32con.WM_KEYUP, input, 0)
    else:
        win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, input, 0)
        time.sleep(0.05)
        win32api.PostMessage(hwnd, win32con.WM_KEYUP, input, 0)


def main():
    """
    The main entry point of the script.

    Performs the following tasks:

    1. Generates a list of patterns using `generate_patterns`.
    2. Finds the HoloCure window and sets it as the foreground.
    3. Sends an escape key event as a test.
    4. Grabs the screen and performs template matching on it using `grab_frame` and `cv2.matchTemplate`.
    5. If a match is found, sends the corresponding key event using `press_key`.
    6. Repeats steps 4-5 indefinitely.
    """
    patterns = generate_patterns()

    hwnd = win32gui.FindWindow(None, "HoloCure")
    if not hwnd:
        print("HoloCure window not found")
        return
    win32gui.SetForegroundWindow(hwnd)

    # Send escape key as a test
    win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_ESCAPE, 0)
    time.sleep(0.05)
    win32api.PostMessage(hwnd, win32con.WM_KEYUP, win32con.VK_ESCAPE, 0)

    while True:
        sc = grab_frame(hwnd)
        if sc is None:
            print("HoloCure window not found")
            return

        # Skip if the screen is blank
        if sc.sum() == 0:
            continue

        # Perform template matching
        for key, pattern in patterns:
            res = cv2.matchTemplate(sc, pattern, cv2.TM_CCORR_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(res)

            if max_val < THRESHOLD:
                continue

            if DEBUG:
                print("found '%s'" % key)

            press_key(hwnd, key)
            break


if __name__ == "__main__":
    main()
