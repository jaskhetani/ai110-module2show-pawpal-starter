"""Tests for the PawPal+ system.

Run from the project root with:

    pytest
"""

import pytest

from pawpal_system import Owner, Pet, Scheduler, Task, load_owner, save_owner


@pytest.fixture
def owner() -> Owner:
    """A small two-pet, four-task owner used across several tests."""
    o = Owner("Test", available_minutes=60)

    dog = Pet("Rex", "dog")
    dog.add_task(Task("Walk", "08:00", 30, "high"))
    dog.add_task(Task("Play", "17:00", 20, "low"))

    cat = Pet("Tom", "cat")
    cat.add_task(Task("Meds", "09:00", 10, "high"))
    cat.add_task(Task("Brush", "19:00", 15, "medium"))

    o.add_pet(dog)
    o.add_pet(cat)
    return o


# --- Task ------------------------------------------------------------------

def test_mark_complete_flips_status():
    task = Task("Walk", "08:00", 30, "high")
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_priority_weight_ranks_high_above_low():
    assert Task("a", "08:00", 5, "high").priority_weight() == 3
    assert Task("b", "08:00", 5, "medium").priority_weight() == 2
    assert Task("c", "08:00", 5, "low").priority_weight() == 1
    # Unknown priority falls back to 0 rather than raising.
    assert Task("d", "08:00", 5, "bogus").priority_weight() == 0


# --- Pet / Owner -----------------------------------------------------------

def test_add_task_stamps_pet_name():
    pet = Pet("Rex", "dog")
    task = Task("Walk", "08:00", 30, "high")
    pet.add_task(task)
    assert task.pet_name == "Rex"


def test_pending_tasks_excludes_completed():
    pet = Pet("Rex", "dog")
    pet.add_task(Task("Walk", "08:00", 30, "high"))
    pet.add_task(Task("Play", "17:00", 20, "low"))
    pet.list_tasks()[0].mark_complete()
    pending = pet.pending_tasks()
    assert len(pending) == 1
    assert pending[0].description == "Play"


def test_owner_all_tasks_spans_every_pet(owner):
    tasks = owner.all_tasks()
    assert len(tasks) == 4
    pet_names = {task.pet_name for task in tasks}
    assert pet_names == {"Rex", "Tom"}


# --- Scheduler: sorting ----------------------------------------------------

def test_sort_by_priority_orders_high_first_across_pets(owner):
    ordered = Scheduler(owner).sort_by_priority()
    assert [t.description for t in ordered] == ["Walk", "Meds", "Brush", "Play"]
    # The two highest-priority tasks come from two different pets.
    assert {ordered[0].pet_name, ordered[1].pet_name} == {"Rex", "Tom"}


def test_sort_by_priority_breaks_ties_by_due_time(owner):
    ordered = Scheduler(owner).sort_by_priority()
    walk, meds = ordered[0], ordered[1]
    assert walk.priority == meds.priority == "high"
    assert walk.due_time < meds.due_time  # 08:00 before 09:00


# --- Scheduler: filtering / planning --------------------------------------

def test_filter_respects_time_budget(owner):
    selected = Scheduler(owner).filter_by_time_budget(60)
    total = sum(t.duration_minutes for t in selected)
    assert total <= 60
    # The low-priority 20-min "Play" cannot fit after the higher-priority work.
    assert "Play" not in [t.description for t in selected]
    assert [t.description for t in selected] == ["Walk", "Meds", "Brush"]


def test_build_daily_plan_is_chronological(owner):
    plan = Scheduler(owner).build_daily_plan()
    due_times = [t.due_time for t in plan]
    assert due_times == sorted(due_times)


def test_completed_tasks_free_budget_for_others(owner):
    scheduler = Scheduler(owner)
    # Before: the 20-min low-priority Play does not make the cut.
    assert "Play" not in [t.description for t in scheduler.build_daily_plan()]

    # Completing the 30-min Walk frees enough budget for Play to fit.
    owner.get_pet("Rex").list_tasks()[0].mark_complete()
    replanned = [t.description for t in scheduler.build_daily_plan()]
    assert "Walk" not in replanned
    assert "Play" in replanned


# --- Persistence -----------------------------------------------------------

def test_owner_dict_round_trip_preserves_data(owner):
    owner.get_pet("Rex").list_tasks()[0].mark_complete()  # Walk -> completed
    clone = Owner.from_dict(owner.to_dict())

    assert clone.name == owner.name
    assert clone.available_minutes == owner.available_minutes
    assert len(clone.pets) == len(owner.pets)
    assert len(clone.all_tasks()) == len(owner.all_tasks())

    # Completion status and the pet back-reference survive the round trip.
    walk = next(t for t in clone.all_tasks() if t.description == "Walk")
    assert walk.completed is True
    assert walk.pet_name == "Rex"


def test_save_and_load_owner_from_file(owner, tmp_path):
    path = tmp_path / "data.json"
    save_owner(owner, str(path))
    loaded = load_owner(str(path))

    assert loaded is not None
    assert [p.name for p in loaded.pets] == [p.name for p in owner.pets]
    assert len(loaded.all_tasks()) == 4


def test_load_owner_missing_file_returns_none(tmp_path):
    assert load_owner(str(tmp_path / "does_not_exist.json")) is None
