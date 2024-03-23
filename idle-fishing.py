from PIL import ImageGrab
import cv2
import numpy as np
import win32gui, win32api, win32con
import time


DEBUG = False
THRESHOLD = 0.9
TEMPLATE_FOLDER = "./patterns/%s.png"
WINDOW_NAME = "HoloCure"
ACTIVE_AREA = (745, 510, 840, 560)
KEY_TO_PATTERN = {
    "up": 0x57,
    "down": 0x53,
    "center": 0x20,
    "left": 0x41,
    "right": 0x44,
    "window": 0x0D,
}


def generate_patterns() -> list:
    """
    Generates a list of patterns by reading grayscale images from the './patterns' directory.
    """

    return [
        (i, cv2.imread(TEMPLATE_FOLDER % i, cv2.IMREAD_GRAYSCALE)[..., None])
        for i in KEY_TO_PATTERN.keys()
    ]


def grab_frame(hwnd: int) -> np.ndarray | None:
    """
    Grabs a specific area from a window with `hwnd` handle.
    """
    if not win32gui.IsWindow(hwnd):
        return None

    x, y, _, _ = win32gui.GetWindowRect(hwnd)
    bbox = (
        x + ACTIVE_AREA[0],
        y + ACTIVE_AREA[1],
        x + ACTIVE_AREA[0] + (ACTIVE_AREA[2] - ACTIVE_AREA[0]),
        y + ACTIVE_AREA[1] + (ACTIVE_AREA[3] - ACTIVE_AREA[1]),
    )

    img = ImageGrab.grab(bbox, all_screens=True)
    img = np.array(img)[:, :, 2]
    img[img <= 248] = 0

    # debug: show imagegrab result
    if DEBUG:
        cv2.imshow("Main Image", img)
        cv2.waitKey(1)

    return img


def main():
    """
    Main function
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
            res = cv2.matchTemplate(sc, pattern, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(res)
            if max_val < THRESHOLD:
                continue

            if DEBUG:
                print("found '%s'" % key)

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

            break


if __name__ == "__main__":
    main()
