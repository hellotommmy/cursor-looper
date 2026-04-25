"""
Cursor Looper - Auto-repeat prompts via Cursor CLI agent.

Runs `cursor agent -p <prompt>` in a loop. Each invocation is a full
agent session that exits on completion; the script simply re-launches it.
"""

import subprocess
import sys
import time
import argparse
import os


def run_agent_once(prompt: str, workspace: str, extra_args: list[str]) -> int:
    """Run one `cursor agent -p <prompt>` session, return exit code."""
    cmd = ["cursor", "agent", "-p", prompt] + extra_args
    result = subprocess.run(cmd, cwd=workspace)
    return result.returncode


def print_banner():
    print("")
    print("  +==========================================+")
    print("  |        Cursor Looper v2.0                |")
    print("  |   Auto-repeat prompts for Cursor Agent   |")
    print("  +==========================================+")
    print("")


def interactive_loop(workspace: str, pause: float, extra_args: list[str]):
    """Main loop: user enters a prompt, tool repeats it N times."""

    workspace = os.path.abspath(workspace)
    print(f"[DIR]   Workspace: {workspace}")
    print(f"[PAUSE] Pause between rounds: {pause}s")
    print(f"Type 'quit' or 'exit' to quit.\n")

    while True:
        print("=" * 50)
        try:
            prompt = input("[PROMPT] Enter instruction: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not prompt:
            print("Prompt cannot be empty.")
            continue
        if prompt.lower() in ('quit', 'exit', 'q'):
            print("Exiting.")
            break

        try:
            repeat_input = input("[REPEAT] How many times? (0=infinite, default=1): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        repeat_count = int(repeat_input) if repeat_input else 1
        label = "infinite" if repeat_count == 0 else str(repeat_count)
        print(f"\nWill run: {label} time(s). Ctrl+C to stop.\n")

        executed = 0
        try:
            while repeat_count == 0 or executed < repeat_count:
                round_num = executed + 1
                total = "inf" if repeat_count == 0 else str(repeat_count)
                print(f"--- Round {round_num}/{total} ---")

                rc = run_agent_once(prompt, workspace, extra_args)
                executed += 1

                print(f"--- Round {round_num} finished (exit code {rc}) ---\n")

                if repeat_count > 0 and executed >= repeat_count:
                    break

                if pause > 0:
                    print(f"Pausing {pause}s before next round...")
                    time.sleep(pause)

        except KeyboardInterrupt:
            print(f"\n[STOP] Interrupted after {executed} round(s).")

        print(f"\n[DONE] {executed} round(s) completed.\n")


def oneshot(prompt: str, repeat_count: int, workspace: str,
            pause: float, extra_args: list[str]):
    """Non-interactive mode: run a given prompt N times and exit."""

    workspace = os.path.abspath(workspace)
    label = "infinite" if repeat_count == 0 else str(repeat_count)
    print(f"[DIR]   {workspace}")
    print(f"[RUNS]  {label}")
    print(f"[PROMPT] {prompt}\n")

    executed = 0
    try:
        while repeat_count == 0 or executed < repeat_count:
            round_num = executed + 1
            total = "inf" if repeat_count == 0 else str(repeat_count)
            print(f"--- Round {round_num}/{total} ---")

            rc = run_agent_once(prompt, workspace, extra_args)
            executed += 1

            print(f"--- Round {round_num} finished (exit code {rc}) ---\n")

            if repeat_count > 0 and executed >= repeat_count:
                break

            if pause > 0:
                print(f"Pausing {pause}s before next round...")
                time.sleep(pause)

    except KeyboardInterrupt:
        print(f"\n[STOP] Interrupted after {executed} round(s).")

    print(f"[DONE] {executed} round(s) completed.")


def main():
    parser = argparse.ArgumentParser(
        description='Cursor Looper - auto-repeat prompts via Cursor CLI agent'
    )
    parser.add_argument(
        'prompt', nargs='?', default=None,
        help='Prompt to send (omit for interactive mode)'
    )
    parser.add_argument(
        '-n', '--repeat', type=int, default=1,
        help='Repeat count (0=infinite, default=1). Used with positional prompt.'
    )
    parser.add_argument(
        '-w', '--workspace', default='.',
        help='Workspace directory (default: current dir)'
    )
    parser.add_argument(
        '--pause', type=float, default=2.0,
        help='Seconds to pause between rounds (default: 2)'
    )
    parser.add_argument(
        '--agent-args', nargs=argparse.REMAINDER, default=[],
        help='Extra arguments forwarded to cursor agent'
    )

    args = parser.parse_args()

    print_banner()

    if args.prompt:
        oneshot(args.prompt, args.repeat, args.workspace,
                args.pause, args.agent_args)
    else:
        interactive_loop(args.workspace, args.pause, args.agent_args)


if __name__ == '__main__':
    main()
