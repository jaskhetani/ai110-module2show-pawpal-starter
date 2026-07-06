"""PawPal+ core domain model.

This module implements the classes designed in ``diagrams/uml.mmd``:

* :class:`Task`  -- one pet-care activity.
* :class:`Pet`   -- a pet that owns a collection of tasks.
* :class:`Owner` -- a person who owns one or more pets and has a daily
  time budget.

The :class:`Scheduler`, which reasons across *all* of an owner's pets, is
added on top of these classes.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

# Priority labels ordered from most to least urgent, with the numeric weight
# used for sorting. Higher weight == higher priority.
PRIORITY_WEIGHTS = {"high": 3, "medium": 2, "low": 1}


def _time_to_minutes(hhmm: str) -> int:
    """Convert a 24h ``'HH:MM'`` string to minutes since midnight."""
    hours, minutes = hhmm.split(":")
    return int(hours) * 60 + int(minutes)


def _minutes_to_time(total_minutes: int) -> str:
    """Convert minutes since midnight to a zero-padded ``'HH:MM'`` string."""
    return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"


class Task:
    """A single pet-care activity (a walk, a feeding, a dose of medicine...)."""

    def __init__(
        self,
        description: str,
        due_time: str,
        duration_minutes: int,
        priority: str = "medium",
        completed: bool = False,
    ) -> None:
        self.description = description
        self.due_time = due_time  # 24h "HH:MM" string, e.g. "08:00"
        self.duration_minutes = duration_minutes
        self.priority = priority
        self.completed = completed
        # Back-reference filled in by Pet.add_task so a task can be traced to
        # its pet once the scheduler has flattened tasks across pets.
        self.pet_name: str = ""

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True

    def priority_weight(self) -> int:
        """Return the numeric weight of this task's priority (high=3 .. low=1)."""
        return PRIORITY_WEIGHTS.get(self.priority, 0)

    def to_dict(self) -> dict:
        """Serialize this task to a plain dict (``pet_name`` is re-derived on load)."""
        return {
            "description": self.description,
            "due_time": self.due_time,
            "duration_minutes": self.duration_minutes,
            "priority": self.priority,
            "completed": self.completed,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Rebuild a task from a dict produced by :meth:`to_dict`."""
        return cls(
            description=data["description"],
            due_time=data["due_time"],
            duration_minutes=data["duration_minutes"],
            priority=data.get("priority", "medium"),
            completed=data.get("completed", False),
        )

    def __str__(self) -> str:
        box = "[x]" if self.completed else "[ ]"
        return (
            f"{box} {self.description} "
            f"({self.duration_minutes} min, {self.priority}, due {self.due_time})"
        )

    def __repr__(self) -> str:  # helpful in test failure output
        return f"Task({self.description!r}, due={self.due_time!r}, priority={self.priority!r})"


class Pet:
    """A pet that owns a list of care tasks."""

    def __init__(self, name: str, species: str) -> None:
        self.name = name
        self.species = species
        self.tasks: List[Task] = []

    def add_task(self, task: Task) -> None:
        """Attach a task to this pet and stamp it with the pet's name."""
        task.pet_name = self.name
        self.tasks.append(task)

    def remove_task(self, description: str) -> bool:
        """Remove the first task matching ``description``.

        Returns ``True`` if a task was removed, ``False`` otherwise.
        """
        for task in self.tasks:
            if task.description == description:
                self.tasks.remove(task)
                return True
        return False

    def list_tasks(self) -> List[Task]:
        """Return all tasks for this pet."""
        return list(self.tasks)

    def pending_tasks(self) -> List[Task]:
        """Return only the tasks that are not yet completed."""
        return [task for task in self.tasks if not task.completed]

    def to_dict(self) -> dict:
        """Serialize this pet and its tasks to a plain dict."""
        return {
            "name": self.name,
            "species": self.species,
            "tasks": [task.to_dict() for task in self.tasks],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Pet":
        """Rebuild a pet (and its tasks) from a dict produced by :meth:`to_dict`."""
        pet = cls(data["name"], data["species"])
        for task_data in data.get("tasks", []):
            pet.add_task(Task.from_dict(task_data))
        return pet

    def __str__(self) -> str:
        return f"{self.name} ({self.species}) - {len(self.tasks)} task(s)"


class Owner:
    """A pet owner with a daily time budget and one or more pets."""

    def __init__(self, name: str, available_minutes: int = 120) -> None:
        self.name = name
        self.available_minutes = available_minutes
        self.pets: List[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        self.pets.append(pet)

    def get_pet(self, name: str) -> Optional[Pet]:
        """Return the pet with the given name, or ``None`` if not found."""
        for pet in self.pets:
            if pet.name == name:
                return pet
        return None

    def all_tasks(self) -> List[Task]:
        """Flatten every task across every pet into a single list."""
        tasks: List[Task] = []
        for pet in self.pets:
            tasks.extend(pet.tasks)
        return tasks

    def to_dict(self) -> dict:
        """Serialize this owner and all of their pets to a plain dict."""
        return {
            "name": self.name,
            "available_minutes": self.available_minutes,
            "pets": [pet.to_dict() for pet in self.pets],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Owner":
        """Rebuild an owner (and all pets/tasks) from a dict produced by :meth:`to_dict`."""
        owner = cls(data["name"], data.get("available_minutes", 120))
        for pet_data in data.get("pets", []):
            owner.add_pet(Pet.from_dict(pet_data))
        return owner

    def __str__(self) -> str:
        return f"{self.name} - {len(self.pets)} pet(s)"


class Scheduler:
    """Plans care tasks across *all* of an owner's pets.

    The scheduler is the only class that reasons over more than one pet. It
    provides two core algorithmic features -- a multi-key sort and a
    time-budget filter -- and combines them into a daily plan.
    """

    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    def sort_by_priority(self) -> List[Task]:
        """Return every pet's tasks sorted by priority, then due time.

        Highest priority first (high -> medium -> low); ties are broken by the
        earliest ``due_time``. This spans all pets via ``owner.all_tasks()``.
        """
        return sorted(
            self.owner.all_tasks(),
            key=lambda task: (-task.priority_weight(), task.due_time),
        )

    def filter_by_time_budget(self, minutes: Optional[int] = None) -> List[Task]:
        """Greedily select pending tasks that fit within a time budget.

        Walks the tasks in priority order and keeps adding them until the
        budget (defaulting to the owner's ``available_minutes``) is exhausted,
        skipping any task that no longer fits. Completed tasks are ignored.
        """
        if minutes is None:
            minutes = self.owner.available_minutes

        remaining = minutes
        selected: List[Task] = []
        for task in self.sort_by_priority():
            if task.completed:
                continue
            if task.duration_minutes <= remaining:
                selected.append(task)
                remaining -= task.duration_minutes
        return selected

    def build_daily_plan(self) -> List[Task]:
        """Return the chosen tasks for today, ordered chronologically.

        Selection is priority-driven (via :meth:`filter_by_time_budget`), but
        the returned plan is sorted by ``due_time`` so it reads like a schedule
        the owner can follow through the day.
        """
        selected = self.filter_by_time_budget(self.owner.available_minutes)
        return sorted(selected, key=lambda task: task.due_time)

    def explain_plan(self) -> str:
        """Return a human-readable daily plan plus the reasoning behind it."""
        plan = self.build_daily_plan()
        used = sum(task.duration_minutes for task in plan)

        lines = [
            f"Daily plan for {self.owner.name} "
            f"({self.owner.available_minutes} min available):"
        ]
        if not plan:
            lines.append("  (nothing fits in the available time)")
        for i, task in enumerate(plan, start=1):
            lines.append(
                f"  {i}. {task.due_time}  {task.pet_name}: {task.description} "
                f"({task.duration_minutes} min, {task.priority} priority)"
            )
        lines.append(f"  Time used: {used}/{self.owner.available_minutes} min.")

        scheduled = {id(task) for task in plan}
        skipped = [
            task
            for task in self.sort_by_priority()
            if not task.completed and id(task) not in scheduled
        ]
        if skipped:
            lines.append("  Skipped (over budget):")
            for task in skipped:
                lines.append(
                    f"    - {task.pet_name}: {task.description} "
                    f"({task.duration_minutes} min, {task.priority})"
                )
        return "\n".join(lines)

    def _time_blocks(self) -> List[tuple]:
        """Return ``(start_min, end_min, task)`` tuples for pending tasks.

        Each pending task occupies the block that begins at its ``due_time``
        and lasts ``duration_minutes``. Sorted by start time; spans all pets.
        """
        blocks = []
        for task in self.owner.all_tasks():
            if task.completed:
                continue
            start = _time_to_minutes(task.due_time)
            blocks.append((start, start + task.duration_minutes, task))
        return sorted(blocks, key=lambda block: block[0])

    def detect_conflicts(self) -> List[tuple]:
        """Return ``(earlier_task, later_task)`` pairs whose time blocks overlap.

        Works across every pet, so it flags when the owner would have to be in
        two places at once (e.g. walking the dog and medicating the cat at the
        same time).
        """
        blocks = self._time_blocks()
        conflicts: List[tuple] = []
        for i, (_, a_end, a_task) in enumerate(blocks):
            for b_start, _, b_task in blocks[i + 1:]:
                if b_start < a_end:
                    conflicts.append((a_task, b_task))
                else:
                    break  # sorted by start, so nothing later can overlap a
        return conflicts

    def next_available_slot(
        self,
        duration_minutes: int,
        day_start: str = "07:00",
        day_end: str = "21:00",
    ) -> Optional[str]:
        """Return the earliest ``'HH:MM'`` start where a task of this length fits.

        Scans the free gaps between existing pending time blocks (across all
        pets) inside ``[day_start, day_end)``. Returns ``None`` if no gap is
        large enough.
        """
        cursor = _time_to_minutes(day_start)
        end_bound = _time_to_minutes(day_end)
        for b_start, b_end, _ in self._time_blocks():
            if b_end <= cursor:
                continue
            if b_start - cursor >= duration_minutes:
                return _minutes_to_time(cursor)
            cursor = max(cursor, b_end)
        if end_bound - cursor >= duration_minutes:
            return _minutes_to_time(cursor)
        return None


# --- Persistence -----------------------------------------------------------
# JSON save/load so an owner's pets and tasks survive between application runs.

DEFAULT_DATA_FILE = "pawpal_data.json"


def save_owner(owner: Owner, path: str = DEFAULT_DATA_FILE) -> None:
    """Write an owner (with all pets and tasks) to a JSON file."""
    Path(path).write_text(json.dumps(owner.to_dict(), indent=2), encoding="utf-8")


def load_owner(path: str = DEFAULT_DATA_FILE) -> Optional[Owner]:
    """Load an owner from a JSON file, or return ``None`` if it does not exist."""
    data_path = Path(path)
    if not data_path.exists():
        return None
    data = json.loads(data_path.read_text(encoding="utf-8"))
    return Owner.from_dict(data)
