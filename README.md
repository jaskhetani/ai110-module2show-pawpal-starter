# PawPal+ (Module 2 Project)

**PawPal+** is a Python pet-care planning system. It helps a busy owner stay on top of daily care by modeling **owners, pets, and tasks** as classes and using a **`Scheduler`** to sort tasks by priority, fit them into the owner's available time, and produce an explained daily plan across all of their pets. Run the [`main.py`](main.py) command-line demo to see the whole workflow end to end.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

The system was designed UML-first ([`diagrams/uml.mmd`](diagrams/uml.mmd)), implemented in [`pawpal_system.py`](pawpal_system.py), verified with a `pytest` suite, and demonstrated through the [`main.py`](main.py) CLI.

## What PawPal+ does

PawPal+ can:

- Model an owner, their pets, and each pet's care tasks (duration, priority, and due time)
- Sort tasks across **all** pets by priority, breaking ties by earliest due time
- Generate a daily plan that fits the owner's available time and explains what it scheduled — and what it skipped
- Mark tasks complete and re-plan the day
- Back all of this with a `pytest` suite covering the key scheduling behaviors

## 🧱 System Design

PawPal+ is built from four classes (see [`diagrams/uml.mmd`](diagrams/uml.mmd) for the full class diagram). The domain model lives in [`pawpal_system.py`](pawpal_system.py):

