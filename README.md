# Idle Fishing for HoloCure

Uses OpenCV, Pillow, and Windows API to automate HoloCure's fishing mini-game.

> [!NOTE]  
> Please use this script only when you played HoloCure for a good amount of time by yourself. It practically breaks the economy and, as a result, fun.
>
> Please support the creator by giving them a review [on Steam](https://store.steampowered.com/app/2420510/HoloCure__Save_the_Fans/).

## How to use

1. Install Python 3.12 or later
2. `pip install -r requirements.txt` (I recommend creating a `venv` first)
3. Open HoloCure, make it windowed, navigate to Holo House
4. `python idle-fishing.py`, Esc menu should pop up
5. Initiate fishing manually
6. ...
7. PROFIT!
8. Halt the script when you want to stop fishing

The HoloCure window must be on the foreground, but you can still use your PC as usual as the script does not interfere with your inputs.

Make sure your mouse is not on top of the HoloCure window (specifically the target area of the fishing mini-game).

## Known issues

- Works only on Windows.
- Tested only with 1280x720 resolution of the HoloCure window.
- Template matching might fail on very high speed levels.
- In rare occasions, fishing does not start automatically.
