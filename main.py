"""PawPal+ command-line demo.

Builds a small but complete scenario -- one owner, two pets, and several
care tasks -- then uses the Scheduler to sort tasks by priority and to build
an explained daily plan, rendered with tabulate tables + emoji. Run with:

    python main.py
"""

import sys

from formatting import format_plan, format_roster
from pawpal_system import (
    DEFAULT_DATA_FILE,
    Owner,
    Pet,
    Scheduler,
    Task,
    load_owner,
    save_owner,
)

# Emoji and box-drawing characters need a UTF-8 stdout (e.g. on Windows).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_demo_owner() -> Owner:
    """Create a sample owner with two pets and several tasks."""
    owner = Owner("Jordan", available_minutes=120)

    biscuit = Pet("Biscuit", "dog")
    biscuit.add_task(Task("Breakfast", "07:30", 10, "high"))
    biscuit.add_task(Task("Morning walk", "08:00", 30, "high"))
    biscuit.add_task(Task("Fetch / enrichment", "16:00", 25, "low"))
    biscuit.add_task(Task("Evening walk", "18:00", 30, "medium"))

    mochi = Pet("Mochi", "cat")
    mochi.add_task(Task("Litter cleanup", "07:45", 10, "medium"))
    mochi.add_task(Task("Thyroid meds", "09:00", 5, "high"))
    mochi.add_task(Task("Brush coat", "19:00", 15, "low"))

    owner.add_pet(biscuit)
    owner.add_pet(mochi)
    return owner


def main() -> None:
    owner = build_demo_owner()
    scheduler = Scheduler(owner)

    print("=" * 60)
    print("🐾 PawPal+ — Daily Care Planner")
    print("=" * 60)
    print(f"Owner: {owner.name}  (daily time budget: {owner.available_minutes} min)\n")
    print("📋 Care roster")
    print(format_roster(owner))

    print("\n🔢 Tasks across pets, sorted by priority then due time:")
    for task in scheduler.sort_by_priority():
        print(f"  {task.pet_name:<8} {task}")

    print("\n🗓️  Today's plan (explained):")
    print(scheduler.explain_plan())

    # Advanced scheduling: time-block conflict detection + next free slot.
    print("\n⚠️  Advanced scheduling checks:")
    print(f"  Conflicts in current schedule: {len(scheduler.detect_conflicts())}")

    biscuit = owner.get_pet("Biscuit")
    biscuit.add_task(Task("Vet phone call", "08:15", 20, "medium"))  # overlaps the walk
    for earlier, later in scheduler.detect_conflicts():
        print(f"  CONFLICT: {later.pet_name}'s '{later.description}' ({later.due_time}) "
              f"overlaps {earlier.pet_name}'s '{earlier.description}' ({earlier.due_time})")

    biscuit.remove_task("Vet phone call")  # drop it so it doesn't block itself
    slot = scheduler.next_available_slot(20)
    print(f"  Earliest free 20-min slot: {slot}")
    biscuit.add_task(Task("Vet phone call", slot, 20, "medium"))
    print(f"  After scheduling the call at {slot}, conflicts: {len(scheduler.detect_conflicts())}")
    biscuit.remove_task("Vet phone call")  # clean up for the sections below

    # Completing a task removes it from future plans and frees up budget.
    print("\n✅ Marking Biscuit's 'Morning walk' complete and re-planning...")
    biscuit = owner.get_pet("Biscuit")
    for task in biscuit.list_tasks():
        if task.description == "Morning walk":
            task.mark_complete()
    print(format_plan(scheduler))

    # Persistence: save the current state to JSON and load it back to prove
    # pets, tasks, and completion status survive between runs.
    print("\n💾 Persistence check:")
    save_owner(owner, DEFAULT_DATA_FILE)
    reloaded = load_owner(DEFAULT_DATA_FILE)
    walk_done = any(
        t.completed for t in reloaded.all_tasks() if t.description == "Morning walk"
    )
    print(f"Saved to {DEFAULT_DATA_FILE} and reloaded: "
          f"{len(reloaded.pets)} pets, {len(reloaded.all_tasks())} tasks, "
          f"'Morning walk' still marked complete = {walk_done}.")


if __name__ == "__main__":
    main()
