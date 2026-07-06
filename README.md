# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

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
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

## 📐 Smarter Scheduling

The **`Scheduler`** holds a reference to an `Owner` and plans across **all** of that owner's pets. It exposes two core algorithmic features plus a combined planner:

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `sort_by_priority()` | Multi-key sort of every pet's tasks: highest `priority` first, ties broken by earliest `due_time`. |
| Filtering | `filter_by_time_budget(minutes)` | Greedy selection in priority order — keeps adding tasks until the owner's daily `available_minutes` runs out, skipping any that no longer fit. |
| Daily plan | `build_daily_plan()` / `explain_plan()` | Runs the filter against the owner's budget, then returns the kept tasks in chronological (`due_time`) order; `explain_plan()` also lists what was skipped and why. |
| Conflict handling | _planned (stretch)_ | Detect overlapping time slots across pets. |
| Recurring tasks | _planned (stretch)_ | Daily vs. weekly repetition. |

Both `sort_by_priority()` and `filter_by_time_budget()` read from `owner.all_tasks()`, so they consider tasks from **every** pet, not just one.

## 📸 Demo Walkthrough

Follow along with the CLI demo (`python main.py`):

1. **Build the world.** `build_demo_owner()` creates owner *Jordan* with a 120-minute daily budget, two pets (*Biscuit* the dog, *Mochi* the cat), and seven tasks split across them.
2. **See the roster.** The demo prints each pet and its tasks so you can see the raw, unsorted care list.
3. **Sort across pets.** `Scheduler.sort_by_priority()` merges every pet's tasks into one list ordered by priority (high → low), breaking ties by earliest due time.
4. **Plan the day.** `Scheduler.explain_plan()` greedily fits tasks into the 120-minute budget, prints them in chronological order, and lists what was skipped — here *Brush coat* is dropped because only 10 minutes remain.
5. **Complete and re-plan.** The demo marks Biscuit's *Morning walk* complete; because completed tasks leave the plan, 30 minutes free up and the re-plan now includes *Brush coat* (95/120 min used).

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
