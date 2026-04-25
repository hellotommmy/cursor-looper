"""
Cursor Looper - Auto-repeat instructions for Cursor AI

Monitors workspace file changes. When AI finishes (folder goes idle),
automatically re-sends the same instruction.
"""

import time
import os
import sys
import threading
import argparse
from pathlib import Path

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("Missing dependency: watchdog. Run: pip install watchdog")
    sys.exit(1)

try:
    import pyautogui
except ImportError:
    print("Missing dependency: pyautogui. Run: pip install pyautogui")
    sys.exit(1)

try:
    import pyperclip
except ImportError:
    print("Missing dependency: pyperclip. Run: pip install pyperclip")
    sys.exit(1)


IGNORE_PATTERNS = {
    '.git', '__pycache__', 'node_modules', '.cursor',
    '.vscode', '.idea', '.DS_Store', 'Thumbs.db',
}


class ChangeDetector(FileSystemEventHandler):

    def __init__(self):
        self.last_change_time = 0.0
        self.change_count = 0
        self.lock = threading.Lock()

    def _should_ignore(self, path: str) -> bool:
        parts = Path(path).parts
        return any(p in IGNORE_PATTERNS for p in parts)

    def on_any_event(self, event):
        if self._should_ignore(event.src_path):
            return
        with self.lock:
            self.last_change_time = time.time()
            self.change_count += 1

    def reset(self):
        with self.lock:
            self.last_change_time = 0.0
            self.change_count = 0

    @property
    def has_activity(self):
        with self.lock:
            return self.change_count > 0

    def seconds_since_last_change(self):
        with self.lock:
            if self.last_change_time == 0:
                return float('inf')
            return time.time() - self.last_change_time


def send_to_cursor(instruction: str, hotkey: str = "ctrl+l", delay: float = 1.0):
    """Send instruction to Cursor chat via keyboard automation."""
    pyperclip.copy(instruction)
    time.sleep(0.3)

    keys = hotkey.split('+')
    pyautogui.hotkey(*keys)
    time.sleep(delay)

    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.1)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(0.3)

    pyautogui.hotkey('enter')


def wait_for_ai_start(detector: ChangeDetector, timeout: int = 120):
    """Wait until file changes are detected (AI starts working)."""
    start = time.time()
    while not detector.has_activity:
        time.sleep(0.5)
        elapsed = time.time() - start
        if elapsed > timeout:
            print(f"  [TIMEOUT] No file changes after {timeout}s, moving on...")
            return False
        if int(elapsed) % 10 == 0 and int(elapsed) > 0:
            remaining = timeout - int(elapsed)
            if remaining % 10 == 0:
                print(f"  Waiting for AI to start... ({int(elapsed)}s / {timeout}s)")
    return True


def wait_for_ai_finish(detector: ChangeDetector, idle_timeout: int = 30):
    """Wait until folder is idle for idle_timeout seconds (AI finished)."""
    while True:
        time.sleep(1)
        gap = detector.seconds_since_last_change()
        if gap >= idle_timeout:
            return


def print_banner():
    print("")
    print("  +==========================================+")
    print("  |        Cursor Looper v1.0                |")
    print("  |   Auto-repeat instructions for Cursor AI |")
    print("  +==========================================+")
    print("")


def interactive_loop(workspace: str, idle_timeout: int, hotkey: str,
                     start_wait: int, send_delay: float):
    """Main interactive loop: user enters instruction, tool repeats it."""

    workspace = os.path.abspath(workspace)
    if not os.path.isdir(workspace):
        print(f"Error: directory does not exist -> {workspace}")
        return

    detector = ChangeDetector()
    observer = Observer()
    observer.schedule(detector, workspace, recursive=True)
    observer.start()
    print(f"[DIR]     Monitoring: {workspace}")
    print(f"[IDLE]    Idle threshold: {idle_timeout}s with no file changes = done")
    print(f"[HOTKEY]  Chat shortcut: {hotkey}")
    print(f"Type 'quit' or 'exit' to quit.\n")

    try:
        while True:
            print("=" * 50)
            instruction = input("[INPUT] Enter instruction (to send to Cursor): ").strip()
            if not instruction:
                print("Instruction cannot be empty, please try again.")
                continue
            if instruction.lower() in ('quit', 'exit', 'q'):
                print("Exiting.")
                break

            repeat_input = input("[REPEAT] How many times? (0=infinite, default=1): ").strip()
            repeat_count = int(repeat_input) if repeat_input else 1

            label = "infinite" if repeat_count == 0 else str(repeat_count)
            print(f"\nStarting: repeat {label} time(s)")
            print(f"Press Ctrl+C to interrupt.\n")

            executed = 0
            try:
                while repeat_count == 0 or executed < repeat_count:
                    round_num = executed + 1
                    total_str = "inf" if repeat_count == 0 else str(repeat_count)
                    print(f"  >> Round {round_num}/{total_str} - Sending instruction...")

                    detector.reset()

                    time.sleep(2)
                    send_to_cursor(instruction, hotkey=hotkey, delay=send_delay)

                    print(f"  [SENT] Instruction sent. Waiting for AI to start...")
                    ai_started = wait_for_ai_start(detector, timeout=start_wait)

                    if ai_started:
                        print(f"  [WORKING] AI is working, waiting for it to finish...")
                        wait_for_ai_finish(detector, idle_timeout=idle_timeout)
                        print(f"  [DONE] Round {round_num} complete ({detector.change_count} file changes detected)")
                    else:
                        print(f"  [WARN] Round {round_num}: no AI activity detected")

                    executed += 1

                    if repeat_count > 0 and executed >= repeat_count:
                        break

                    time.sleep(1)

            except KeyboardInterrupt:
                print(f"\n  [STOP] Loop interrupted after {executed} round(s)")

            print(f"\n[RESULT] Task finished: {executed} round(s) completed\n")

    except KeyboardInterrupt:
        print("\nExiting.")
    finally:
        observer.stop()
        observer.join()


def main():
    parser = argparse.ArgumentParser(
        description='Cursor Looper - Auto-repeat instructions for Cursor AI'
    )
    parser.add_argument(
        '-w', '--workspace',
        default='.',
        help='Workspace directory to monitor (default: current dir)'
    )
    parser.add_argument(
        '-t', '--idle-timeout',
        type=int,
        default=30,
        help='Seconds of no file changes before AI is considered done (default: 30)'
    )
    parser.add_argument(
        '-k', '--hotkey',
        default='ctrl+l',
        help='Hotkey to open Cursor chat (default: ctrl+l)'
    )
    parser.add_argument(
        '--start-wait',
        type=int,
        default=120,
        help='Seconds to wait for AI to start working (default: 120)'
    )
    parser.add_argument(
        '--send-delay',
        type=float,
        default=1.0,
        help='Delay after pressing chat hotkey before pasting (default: 1.0s)'
    )

    args = parser.parse_args()

    print_banner()
    interactive_loop(
        workspace=args.workspace,
        idle_timeout=args.idle_timeout,
        hotkey=args.hotkey,
        start_wait=args.start_wait,
        send_delay=args.send_delay,
    )


if __name__ == '__main__':
    main()
