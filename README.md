# Cursor Looper

Auto-repeat prompts for the Cursor CLI agent. When one agent session finishes, the next one starts automatically with the same prompt.

Zero external dependencies -- just Python 3 and the Cursor CLI.

## How it works

1. Runs `cursor agent -p "<your prompt>"` as a subprocess
2. When the agent exits (work complete), re-runs the same command
3. Repeats for the specified number of rounds

No keyboard simulation, no file-system watchers -- just a simple subprocess loop around the official CLI.

## Prerequisites

- Python 3.10+
- [Cursor CLI](https://www.cursor.com/docs/cli/overview) (`cursor` must be on PATH)

## Usage

### Interactive mode (enter prompts at runtime)

```bash
python cursor_looper.py
```

### One-shot mode (specify prompt directly)

```bash
# Run a prompt 5 times
python cursor_looper.py "fix all linting errors" -n 5

# Run infinitely until Ctrl+C
python cursor_looper.py "continue implementing the remaining TODOs" -n 0

# Specify workspace
python cursor_looper.py "refactor auth module" -n 3 -w /path/to/project
```

### Parameters

| Param | Default | Description |
|-------|---------|-------------|
| `prompt` | *(interactive)* | The prompt to send. Omit for interactive mode. |
| `-n, --repeat` | `1` | Repeat count. `0` = infinite. |
| `-w, --workspace` | `.` | Working directory for the agent. |
| `--pause` | `2.0` | Seconds to wait between rounds. |
| `--agent-args` | | Extra args forwarded to `cursor agent`. |

## Examples

```bash
# Interactive: enter a new prompt each time
python cursor_looper.py

# Repeat a refactoring task 10 times
python cursor_looper.py "find the next TODO comment and implement it" -n 10

# Infinite loop with 5s pause between rounds
python cursor_looper.py "check for and fix any remaining test failures" -n 0 --pause 5
```

## License

MIT
