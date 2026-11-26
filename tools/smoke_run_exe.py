"""Launch the desktop build and confirm a rendered game window appears."""
import ctypes
import ctypes.wintypes
import subprocess
import sys
import time
from pathlib import Path

from PIL import ImageGrab

ROOT = Path(__file__).resolve().parents[1]
EXE = (ROOT / 'dist/RogueFPS/RogueFPS.exe').resolve()
SHOT = ROOT / 'artifacts/desktop_build_check.png'
TITLE = '异星实验场'


def find_windows():
    user32 = ctypes.windll.user32
    matches = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def callback(hwnd, _):
        length = user32.GetWindowTextLengthW(hwnd)
        if length:
            buffer = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buffer, length + 1)
            if TITLE in buffer.value:
                matches.append((hwnd, buffer.value))
        return True

    user32.EnumWindows(callback, 0)
    return matches


def capture(hwnd):
    user32 = ctypes.windll.user32
    user32.ShowWindow(hwnd, 9)
    user32.SetForegroundWindow(hwnd)
    time.sleep(2)
    rect = ctypes.wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    if rect.right <= rect.left or rect.bottom <= rect.top:
        return None
    image = ImageGrab.grab(bbox=(rect.left, rect.top, rect.right, rect.bottom), all_screens=True)
    SHOT.parent.mkdir(parents=True, exist_ok=True)
    image.save(SHOT)
    colors = image.convert('RGB').getcolors(maxcolors=1 << 20)
    dark = sum(count for count, color in colors if max(color) < 12)
    white = sum(count for count, color in colors if min(color) > 245)
    total = image.width * image.height
    return image.size, 1 - dark / total, white / total


def main():
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
    started = time.time()
    process = subprocess.Popen([str(EXE)], cwd=str(EXE.parent))
    try:
        deadline = time.time() + 60
        matches = []
        while time.time() < deadline:
            if process.poll() is not None:
                print(f'EXITED code={process.returncode}')
                return 1
            matches = find_windows()
            if matches:
                break
            time.sleep(1)
        if not matches:
            print('NO_WINDOW')
            return 1
        print(f'window_after={time.time() - started:.1f}s')
        hwnd, title = matches[0]
        size = lit = white = None
        for _ in range(25):
            result = capture(hwnd)
            if not result:
                continue
            size, lit, white = result
            if lit >= 0.2 and white <= 0.9:
                break
        print(f'WINDOW title={title} size={size} lit_ratio={lit:.3f} white_ratio={white:.3f}')
        print(f'render_after={time.time() - started:.1f}s')
        if lit is None or lit < 0.2 or white > 0.9:
            print('BLANK_WINDOW')
            return 1
        return 0
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()


if __name__ == '__main__':
    sys.exit(main())