- **`Task`** — one care activity. Holds `description`, `due_time` (a 24h `"HH:MM"` string), `duration_minutes`, `priority` (`low` / `medium` / `high`), and a `completed` flag. `mark_complete()` closes it out, and `priority_weight()` turns the priority label into a sortable number (high = 3 … low = 1).
- **`Pet`** — a pet (`name`, `species`) that owns a list of `Task`s. Methods to `add_task()` (which also stamps the task with the pet's name), `remove_task()`, `list_tasks()`, and `pending_tasks()`.
- **`Owner`** — a person (`name`) with a daily `available_minutes` budget and a list of `Pet`s. Methods `add_pet()`, `get_pet()`, and `all_tasks()`, which flattens every pet's tasks into one list.

The **`Scheduler`** — the class that plans across *all* of an owner's pets — is described under [Smarter Scheduling](#-smarter-scheduling) below.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Running the demo and tests

```bash
python main.py       # run the CLI demo (builds the sample world and plans the day)
pytest               # run the full test suite from the project root
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Below is the output of `python main.py`, which builds one owner (Jordan), two pets (Biscuit the dog and Mochi the cat), and seven tasks, then uses the `Scheduler` to sort and plan the day:

```
============================================================
PawPal+ - Daily Care Planner
============================================================
Owner: Jordan (daily time budget: 120 min)
  Biscuit (dog) - 4 task(s)
    - [ ] Breakfast (10 min, high, due 07:30)
    - [ ] Morning walk (30 min, high, due 08:00)
    - [ ] Fetch / enrichment (25 min, low, due 16:00)
    - [ ] Evening walk (30 min, medium, due 18:00)
  Mochi (cat) - 3 task(s)
    - [ ] Litter cleanup (10 min, medium, due 07:45)
    - [ ] Thyroid meds (5 min, high, due 09:00)
    - [ ] Brush coat (15 min, low, due 19:00)

------------------------------------------------------------
All tasks across pets, sorted by priority then due time:
------------------------------------------------------------
  Biscuit  [ ] Breakfast (10 min, high, due 07:30)
  Biscuit  [ ] Morning walk (30 min, high, due 08:00)
  Mochi    [ ] Thyroid meds (5 min, high, due 09:00)
  Mochi    [ ] Litter cleanup (10 min, medium, due 07:45)
  Biscuit  [ ] Evening walk (30 min, medium, due 18:00)
  Biscuit  [ ] Fetch / enrichment (25 min, low, due 16:00)
  Mochi    [ ] Brush coat (15 min, low, due 19:00)

------------------------------------------------------------
Daily plan for Jordan (120 min available):
  1. 07:30  Biscuit: Breakfast (10 min, high priority)
  2. 07:45  Mochi: Litter cleanup (10 min, medium priority)
  3. 08:00  Biscuit: Morning walk (30 min, high priority)
  4. 09:00  Mochi: Thyroid meds (5 min, high priority)
  5. 16:00  Biscuit: Fetch / enrichment (25 min, low priority)
  6. 18:00  Biscuit: Evening walk (30 min, medium priority)
  Time used: 110/120 min.
  Skipped (over budget):
    - Mochi: Brush coat (15 min, low)

------------------------------------------------------------
Advanced scheduling checks:
  Conflicts in current schedule: 0
  CONFLICT: Biscuit's 'Vet phone call' (08:15) overlaps Biscuit's 'Morning walk' (08:00)
  Earliest free 20-min slot: 07:00
  After scheduling the call at 07:00, conflicts: 0

------------------------------------------------------------
Marking Biscuit's 'Morning walk' complete and re-planning...
------------------------------------------------------------
Daily plan for Jordan (120 min available):
  1. 07:30  Biscuit: Breakfast (10 min, high priority)
  2. 07:45  Mochi: Litter cleanup (10 min, medium priority)
  3. 09:00  Mochi: Thyroid meds (5 min, high priority)
  4. 16:00  Biscuit: Fetch / enrichment (25 min, low priority)
  5. 18:00  Biscuit: Evening walk (30 min, medium priority)
  6. 19:00  Mochi: Brush coat (15 min, low priority)
  Time used: 95/120 min.

------------------------------------------------------------
Saved to pawpal_data.json and reloaded: 2 pets, 7 tasks, 'Morning walk' still marked complete = True.
```

## 🧪 Testing PawPal+

Run the full suite from the project root:

```bash
pytest
```

**Test coverage summary** — [`tests/test_pawpal.py`](tests/test_pawpal.py) has 10 passing tests:

- **Task** — `mark_complete()` flips completion status; `priority_weight()` ranks high/medium/low and falls back to `0` for unknown labels.
- **Pet / Owner** — `add_task()` stamps the pet's name onto the task; `pending_tasks()` excludes completed tasks; `Owner.all_tasks()` flattens tasks from every pet.
- **Scheduler — sorting** — `sort_by_priority()` puts high-priority tasks first across *both* pets and breaks ties by earliest due time.
- **Scheduler — filtering / planning** — `filter_by_time_budget()` never exceeds the budget and drops tasks that no longer fit; `build_daily_plan()` returns tasks in chronological order; completing a task frees budget so a previously-skipped task reappears in the re-plan.

Sample output:

```
============================= test session starts =============================
platform win32 -- Python 3.13.7, pytest-9.1.1, pluggy-1.6.0
rootdir: <project root>
plugins: anyio-4.14.1
collected 10 items

tests\test_pawpal.py ..........                                          [100%]

============================= 10 passed in 0.11s ==============================
```

## 📐 Smarter Scheduling

The **`Scheduler`** holds a reference to an `Owner` and plans across **all** of that owner's pets. It exposes two core algorithmic features plus a combined planner:

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `sort_by_priority()` | Multi-key sort of every pet's tasks: highest `priority` first, ties broken by earliest `due_time`. |
| Filtering | `filter_by_time_budget(minutes)` | Greedy selection in priority order — keeps adding tasks until the owner's daily `available_minutes` runs out, skipping any that no longer fit. |
| Daily plan | `build_daily_plan()` / `explain_plan()` | Runs the filter against the owner's budget, then returns the kept tasks in chronological (`due_time`) order; `explain_plan()` also lists what was skipped and why. |
| Conflict handling | `detect_conflicts()` | Flags pending tasks across pets whose time blocks (`due_time` + duration) overlap — the owner can't be in two places at once. |
| Free-slot search | `next_available_slot(minutes)` | Finds the earliest gap in the day (default 07:00–21:00) that fits a new task without overlapping existing blocks. |
| Recurring tasks | _planned (stretch)_ | Daily vs. weekly repetition. |

Both `sort_by_priority()` and `filter_by_time_budget()` read from `owner.all_tasks()`, so they consider tasks from **every** pet, not just one.

### Advanced scheduling (stretch)

`detect_conflicts()` and `next_available_slot()` add **time-blocking** on top of the basic planner: each task occupies the block `[due_time, due_time + duration)`, a conflict is any overlap between two blocks (even across different pets), and the slot finder scans the free gaps. From the demo — a vet call added at 08:15 collides with the 08:00 walk, and the finder relocates it to the first open 20-minute slot:

```
Advanced scheduling checks:
  Conflicts in current schedule: 0
  CONFLICT: Biscuit's 'Vet phone call' (08:15) overlaps Biscuit's 'Morning walk' (08:00)
  Earliest free 20-min slot: 07:00
  After scheduling the call at 07:00, conflicts: 0
```

## 💾 Data Persistence

PawPal+ can save an owner — with every pet and task — to JSON and load it back, so state survives between runs.

- **Save:** `save_owner(owner, "pawpal_data.json")` serializes the owner via `Owner.to_dict()` → `Pet.to_dict()` → `Task.to_dict()` and writes indented JSON.
- **Load:** `load_owner("pawpal_data.json")` reads the file and rebuilds the objects with the matching `from_dict()` classmethods (returning `None` if the file doesn't exist). Because `Pet.from_dict()` re-runs `add_task()`, each task's `pet_name` back-reference is restored automatically.

The [`main.py`](main.py) demo saves after planning and immediately reloads to confirm the round trip — including that a completed task stays completed. The generated `pawpal_data.json` is git-ignored.

**Files modified for this feature:** [`pawpal_system.py`](pawpal_system.py) (`to_dict`/`from_dict` on `Task`/`Pet`/`Owner` + module-level `save_owner`/`load_owner`), [`main.py`](main.py) (save/reload demo), [`tests/test_pawpal.py`](tests/test_pawpal.py) (round-trip, file, and missing-file tests), and `.gitignore`.

## 📸 Demo Walkthrough

Follow along with the CLI demo (`python main.py`):

1. **Build the world.** `build_demo_owner()` creates owner *Jordan* with a 120-minute daily budget, two pets (*Biscuit* the dog, *Mochi* the cat), and seven tasks split across them.
2. **See the roster.** The demo prints each pet and its tasks so you can see the raw, unsorted care list.
3. **Sort across pets.** `Scheduler.sort_by_priority()` merges every pet's tasks into one list ordered by priority (high → low), breaking ties by earliest due time.
4. **Plan the day.** `Scheduler.explain_plan()` greedily fits tasks into the 120-minute budget, prints them in chronological order, and lists what was skipped — here *Brush coat* is dropped because only 10 minutes remain.
5. **Complete and re-plan.** The demo marks Biscuit's *Morning walk* complete; because completed tasks leave the plan, 30 minutes free up and the re-plan now includes *Brush coat* (95/120 min used).

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
