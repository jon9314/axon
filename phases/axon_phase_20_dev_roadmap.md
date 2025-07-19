# Axon Development Roadmap: Phase 20 – CLI Utility Suite, Shell Interaction, and Scriptable Modes

This document outlines **Phase 20** of the Axon agent system. This phase introduces CLI-only deployment modes, useful developer tools, and interfaces for shell scripting or command-based workflows.

---

## 🖥️ 20.1 – CLI Startup Mode
**Goal:** Enable Axon to run entirely from the command line for headless environments, testing, or constrained systems.

**Features:**
- `--cli` flag starts Axon in terminal-only mode
- Memory read/write via shell prompts
- Lightweight REPL interface (Read-Eval-Print Loop)
- Colorized terminal output for clarity

**Commands (tentative):**
- `note "Remember to check insulation."`
- `search attic`
- `summary today`

---

## 🔌 20.2 – Scripting & Automation Support
**Goal:** Allow Axon to be triggered from shell scripts or external automations.

**Interface Options:**
- `axon run --file note.md`
- `axon query --prompt "Summarize last week’s tasks"`
- Exit codes and JSON output flags

**Optional:**
- Pipe/redirect support for Unix workflows (e.g., `echo "idea" | axon note`)

---

## ⚙️ 20.3 – CLI Plugin Introspection
**Goal:** Make it easy to inspect plugins or loaded tools via CLI.

**Examples:**
- `axon plugins list`
- `axon plugins info summarizer`
- `axon memory stats`

Useful for headless ops and plugin debugging.

---

## 🧪 20.4 – TTY Compatibility and Fallbacks
**Goal:** Ensure CLI works across terminals (Linux, macOS, Windows).

**Handling:**
- Graceful degradation in no-color terminals
- UTF-8-safe output
- Responsive to common interruptions (Ctrl+C, Ctrl+D)

---

## ✅ Phase 20 Completion Criteria
- CLI mode fully functional with memory and chat interaction
- Script-compatible flags and basic piping supported
- CLI plugin visibility and inspection tools
- Terminal compatibility across platforms

---

Next: Phase 21 – Agent Scheduling Framework, Recurring Task Memory, and Event Time Normalization

