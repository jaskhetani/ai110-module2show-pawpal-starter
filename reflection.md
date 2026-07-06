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

*(To be completed as implementation proceeds — this section will record any
divergence between the diagram above and the final code.)*

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

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
