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

from typing import List, Optional

# Priority labels ordered from most to least urgent, with the numeric weight
# used for sorting. Higher weight == higher priority.
PRIORITY_WEIGHTS = {"high": 3, "medium": 2, "low": 1}


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

    def __str__(self) -> str:
        return f"{self.name} - {len(self.pets)} pet(s)"
