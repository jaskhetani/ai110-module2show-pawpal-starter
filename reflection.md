# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

My initial UML design (`diagrams/uml.mmd`) uses four classes with a clear
ownership hierarchy:

- **Task** — the smallest unit of work. It holds `description`, `due_time`,
  `duration_minutes`, `priority`, and a `completed` flag, plus a `pet_name`
  back-reference so a task can be traced to its pet once it leaves the pet's
  list. Its responsibility is to *describe one care activity and know whether
  it is done* (`mark_complete()`, `priority_weight()`).
- **Pet** — owns a collection of `Task`s. Responsible for *managing its own
  tasks* (`add_task()`, `remove_task()`, `list_tasks()`, `pending_tasks()`).
- **Owner** — owns a collection of `Pet`s plus a daily time budget
  (`available_minutes`). Responsible for *modeling the human and their pets*
  (`add_pet()`, `get_pet()`, `all_tasks()` to flatten every pet's tasks).
- **Scheduler** — holds a reference to an `Owner` and is the only class that
  reasons *across multiple pets*. Responsible for the algorithmic work:
  ordering tasks (`sort_by_priority()`), fitting them into the owner's time
  budget (`filter_by_time_budget()`), producing a daily plan
  (`build_daily_plan()`), and explaining it (`explain_plan()`).

Relationships: `Owner "1" --> "*" Pet`, `Pet "1" --> "*" Task`, and
`Scheduler "1" --> "1" Owner`. Keeping the Scheduler pointed at the Owner (not
at a single Pet) is what forces the scheduling logic to be genuinely
cross-pet.

**b. Design changes**

The class structure held up well against the original diagram, but two
refinements emerged during implementation:

1. I split *selection* from *presentation* in the planner. `build_daily_plan()`
   still **chooses** tasks by priority (via `filter_by_time_budget()`), but it
   returns them sorted by `due_time` so the plan reads chronologically like a
   real daily schedule. The diagram originally implied a single ordering.
2. I added `explain_plan()` to the `Scheduler` to satisfy the scenario's "explain
   why it chose that plan" goal — it reports both the scheduled tasks and the
   ones skipped for being over budget. The UML was updated to include it.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers three constraints, in this order of importance:

1. **Priority** — each task is `high`, `medium`, or `low`; `priority_weight()`
   turns that into a number so the sort can put urgent care first.
2. **Time budget** — the owner has a daily `available_minutes` cap, and
   `filter_by_time_budget()` refuses to schedule more work than fits.
3. **Due time** — used as the tie-breaker when sorting, and to order the final
   plan chronologically so it reads like a real daily schedule.

I decided priority mattered most because pet care has genuinely urgent items
(medication, feeding) that should never be dropped in favor of optional ones
(enrichment, extra grooming). Time is the hard constraint that makes the
problem interesting — without a budget, "the plan" is just "do everything."

**b. Tradeoffs**

The filter is **greedy**: it walks tasks in priority order and grabs each one
that still fits, rather than searching for the combination of tasks that packs
the day most tightly (a knapsack-style optimum). This means it can leave a few
minutes unused — e.g. it may keep one 45-minute high-priority walk and skip a
40-minute medium task even though two 20-minute tasks would have filled the
slot better.

That tradeoff is reasonable here because an owner reasons the same way ("do the
important things first"), the result is predictable and easy to explain via
`explain_plan()`, and it runs in a simple `O(n log n)` sort instead of an
exponential search. Optimal packing would be surprising and hard to justify to
a user who just wants their pet's essentials handled first.

---

## 3. AI Collaboration

**a. How you used AI**

I used AI across the whole project: brainstorming the class breakdown for the
UML, turning that design into Python classes, writing the `pytest` suite, and
generating the CLI demo. The most useful prompting move was giving the AI the
**full grading rubric up front** and asking it to produce a *commit-by-commit
plan* before writing any code. That forced the work into small, reviewable
steps. The second most useful instruction was "keep the docs in sync with the
code in each commit" — it stopped documentation from drifting away from what
the code actually did.

**b. Judgment and verification**

One suggestion I pushed back on was framing the scheduler as producing an
"optimal" daily plan. The implementation is a **greedy** fit, which is *not*
globally optimal (it can leave a few minutes unused), so I kept the honest
framing in the README and reflection instead of overselling it. I verified the
AI's code rather than trusting it: I ran `python main.py` and read the output
by hand (checking that high-priority tasks came first, that the over-budget
task was correctly skipped, and that completing a task freed time on the
re-plan), and I encoded those expectations as assertions in
`tests/test_pawpal.py` so the behavior is checked automatically.

---

## 4. Testing and Verification

**a. What you tested**

The suite (`tests/test_pawpal.py`, 10 tests) covers the behaviors the rest of
the system depends on: `mark_complete()` flipping status, `priority_weight()`
ranking (including an unknown label falling back to 0), `add_task()` stamping
the pet's name, `pending_tasks()` excluding completed work, `all_tasks()`
flattening across pets, priority sorting with a due-time tie-break, the
time-budget filter never exceeding the budget, chronological plan ordering,
and completing a task freeing budget for a previously-skipped one. These matter
because the whole daily plan is built on correct sorting and filtering — if
those are wrong, everything downstream is wrong.

**b. Confidence**

I'm confident the core behaviors are correct: all 10 tests pass and the CLI
output matches what I expect by hand. If I had more time I'd add edge-case
tests for: a task whose duration exceeds the entire budget, an owner with
`available_minutes = 0`, two tasks that share both priority *and* due time
(stable-sort behavior), and `remove_task()` when two tasks share a
description.

---

## 5. Reflection

**a. What went well**

I'm most satisfied with the clean separation of responsibilities — `Task`,
`Pet`, and `Owner` are simple data-and-behavior classes, and *only* the
`Scheduler` reasons across multiple pets. Pointing the `Scheduler` at the
`Owner` (rather than a single `Pet`) is what made the "across all pets"
requirement fall out naturally instead of being bolted on.

**b. What you would improve**

The greedy time-budget fit is the obvious target. In another iteration I'd add
real **time-blocking** (assign start/end times and detect overlaps) and
smarter packing so the day isn't left with unused gaps, plus support for
**recurring tasks**. (JSON **data persistence** was added afterward as a
stretch feature — see the README's Data Persistence section.)

**c. Key takeaway**

Designing the UML first paid off: because the class boundaries were decided
before any code, implementation and testing were mostly mechanical. And AI is
most valuable when you hand it a clear specification (the rubric) and then make
it *prove* its work — running the demo and writing tests caught the difference
between code that looks right and code that is right.
