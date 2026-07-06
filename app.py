"""PawPal+ interactive Streamlit UI.

This app is wired to the same backend the CLI demo uses: `pawpal_system.py`
(Owner / Pet / Task / Scheduler) plus the JSON persistence helpers. Run with:

    streamlit run app.py
"""

import re

import streamlit as st

from pawpal_system import (
    DEFAULT_DATA_FILE,
    Owner,
    Pet,
    Scheduler,
    Task,
    load_owner,
    save_owner,
)

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

PRIORITY_EMOJI = {"high": "🔴", "medium": "🟡", "low": "🟢"}
SPECIES_EMOJI = {"dog": "🐕", "cat": "🐈", "other": "🐾"}
TIME_RE = re.compile(r"^([01]?\d|2[0-3]):[0-5]\d$")  # 24h HH:MM


def _demo_owner() -> Owner:
    """Build a sample owner with two pets and seven tasks (mirrors the CLI demo)."""
    owner = Owner("Jordan", available_minutes=120)

    biscuit = Pet("Biscuit", "dog")
    for task in [
        Task("Breakfast", "07:30", 10, "high"),
        Task("Morning walk", "08:00", 30, "high"),
        Task("Fetch / enrichment", "16:00", 25, "low"),
        Task("Evening walk", "18:00", 30, "medium"),
    ]:
        biscuit.add_task(task)

    mochi = Pet("Mochi", "cat")
    for task in [
        Task("Litter cleanup", "07:45", 10, "medium"),
        Task("Thyroid meds", "09:00", 5, "high"),
        Task("Brush coat", "19:00", 15, "low"),
    ]:
        mochi.add_task(task)

    owner.add_pet(biscuit)
    owner.add_pet(mochi)
    return owner


# --- Session state: hold one Owner across reruns --------------------------
if "owner" not in st.session_state:
    st.session_state.owner = Owner("Jordan", available_minutes=120)
owner: Owner = st.session_state.owner

st.title("🐾 PawPal+")
st.caption("Plan daily care tasks across all of your pets.")

# --- Sidebar: owner settings, demo data, persistence ----------------------
with st.sidebar:
    st.header("Owner")
    owner.name = st.text_input("Owner name", value=owner.name)
    owner.available_minutes = int(
        st.number_input(
            "Daily time budget (min)",
            min_value=0,
            max_value=1440,
            value=int(owner.available_minutes),
            step=15,
        )
    )

    st.divider()
    if st.button("Load demo data", use_container_width=True):
        st.session_state.owner = _demo_owner()
        st.rerun()
    if st.button("Reset (empty)", use_container_width=True):
        st.session_state.owner = Owner(owner.name, available_minutes=owner.available_minutes)
        st.rerun()

    st.divider()
    st.subheader("Persistence")
    if st.button("💾 Save to JSON", use_container_width=True):
        save_owner(owner, DEFAULT_DATA_FILE)
        st.success(f"Saved to {DEFAULT_DATA_FILE}")
    if st.button("📂 Load from JSON", use_container_width=True):
        loaded = load_owner(DEFAULT_DATA_FILE)
        if loaded is None:
            st.warning(f"No {DEFAULT_DATA_FILE} found yet.")
        else:
            st.session_state.owner = loaded
            st.rerun()

# --- 1) Add a pet ---------------------------------------------------------
st.subheader("1) Pets")
with st.form("add_pet", clear_on_submit=True):
    c1, c2 = st.columns([2, 1])
    new_pet = c1.text_input("Pet name")
    species = c2.selectbox("Species", ["dog", "cat", "other"])
    if st.form_submit_button("Add pet"):
        if not new_pet.strip():
            st.warning("Enter a pet name.")
        elif owner.get_pet(new_pet.strip()):
            st.warning(f"{new_pet.strip()} already exists.")
        else:
            owner.add_pet(Pet(new_pet.strip(), species))
            st.rerun()

if not owner.pets:
    st.info("No pets yet — add one above or click **Load demo data** in the sidebar.")
    st.stop()

# --- 2) Add a task --------------------------------------------------------
st.subheader("2) Tasks")
with st.form("add_task", clear_on_submit=True):
    c1, c2 = st.columns([1, 2])
    target = c1.selectbox("Pet", [pet.name for pet in owner.pets])
    desc = c2.text_input("Task description")
    c3, c4, c5 = st.columns(3)
    due = c3.text_input("Due time (HH:MM)", value="08:00")
    duration = c4.number_input("Duration (min)", min_value=1, max_value=240, value=20)
    priority = c5.selectbox("Priority", ["high", "medium", "low"], index=1)
    if st.form_submit_button("Add task"):
        if not desc.strip():
            st.warning("Enter a task description.")
        elif not TIME_RE.match(due.strip()):
            st.warning("Due time must be 24h HH:MM, e.g. 08:00.")
        else:
            owner.get_pet(target).add_task(
                Task(desc.strip(), due.strip(), int(duration), priority)
            )
            st.rerun()

# --- 3) Roster ------------------------------------------------------------
st.subheader("3) Care roster")
roster = [
    {
        "Pet": f"{SPECIES_EMOJI.get(pet.species, '🐾')} {pet.name}",
        "Task": task.description,
        "Due": task.due_time,
        "Duration": f"{task.duration_minutes} min",
        "Priority": f"{PRIORITY_EMOJI.get(task.priority, '')} {task.priority}",
        "Done": "✅" if task.completed else "⬜",
    }
    for pet in owner.pets
    for task in pet.list_tasks()
]
if roster:
    st.table(roster)
else:
    st.info("No tasks yet. Add one above.")

# Mark a pending task complete.
pending = [(pet, task) for pet in owner.pets for task in pet.pending_tasks()]
if pending:
    labels = [f"{pet.name}: {task.description} (due {task.due_time})" for pet, task in pending]
    choice = st.selectbox("Mark a task complete", ["—"] + labels)
    if st.button("Mark complete") and choice != "—":
        pending[labels.index(choice)][1].mark_complete()
        st.rerun()

# --- 4) Daily plan --------------------------------------------------------
st.subheader("4) Daily plan")
scheduler = Scheduler(owner)
if st.button("🗓️ Generate daily plan", type="primary"):
    st.markdown("**Tasks sorted by priority (across pets):**")
    st.table([
        {
            "Pet": task.pet_name,
            "Task": task.description,
            "Due": task.due_time,
            "Priority": f"{PRIORITY_EMOJI.get(task.priority, '')} {task.priority}",
        }
        for task in scheduler.sort_by_priority()
    ])

    st.markdown("**Plan for the day (fit into the time budget):**")
    st.code(scheduler.explain_plan(), language="text")

    conflicts = scheduler.detect_conflicts()
    if conflicts:
        st.warning(f"⚠️ {len(conflicts)} time conflict(s) detected:")
        for earlier, later in conflicts:
            st.write(
                f"- **{later.pet_name}: {later.description}** ({later.due_time}) overlaps "
                f"**{earlier.pet_name}: {earlier.description}** ({earlier.due_time})"
            )
    else:
        st.success("✅ No time conflicts in the current schedule.")

# --- 5) Next available slot -----------------------------------------------
st.subheader("5) Find a free slot")
c1, c2 = st.columns([1, 2])
slot_len = c1.number_input("Duration to fit (min)", min_value=1, max_value=240, value=30)
if c2.button("Find earliest free slot"):
    slot = Scheduler(owner).next_available_slot(int(slot_len))
    if slot is None:
        st.warning("No free slot large enough between 07:00 and 21:00.")
    else:
        st.info(f"Earliest free {int(slot_len)}-min slot: **{slot}**")
