# Idle Fishing for HoloCure

Uses OpenCV and WinAPI to automate HoloCure's fishing mini-game.

> [!NOTE]  
> Please use this script only when you played HoloCure for a good amount of time by yourself. It practically breaks the economy and, as a result, fun.
>
> Please support the creator by giving them a review [on Steam](https://store.steampowered.com/app/2420510/HoloCure__Save_the_Fans/).

## How to use

1. Install Python 3.12.x
2. (optional, but recommended) Create a `venv`, activate it
3. `pip install -r requirements.txt`
4. Open HoloCure, make it windowed (resolution must be 1280x720), navigate to Holo House's pond
5. Start the script by running `python idle-fishing.py`
6. Wait for it to start fishing
7. ...
8. PROFIT!

The HoloCure window **must** be on the foreground, but you can still use your PC as usual as the script does not interfere with your inputs.

Make sure your mouse is not on top of the HoloCure window (specifically the target area of the fishing mini-game).

The script is written with a lot of comments, so you can easily understand what it does.

## Limitations

- Works only on Windows.
- Works only in windowed mode with 1280x720 resolution.
