"""
Cursor Looper - 自动重复发送指令给 Cursor AI 的工具

监控工作区文件变化，当 AI 完成工作（文件夹无变动）后自动重新发送指令。
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
    print("缺少依赖: watchdog。请运行: pip install watchdog")
    sys.exit(1)

try:
    import pyautogui
except ImportError:
    print("缺少依赖: pyautogui。请运行: pip install pyautogui")
    sys.exit(1)

try:
    import pyperclip
except ImportError:
    print("缺少依赖: pyperclip。请运行: pip install pyperclip")
    sys.exit(1)


IGNORE_PATTERNS = {
    '.git', '__pycache__', 'node_modules', '.cursor',
    '.vscode', '.idea', '.DS_Store', 'Thumbs.db',
}


class ChangeDetector(FileSystemEventHandler):
    """监控文件系统变化，记录最后变动时间"""

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
    """通过键盘自动化将指令发送到 Cursor 的聊天框"""
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
    """等待 AI 开始工作（检测到文件变化）"""
    start = time.time()
    while not detector.has_activity:
        time.sleep(0.5)
        elapsed = time.time() - start
        if elapsed > timeout:
            print(f"  ⏳ 等待 {timeout}s 未检测到文件变化，继续下一轮...")
            return False
        if int(elapsed) % 10 == 0 and int(elapsed) > 0:
            remaining = timeout - int(elapsed)
            if remaining % 10 == 0:
                print(f"  等待 AI 开始... ({int(elapsed)}s / {timeout}s)")
    return True


def wait_for_ai_finish(detector: ChangeDetector, idle_timeout: int = 30):
    """等待 AI 完成工作（文件夹连续 idle_timeout 秒无变化）"""
    while True:
        time.sleep(1)
        gap = detector.seconds_since_last_change()
        if gap >= idle_timeout:
            return


def print_banner():
    banner = r"""
  ╔══════════════════════════════════════════╗
  ║        Cursor Looper v1.0               ║
  ║   自动重复发送指令给 Cursor AI           ║
  ╚══════════════════════════════════════════╝
    """
    print(banner)


def interactive_loop(workspace: str, idle_timeout: int, hotkey: str,
                     start_wait: int, send_delay: float):
    """交互式主循环：用户输入指令后自动重复执行"""

    workspace = os.path.abspath(workspace)
    if not os.path.isdir(workspace):
        print(f"错误: 目录不存在 -> {workspace}")
        return

    detector = ChangeDetector()
    observer = Observer()
    observer.schedule(detector, workspace, recursive=True)
    observer.start()
    print(f"📂 监控目录: {workspace}")
    print(f"⏱  空闲判定: {idle_timeout}s 无文件变化视为完成")
    print(f"⌨  聊天快捷键: {hotkey}")
    print(f"输入 'quit' 或 'exit' 退出程序\n")

    try:
        while True:
            print("=" * 50)
            instruction = input("📝 输入指令 (发送给 Cursor): ").strip()
            if not instruction:
                print("指令不能为空，请重新输入。")
                continue
            if instruction.lower() in ('quit', 'exit', 'q'):
                print("退出程序。")
                break

            repeat_input = input("🔄 重复次数 (0=无限, 默认1): ").strip()
            repeat_count = int(repeat_input) if repeat_input else 1

            print(f"\n开始执行: 重复 {'无限' if repeat_count == 0 else repeat_count} 次")
            print(f"按 Ctrl+C 可随时中断当前循环\n")

            executed = 0
            try:
                while repeat_count == 0 or executed < repeat_count:
                    round_num = executed + 1
                    total_str = '∞' if repeat_count == 0 else str(repeat_count)
                    print(f"  ▶ 第 {round_num}/{total_str} 轮 - 发送指令...")

                    detector.reset()

                    time.sleep(2)
                    send_to_cursor(instruction, hotkey=hotkey, delay=send_delay)

                    print(f"  ✅ 指令已发送，等待 AI 开始工作...")
                    ai_started = wait_for_ai_start(detector, timeout=start_wait)

                    if ai_started:
                        print(f"  🔨 AI 正在工作，等待完成...")
                        wait_for_ai_finish(detector, idle_timeout=idle_timeout)
                        print(f"  ✅ 第 {round_num} 轮完成 (检测到 {detector.change_count} 次文件变化)")
                    else:
                        print(f"  ⚠  第 {round_num} 轮：未检测到 AI 活动")

                    executed += 1

                    if repeat_count > 0 and executed >= repeat_count:
                        break

                    time.sleep(1)

            except KeyboardInterrupt:
                print(f"\n  ⏹ 循环被中断，已完成 {executed} 轮")

            print(f"\n📊 本次任务完成: 共执行 {executed} 轮\n")

    except KeyboardInterrupt:
        print("\n退出程序。")
    finally:
        observer.stop()
        observer.join()


def main():
    parser = argparse.ArgumentParser(
        description='Cursor Looper - 自动重复发送指令给 Cursor AI'
    )
    parser.add_argument(
        '-w', '--workspace',
        default='.',
        help='要监控的工作区目录 (默认: 当前目录)'
    )
    parser.add_argument(
        '-t', '--idle-timeout',
        type=int,
        default=30,
        help='文件无变化多少秒后判定 AI 完成 (默认: 30)'
    )
    parser.add_argument(
        '-k', '--hotkey',
        default='ctrl+l',
        help='打开 Cursor 聊天的快捷键 (默认: ctrl+l)'
    )
    parser.add_argument(
        '--start-wait',
        type=int,
        default=120,
        help='等待 AI 开始工作的超时秒数 (默认: 120)'
    )
    parser.add_argument(
        '--send-delay',
        type=float,
        default=1.0,
        help='按下聊天快捷键后等待多久再粘贴 (默认: 1.0s)'
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
