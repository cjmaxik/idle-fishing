from PIL import ImageGrab
import cv2
import numpy as np
import win32gui, win32api, win32con
import time

DEBUG = False
threshold = 0.8

# HoloCure window
windowName = "HoloCure"
activeArea = (747, 480, 850, 570)
hwndMain = 0


def grab_frame(hwnd):
    if not win32gui.IsWindow(hwnd):
        return None

    img = ImageGrab.grab(
        bbox=win32gui.GetWindowRect(hwnd),
        all_screens=True,
    )

    # debug: show imagegrab result
    if DEBUG:
        cv2.imshow("Main Image", np.array(img))
        cv2.waitKey(1)

    return img.crop(activeArea)


def generate_patterns():
    patterns = []
    for i in ["up", "down", "center", "left", "right", "window"]:
        pattern = cv2.imread("./patterns/%s.png" % i, cv2.COLOR_RGB2GRAY)
        pattern, *_ = cv2.split(pattern)
        patterns.append((i, pattern))

    return patterns


def match_inputs(pattern):
    match pattern:
        case "up":
            return [0x57]
        case "down":
            return [0x53]
        case "center":
            return [0x20]
        case "left":
            return [0x41]
        case "right":
            return [0x44]
        case "window":
            return [0x0D, 0.5, 0x0D]
        case _:
            return None


def main():
    patterns = generate_patterns()

    hwndMain = win32gui.FindWindow(None, "HoloCure")
    if not hwndMain:
        print("HoloCure window not found")
        return
    win32gui.SetForegroundWindow(hwndMain)

    # Send escape key as a test
    win32api.PostMessage(hwndMain, win32con.WM_KEYDOWN, win32con.VK_ESCAPE, 0)
    time.sleep(0.05)
    win32api.PostMessage(hwndMain, win32con.WM_KEYUP, win32con.VK_ESCAPE, 0)

    while True:
        sc = grab_frame(hwndMain)
        if sc is None:
            print("HoloCure window not found")
            return

        # Convert to grayscale and threshold
        img = cv2.cvtColor(np.array(sc), cv2.COLOR_RGB2GRAY)
        _, img = cv2.threshold(img, 120, 255, cv2.THRESH_BINARY)

        # debug: show the resulted image
        if DEBUG:
            cv2.imshow("Result", img)
            cv2.waitKey(1)

        # Perform template matching
        for pattern in patterns:
            r = cv2.matchTemplate(img, pattern[1], cv2.TM_CCOEFF_NORMED)
            loc = np.where(r >= np.array(threshold))

            for pt in zip(*loc[::-1]):
                print("found '%s'" % pattern[0])

                inputs = match_inputs(pattern[0])
                if inputs is None:
                    continue

                for i in inputs:
                    if type(i) == float:
                        time.sleep(i)
                    else:
                        win32api.PostMessage(hwndMain, win32con.WM_KEYDOWN, i, 0)
                        time.sleep(0.05)
                        win32api.PostMessage(hwndMain, win32con.WM_KEYUP, i, 0)

                break


if __name__ == "__main__":
    main()
