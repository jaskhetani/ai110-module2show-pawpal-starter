# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agent Workflow (SF7)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**What task did you give the agent?**

Extend PawPal+ with advanced scheduling that goes beyond the basic sort/filter:
a **time-blocking conflict detector** (find pending tasks across pets whose
time blocks overlap) and a **`next_available_slot`** finder (earliest free gap
that fits a new task). It had to land as one coherent commit — implementation,
a CLI demonstration, tests, and updated UML/README docs.

**What did the agent do?**

Files modified: `pawpal_system.py`, `main.py`, `tests/test_pawpal.py`,
`diagrams/uml.mmd`, `README.md`, `reflection.md`.

- `pawpal_system.py` — added `_time_to_minutes` / `_minutes_to_time` helpers and
  three `Scheduler` methods: `_time_blocks()`, `detect_conflicts()`, and
  `next_available_slot(duration, day_start, day_end)`.
- `main.py` — added an "Advanced scheduling checks" section that reports current
  conflicts, injects an overlapping "Vet phone call" to trigger one, finds the
  earliest free 20-minute slot, reschedules the call there, and cleans up.
- `tests/test_pawpal.py` — added 6 tests (cross-pet overlap, no-overlap,
  completed-task exclusion, earliest gap, skipping occupied blocks, and
  none-when-full).
- Updated the UML `Scheduler` class and the README (Smarter Scheduling table +
  an "Advanced scheduling" example + refreshed sample output), and ran
  `python main.py` and `pytest` (19 passing).

**What did you have to verify or fix manually?**

- Confirmed the early `break` in `detect_conflicts()` is sound: because blocks
  are sorted by start time, once a later block starts at/after the current
  block's end, nothing after it can overlap either.
- Caught that `next_available_slot()` would otherwise treat the task being
  placed as its own obstacle, so the demo removes the temporary task before
  computing the slot.
- Verified `_time_blocks()` excludes completed tasks (a done task shouldn't
  create a phantom conflict) and that the demo's temporary task is removed so
  the later mark-complete and persistence sections still produce identical
  output.

---

## Prompt Comparison (SF11)

> Compare two different prompts (or two different models) on the same task.

| | Option A | Option B |
|-|----------|----------|
| **Model / tool used** | | |
| **Prompt** | | |
| **Response summary** | | |
| **What was useful** | | |
| **Problems noticed** | | |
| **Decision** | | |

**Which approach did you use in your final implementation and why?**

<!-- Your conclusion -->
