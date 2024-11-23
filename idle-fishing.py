import time
import win32gui
import win32api
import win32con
import win32ui
import numpy
import cv2
from functools import cache

# Constants
DEBUG = False
THRESHOLD = 0.95
TEMPLATE_FOLDER = "./patterns/%s.png"
WINDOW_NAME = "HoloCure"
ACTIVE_AREA = (760, 510, 840, 560)
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
    Generates a list of patterns using the images in the folder specified by the
    `TEMPLATE_FOLDER` constant.

    Returns:
        A list of tuples, where each tuple contains a key from `KEY_TO_PATTERN` and
        the corresponding grayscale image loaded from the file specified by the
        `TEMPLATE_FOLDER` constant.
    """
    return [
        (i, cv2.imread(TEMPLATE_FOLDER % i, cv2.IMREAD_GRAYSCALE))
        for i in KEY_TO_PATTERN.keys()
    ]


@cache
def get_bbox(
    rect: tuple[int, int, int, int],
) -> tuple[tuple[int, int, int, int], int, int]:
    """
    Calculates the bounding box of the active area within the given window rect.
    Cached in case of repeated calls.

    Args:
        rect (tuple[int, int, int, int]): The window's bounding box (x1, y1, x2, y2)

    Returns:
        tuple[tuple[int, int, int, int], int, int]:
            * The bounding box of the active area within the window (x1, y1, x2, y2)
            * The width of the active area
            * The height of the active area
    """
    bbox = (
        rect[0] + ACTIVE_AREA[0],
        rect[1] + ACTIVE_AREA[1],
        rect[0] + ACTIVE_AREA[0] + (ACTIVE_AREA[2] - ACTIVE_AREA[0]),
        rect[1] + ACTIVE_AREA[1] + (ACTIVE_AREA[3] - ACTIVE_AREA[1]),
    )

    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]

    return (bbox, width, height)


def grab_screenshot(hwnd: int) -> numpy.ndarray | None:
    """
    Captures a screenshot of the specified window and processes it into a grayscale image.

    The function retrieves the window's device context and dimensions, captures the screen content into a bitmap,
    converts the bitmap to a numpy array, and processes it into a grayscale image with thresholding. If DEBUG is
    enabled, it displays the original and processed images side by side.

    Args:
        hwnd (int): Handle to the window to capture.

    Returns:
        numpy.ndarray | None: The processed grayscale image of the window's content, or None if the window is invalid.
    """
    if not win32gui.IsWindow(hwnd):
        return None

    bbox, w, h = get_bbox(win32gui.GetWindowRect(hwnd))

    # Get the device context of the window
    hwnd = win32gui.GetDesktopWindow()
    dc = win32gui.GetWindowDC(hwnd)
    dc_obj = win32ui.CreateDCFromHandle(dc)

    # Create a compatible bitmap and get its handle
    bmp = win32ui.CreateBitmap()
    bmp.CreateCompatibleBitmap(dc_obj, w, h)
    bmp_handle = bmp.GetHandle()

    # Select the bitmap into the device context
    mem_dc = win32gui.CreateCompatibleDC(dc)
    win32gui.SelectObject(mem_dc, bmp_handle)

    # Bit block transfer the window's device context to the bitmap
    win32gui.BitBlt(mem_dc, 0, 0, w, h, dc, bbox[0], bbox[1], win32con.SRCCOPY)

    # Release the device context
    win32gui.ReleaseDC(hwnd, dc)
    win32gui.DeleteDC(mem_dc)

    # Convert the bitmap to a numpy array, reshape the array based on the bitmap's bits per pixel
    bitmap_img = numpy.frombuffer(bmp.GetBitmapBits(True), dtype=numpy.uint8)
    color_img = bitmap_img.reshape((bbox[3] - bbox[1], bbox[2] - bbox[0], 4))

    # Convert to grayscale, threshold the image
    img = cv2.cvtColor(color_img, cv2.COLOR_BGR2GRAY)
    numpy.putmask(img, img <= 248, 0)

    # Delete the bitmap object
    win32gui.DeleteObject(bmp_handle)

    # debug: show imagegrab result
    if DEBUG:
        # concatenate the color image and the grayscale image
        color_img = cv2.cvtColor(color_img, cv2.COLOR_BGR2RGB)
        gray_img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        debug_img = numpy.concatenate((color_img, gray_img), axis=1)

        cv2.imshow("Debug Image", debug_img)
        cv2.setWindowProperty("Debug Image", cv2.WND_PROP_TOPMOST, 1)

        cv2.waitKey(1)

    return img


def post_message(hwnd: int, input: int | None) -> None:
    """
    Simulates a key press event on the window specified by `hwnd`.

    Args:
        hwnd (int): Handle to the window where the key press should be simulated.
        input (int | None): The key to be pressed, or None to do nothing.
    """
    if input is None:
        return

    win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, input, 0)
    time.sleep(0.05)
    win32api.PostMessage(hwnd, win32con.WM_KEYUP, input, 0)


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
        post_message(hwnd, input)
        time.sleep(0.5)
        post_message(hwnd, input)
    else:
        post_message(hwnd, input)


def match_pattern_thread(hwnd, sc, pattern, key) -> None:
    """
    Runs template matching on a given screen and pattern, and simulates a key press event on the window if the pattern is matched.

    Args:
        hwnd (int): Handle to the window where the key press should be simulated.
        sc (ndarray): The screenshot of the window to match the pattern on.
        pattern (ndarray): The pattern to match on the screenshot.
        key (str): The key to be pressed if the pattern is matched, mapped from `KEY_TO_PATTERN`.
    """
    if sc is None:
        return

    res = cv2.matchTemplate(sc, pattern, cv2.TM_CCORR_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(res)

    if max_val < THRESHOLD:
        return

    if DEBUG:
        print("Matched pattern:", key)

    press_key(hwnd, key)
    return


def main() -> None:
    """
    Main entry point.

    - Grabs the screen of the HoloCure window
    - Performs template matching on the grabbed screen
    - Sends a key press event to the window if a pattern is matched
    - If the matching is blank for more than 10 seconds, tries to initiate fishing by sending a Space key press event
    """
    patterns = generate_patterns()

    hwnd = win32gui.FindWindow(None, "HoloCure")
    if not hwnd:
        print("HoloCure window not found")
        return
    win32gui.SetForegroundWindow(hwnd)

    last_idle_time = time.time()

    while True:
        sc = grab_screenshot(hwnd)
        if sc is None:
            print("Unable to create HoloCure screenshot")
            return

        # Skip if the screen is blank
        time_to_check = time.time() - last_idle_time
        if sc.sum() == 0:
            # If the screen is blank for more than 10 seconds, try to initiate fishing
            if time_to_check > 10:
                print("Timeout, trying to initiate fishing...")
                post_message(hwnd, win32con.VK_SPACE)
                last_idle_time = time.time() + 10
            continue

        # Perform template matching
        for key, pattern in patterns:
            match_pattern_thread(hwnd, sc, pattern, key)

        # Update the fishing check
        last_idle_time = time.time() + 10


if __name__ == "__main__":
    main()
