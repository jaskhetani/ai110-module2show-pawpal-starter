"""Presentation helpers for PawPal+ CLI output.

Uses the third-party ``tabulate`` library plus a few emoji to render the roster
and the daily plan as clean tables. Kept separate from ``pawpal_system.py`` so
the core domain logic stays free of any presentation concerns.
"""

from tabulate import tabulate

from pawpal_system import Owner, Scheduler

# Emoji used to make priority and species scannable at a glance.
PRIORITY_EMOJI = {"high": "🔴", "medium": "🟡", "low": "🟢"}
SPECIES_EMOJI = {"dog": "🐕", "cat": "🐈"}

TABLE_FORMAT = "rounded_outline"


def _priority_cell(priority: str) -> str:
    return f"{PRIORITY_EMOJI.get(priority, '')} {priority}".strip()


def format_roster(owner: Owner) -> str:
    """Render an owner's pets and their tasks as a table."""
    rows = []
    for pet in owner.pets:
        icon = SPECIES_EMOJI.get(pet.species, "🐾")
        for task in pet.list_tasks():
            rows.append([
                f"{icon} {pet.name}",
                task.description,
                task.due_time,
                f"{task.duration_minutes} min",
                _priority_cell(task.priority),
                "✅" if task.completed else "⬜",
            ])
    headers = ["Pet", "Task", "Due", "Duration", "Priority", "Done"]
    return tabulate(rows, headers=headers, tablefmt=TABLE_FORMAT)


def format_plan(scheduler: Scheduler) -> str:
    """Render the scheduler's daily plan as a numbered table with a time footer."""
    plan = scheduler.build_daily_plan()
    rows = [
        [
            i,
            task.due_time,
            task.pet_name,
            task.description,
            f"{task.duration_minutes} min",
            _priority_cell(task.priority),
        ]
        for i, task in enumerate(plan, start=1)
    ]
    headers = ["#", "Time", "Pet", "Task", "Duration", "Priority"]
    table = tabulate(rows, headers=headers, tablefmt=TABLE_FORMAT)
    used = sum(task.duration_minutes for task in plan)
    return f"{table}\n⏱️  {used}/{scheduler.owner.available_minutes} min used"
