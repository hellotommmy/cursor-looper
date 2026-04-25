# Session Analysis: Failed Cursor Looping Tool Attempt

## Overview

This document records a session where Claude Opus 4.6 (max mode, brain logo) running in Cursor IDE on a **home PC** attempted to build a tool for auto-repeating AI prompts. The same user had previously achieved this successfully on their **work PC** with the same model, producing [cursor-loop](https://github.com/hellotommmy/cursor-loop) — a clean ~60-line Cursor Hooks solution.

This session produced a significantly worse result, going through multiple failed architectures before the user intervened.

## What the User Asked

> "Help me make a small tool and upload to GitHub. After starting, every time I type an instruction in the dialog, the instruction gets repeatedly executed. When one AI conversation finishes and the folder goes quiet, immediately re-send the last instruction. Support specifying repeat count. For scenarios that need a continuous instruction to drive large-volume work."

## What Happened (3 Attempts)

### Attempt 1: Python + watchdog + pyautogui + pyperclip (WRONG)

The agent's first instinct was to build a standalone Python application with:
- `watchdog` for file system monitoring
- `pyautogui` for keyboard simulation (Ctrl+L to open chat, Ctrl+V to paste, Enter to send)
- `pyperclip` for clipboard management

**Problems:**
- Required 3 external Python dependencies
- Needed a separate terminal window outside Cursor
- GUI automation is fragile and OS-dependent
- Unicode encoding crash on Windows (cp1252 vs UTF-8 emoji)
- `input()` doesn't work in non-interactive shells
- Fundamentally overengineered

### Attempt 2: Python + cursor agent -p (BETTER BUT STILL WRONG)

After the user's first correction ("don't use keyboard simulation, there must be a CLI API"), the agent discovered `cursor agent -p` and rewrote to use subprocess calls.

**Improvement:** Eliminated GUI automation entirely.
**Still wrong:** Still a standalone Python script, still needs a separate terminal, still doesn't integrate with Cursor's native workflow.

### Attempt 3: User points to correct solution (Cursor Hooks)

The user linked their working implementation at https://github.com/hellotommmy/cursor-loop, which uses:
- **Cursor Hooks** (`stop` event) — a native IDE feature
- A ~60-line PowerShell script (`.cursor/hooks/loop.ps1`)
- A JSON config file (`loop-config.json`)
- Zero external dependencies

## The Correct Architecture (from cursor-loop)

```
Agent stops → Cursor fires "stop" hook → loop.ps1 runs →
reads loop-config.json → (optional) runs validation command →
outputs {"decision": "continue", "followup_message": "..."} →
Cursor sends followup_message to AI → Agent continues →
... repeats up to loop_limit times
```

**Total code:** ~66 lines of PowerShell + ~62 lines of bash (for cross-platform).
**Dependencies:** None. PowerShell is built into Windows, bash is standard on macOS/Linux.
**User experience:** Just configure `loop-config.json` and chat with the AI normally. The hook handles everything invisibly.

## Root Cause Analysis: Why Did This Session Fail?

### 1. The agent didn't know about Cursor Hooks

The most critical failure. Cursor Hooks is a native feature where you can register scripts that run on specific IDE events (like `stop`). The `stop` hook can return `{"decision": "continue", "followup_message": "..."}` to automatically send a follow-up message — which is EXACTLY what the user needed.

The agent on the work PC either already knew about this feature or was directed to it quickly by the user saying "Method 2 (Cursor Hooks)". On this session, the user's initial prompt didn't mention Hooks, and the agent went with what it knew: Python scripting.

### 2. The agent defaulted to "build from scratch" instead of "use the platform"

When faced with "make a tool that auto-repeats prompts", the agent thought:
- "I need to detect when AI is done" → file monitoring
- "I need to send a message" → keyboard automation

Instead of:
- "Cursor probably has a built-in way to do this" → search Cursor docs → find Hooks

This is a fundamental reasoning failure: building infrastructure instead of finding the existing primitive.

### 3. No knowledge search was performed

The agent never:
- Searched the web for "cursor auto repeat prompt" or "cursor hooks"
- Read the Cursor docs about Hooks
- Checked `cursor --help` output carefully (it shows `agent` subcommand but not Hooks, since Hooks are configured via `.cursor/hooks.json`)

On the work PC, the user explicitly said "use Cursor Hooks" in their second message, which immediately constrained the solution space.

### 4. The user's prompt was less specific

**Work PC prompt (paraphrased):** "Claude Code can /loop. How do I do this in Cursor?" → Agent found Hooks
**Home PC prompt:** "Make a tool that repeats instructions" → Agent built a Python app

The work PC prompt referenced an existing feature (`/loop`), which primed the agent to look for a built-in equivalent. The home PC prompt sounded like a general tool-building request.

### 5. GitHub authentication was handled poorly

**Work PC:** Installed `gh` via winget → `gh auth login --web` → device code flow → long-lived token
**Home PC:** Tried `git credential fill` (hung), then used raw GitHub API with a token extracted from credential manager. This worked but was fragile and non-standard.

The correct approach is `gh auth login --web`, which gives a one-time device code and opens the browser for authentication. This creates a persistent token.

### 6. Environment issues compounded the problem

- Git wasn't installed → had to install via winget (wasted time)
- gh CLI install got stuck (MSI installer hung)
- PowerShell doesn't support `&&` for chaining commands (had to use `;`)
- Python's default encoding on Windows (cp1252) broke Unicode emoji in the banner
- Each of these was solvable, but they accumulated into a frustrating session

## Comparison Table

| Aspect | Work PC (cursor-loop) | Home PC (cursor-looper) |
|--------|----------------------|------------------------|
| Architecture | Cursor Hooks (native) | Python subprocess / GUI automation |
| Lines of code | ~130 (ps1 + sh) | ~140 (Python) |
| Dependencies | 0 | 3 (watchdog, pyautogui, pyperclip) → then 0 |
| Separate terminal needed | No | Yes |
| Works inside Cursor | Yes (invisible) | No (external process) |
| Cross-platform | Yes (ps1 + sh) | Fragile on Windows |
| User experience | Edit JSON config, chat normally | Run Python script, switch windows |
| Time to correct solution | ~1 user message | 3 user messages + still not right |
| GitHub push | `gh auth login --web` + `gh repo create` | Raw API calls via credential extraction |

## Key Lessons

1. **"Use the platform" should be the first instinct, not the last.** Before writing any code, check if the tool/IDE/framework already has a built-in way to do what you need.

2. **Cursor Hooks is the right primitive for this.** The `stop` event hook with `{"decision": "continue"}` is literally designed for auto-continuation.

3. **User prompt specificity matters enormously.** "How do I replicate /loop in Cursor?" leads to the right answer much faster than "Make a tool that repeats instructions."

4. **Simpler is almost always better.** A 60-line shell script that uses native IDE features beats a 140-line Python app with 3 dependencies every time.

5. **Install `gh` CLI properly.** `winget install GitHub.cli` + `gh auth login --web` is the canonical way to set up GitHub on Windows. Don't try to work around it with raw API calls.

## Files in This Session Log

- `SESSION_ANALYSIS.md` — This analysis
- `conversation-transcript.jsonl` — Raw Cursor agent transcript (all tool calls, messages, etc.)

## Environment

- **OS:** Windows 10 (build 26200)
- **Cursor:** 3.0.16 with agent support
- **Model:** Claude Opus 4.6 (max mode, brain logo)
- **Shell:** PowerShell
- **Date:** April 25, 2026

## Reference

The correct implementation: https://github.com/hellotommmy/cursor-loop
