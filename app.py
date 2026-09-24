"""PawPal+ Streamlit front end.

The thinking lives in pawpal_system.py: a User owns pets and tasks, asks for two
candidate Schedules under different strategies, compares them, and saves one. This
file is only the surface -- it collects input, calls those methods, and prints what
they hand back. No scheduling decisions are made here.
"""

from datetime import time

import streamlit as st

from pawpal_system import Task, User, to_minutes

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")

# "as-entered" is not a real strategy name -- sort_by_strategy leaves any name it
# does not recognise in the order the tasks came in, which is worth being able to see
STRATEGIES = ["priority", "shortest", "longest", "earliest", "as-entered"]

CATEGORIES = [
    "feeding",
    "exercise",
    "medicine",
    "grooming",
    "cleaning",
    "enrichment",
    "vet",
    "errand",
    "other",
]

SPECIES = ["dog", "cat", "bird", "reptile", "other"]

# time widgets move in 5-minute steps to match SEARCH_STEP, the grain the scheduler
# slides a task by when a slot is taken
STEP = 300


# ---------------------------------------------------------------- state and helpers


def demo_owner() -> "User":
    """Build an owner with two pets, a fixed work block, and a dependency, so the
    app has something to plan on first load and every feature has an example."""
    owner = User("Jordan", time(7, 0), time(20, 0))
    mochi = owner.add_pet("pet_1", "Mochi", "dog", 3, "pulls on the leash")
    nori = owner.add_pet("pet_2", "Nori", "cat", 2, "needs meds with food")

    owner.add_task(
        Task("task_1", "Feed Mochi breakfast", "feeding", 5, 15, time(7, 0), pets=[mochi])
    )
    owner.add_task(
        Task("task_2", "Walk Mochi", "exercise", 4, 45, time(7, 30), pets=[mochi])
    )
    owner.add_task(Task("task_3", "Feed Nori", "feeding", 5, 10, time(7, 0), pets=[nori]))
    owner.add_task(
        Task("task_4", "Give Nori her medicine", "medicine", 5, 5, pets=[nori])
    )
    owner.add_task(Task("task_5", "Clean the litter box", "cleaning", 2, 10, pets=[nori]))
    owner.add_task(
        Task("task_6", "Vet call about Mochi", "vet", 4, 20, time(10, 0), time(11, 0))
    )
    owner.add_task(Task("task_7", "Buy pet food", "errand", 2, 55))

    owner.add_event("Work", time(9, 0), time(17, 0))
    # medicine goes with food, so it cannot be placed until breakfast is placed
    owner.set_dependency("task_4", "task_3")
    return owner


def get_owner() -> "User":
    """Return the one User the whole page works on, creating the demo owner the
    first time. Streamlit reruns this file top to bottom on every click, so the
    owner has to live in session_state or every edit would be forgotten."""
    if "owner" not in st.session_state:
        st.session_state.owner = demo_owner()
    return st.session_state.owner


def replace_owner(owner: "User") -> None:
    """Swap in a different owner and forget the sidebar widget values, so the new
    owner's name and awake window show instead of the old owner's."""
    st.session_state.owner = owner
    for key in ("owner_name", "wake_time", "sleep_time"):
        st.session_state.pop(key, None)


def flash(kind: str, text: str) -> None:
    """Queue a message to show after the rerun. An edit is followed by a rerun so
    the tables redraw, and anything written before that rerun would be wiped, so
    the message waits in session_state instead."""
    st.session_state.flash = (kind, text)


def show_flash() -> None:
    """Print and clear the queued message, if there is one."""
    if "flash" not in st.session_state:
        return
    kind, text = st.session_state.pop("flash")
    {"ok": st.success, "warn": st.warning, "err": st.error}[kind](text)


def next_pet_id(owner: "User") -> str:
    """Suggest an unused pet id, skipping over ids already taken so deleting and
    re-adding does not collide."""
    number = len(owner.pets) + 1
    while owner.get_pet(f"pet_{number}") is not None:
        number += 1
    return f"pet_{number}"


def next_task_id(owner: "User") -> str:
    """Suggest an unused task id, the same way User.add_event names its events."""
    number = len(owner.tasks) + 1
    while owner.get_task(f"task_{number}") is not None:
        number += 1
    return f"task_{number}"


def clock(moment: "time | None") -> str:
    """Format a time for a table, or a dash if there is none."""
    return moment.strftime("%H:%M") if moment is not None else "--"


def window_label(start: "time | None", end: "time | None") -> str:
    """Describe a task's time preference in one cell: a window, an 'at or after'
    time, or nothing asked for."""
    if start is None and end is None:
        return "any time"
    if end is None:
        return f"{clock(start)} onwards"
    if start is None:
        return f"by {clock(end)}"
    return f"{clock(start)}-{clock(end)}"


def pet_rows(pets: list) -> list[dict]:
    """Turn pets into table rows."""
    return [
        {
            "id": pet.pet_id,
            "name": pet.name,
            "species": pet.species,
            "age": pet.age,
            "notes": pet.notes or "--",
        }
        for pet in pets
    ]


def task_rows(tasks: list) -> list[dict]:
    """Turn tasks into table rows, leaning on the Task methods for the derived
    columns rather than re-deriving them here."""
    return [
        {
            "id": task.task_id,
            "title": task.title,
            "category": task.category,
            "priority": task.priority,
            "minutes": task.duration_minutes,
            "preferred": window_label(task.preferred_start, task.preferred_end),
            "fixed": "yes" if task.is_fixed else "",
            "pets": ", ".join(task.pet_names()) if task.is_pet_task() else "--",
            "after": ", ".join(task.depends_on) if task.has_dependencies() else "--",
        }
        for task in tasks
    ]


def placement_rows(schedule, tasks: list) -> list[dict]:
    """Turn placed tasks into table rows with the times they were given."""
    rows = []
    for task in tasks:
        placement = schedule.get_placement(task.task_id)
        rows.append(
            {
                "start": clock(placement[0]) if placement else "--",
                "end": clock(placement[1]) if placement else "--",
                "task": task.title,
                "pets": ", ".join(task.pet_names()) if task.is_pet_task() else "--",
                "priority": task.priority,
            }
        )
    return rows


def table(rows: list[dict], empty_message: str) -> None:
    """Draw a table, or say why it is empty. st.table cannot render an empty list."""
    if rows:
        st.dataframe(rows, hide_index=True, width="stretch")
    else:
        st.caption(empty_message)


def task_label(owner: "User", task_id: str) -> str:
    """Label a task in a dropdown: the id is what the backend works in, the title is
    what the user recognises. Falls back to the bare id for a task that has since
    been deleted but still appears in an already-built plan."""
    task = owner.get_task(task_id)
    return f"{task_id} -- {task.title}" if task is not None else task_id


def pick_task_id(
    owner: "User", label: str, key: str, tasks: list | None = None
) -> "str | None":
    """Show a task dropdown and return the chosen task's id, or None if there is
    nothing to choose from. Every dropdown in this app offers ids rather than the
    objects themselves: Streamlit copies whatever it stores for a widget, so a Task
    handed to a widget comes back a copy, and editing that copy would change
    nothing. An id always leads back to the real task through owner.get_task."""
    choices = tasks if tasks is not None else owner.tasks
    if not choices:
        return None
    return st.selectbox(
        label,
        [task.task_id for task in choices],
        format_func=lambda task_id: task_label(owner, task_id),
        key=key,
    )


def pick_pet_id(owner: "User", label: str, key: str) -> "str | None":
    """Show a pet dropdown and return the chosen pet's id, for the same reason
    pick_task_id deals in ids."""
    if not owner.pets:
        return None
    return st.selectbox(
        label,
        [pet.pet_id for pet in owner.pets],
        format_func=lambda pet_id: owner.get_pet(pet_id).name,
        key=key,
    )


# --------------------------------------------------------------------------- header

owner = get_owner()

st.title("🐾 PawPal+")
st.caption(
    "Add your pets and what their day needs, then ask for two plans and keep the one "
    "that fits more in."
)
show_flash()


# -------------------------------------------------------------------------- sidebar

with st.sidebar:
    st.header("Owner")
    owner.name = st.text_input("Name", value=owner.name, key="owner_name")

    st.subheader("Awake window")
    st.caption("The scheduler only places tasks between these two times.")
    owner.wake_time = st.time_input(
        "Wake time", value=owner.wake_time, step=STEP, key="wake_time"
    )
    owner.sleep_time = st.time_input(
        "Sleep time", value=owner.sleep_time, step=STEP, key="sleep_time"
    )

    # the same pair the scheduler will be handed, read back through the accessor
    wake_time, sleep_time = owner.awake_window()
    awake_minutes = to_minutes(sleep_time) - to_minutes(wake_time)
    if awake_minutes <= 0:
        # the scheduler assumes a day that does not cross midnight, so it cannot
        # place anything in a window that ends before it starts
        st.error("Sleep time has to come after wake time, or nothing can be planned.")
    else:
        st.metric("Hours awake", f"{awake_minutes // 60}h {awake_minutes % 60:02d}m")

    booked = sum(task.duration_minutes for task in owner.tasks)
    st.metric("Minutes of tasks added", booked)
    if booked > awake_minutes > 0:
        st.warning("More tasks than hours -- expect some to be left out of a plan.")

    st.divider()
    st.subheader("Start over")
    if st.button("Load the demo day", width="stretch"):
        replace_owner(demo_owner())
        flash("ok", "Loaded the demo day.")
        st.rerun()
    if st.button("Empty everything", width="stretch"):
        replace_owner(User("Owner", time(7, 0), time(21, 0)))
        flash("ok", "Cleared the pets, tasks, and plans.")
        st.rerun()


pets_tab, tasks_tab, deps_tab, plans_tab, day_tab = st.tabs(
    ["🐕 Pets", "✅ Tasks", "🔗 Order", "📅 Plans", "🔍 Day view"]
)


# ----------------------------------------------------------------------- pets tab

with pets_tab:
    st.subheader("Pets")
    table(pet_rows(owner.pets), "No pets yet. Add one below.")

    left, right = st.columns(2)

    with left:
        st.markdown("**Add a pet**")
        with st.form("add_pet", clear_on_submit=True):
            pet_id = st.text_input("Pet id", value=next_pet_id(owner))
            name = st.text_input("Name")
            species = st.selectbox("Species", SPECIES)
            age = st.number_input("Age", min_value=0, max_value=40, value=1, step=1)
            notes = st.text_area("Notes", placeholder="anything the plan should know")
            if st.form_submit_button("Add pet"):
                if not name.strip():
                    flash("err", "A pet needs a name.")
                else:
                    try:
                        owner.add_pet(pet_id.strip(), name.strip(), species, int(age), notes.strip())
                        flash("ok", f"Added {name.strip()}.")
                    except ValueError as problem:
                        # add_pet refuses a duplicate id, since get_pet could not
                        # then tell the two pets apart
                        flash("err", str(problem))
                st.rerun()

    with right:
        st.markdown("**What each pet needs**")
        if owner.pets:
            # tasks_by_pet gives every pet a key, so a pet with nothing to do shows
            # an empty day instead of vanishing from this view
            for owned_id, pet_tasks in owner.tasks_by_pet().items():
                pet = owner.get_pet(owned_id)
                with st.expander(f"{pet.name} ({pet.species}) -- {len(pet_tasks)} tasks"):
                    table(task_rows(pet_tasks), f"Nothing scheduled for {pet.name} yet.")
        else:
            st.caption("Add a pet to see its tasks grouped here.")

        st.markdown("**By species**")
        if owner.pets:
            # a shared task counts once per species, not once per pet
            species_choice = st.selectbox(
                "Species",
                sorted({pet.species for pet in owner.pets}),
                key="species_view",
            )
            table(
                task_rows(owner.tasks_for_species(species_choice)),
                f"No tasks for any {species_choice}.",
            )
        else:
            st.caption("Add a pet to filter tasks by species.")

        st.markdown("**Your own tasks**")
        table(task_rows(owner.personal_tasks()), "Nothing that is not for a pet.")


# ---------------------------------------------------------------------- tasks tab

with tasks_tab:
    st.subheader("Tasks")
    table(task_rows(owner.tasks), "No tasks yet. Add one below.")

    add_col, event_col = st.columns(2)

    with add_col:
        st.markdown("**Add a task**")
        with st.form("add_task", clear_on_submit=True):
            task_id = st.text_input("Task id", value=next_task_id(owner))
            title = st.text_input("Title", placeholder="Walk Mochi")
            category = st.selectbox("Category", CATEGORIES)
            priority = st.slider(
                "Priority", 1, 5, 3, help="5 matters most. The priority strategy sorts on this."
            )
            duration = st.number_input(
                "Duration (minutes)", min_value=5, max_value=480, value=20, step=5
            )
            pet_choices = st.multiselect(
                "For which pets?",
                [pet.pet_id for pet in owner.pets],
                format_func=lambda pet_id: owner.get_pet(pet_id).name,
                help="Leave empty for one of your own tasks.",
            )

            st.markdown("Time preference")
            wants_window = st.checkbox("This should happen at a particular time")
            pref_start = st.time_input("Preferred start", value=time(8, 0), step=STEP)
            use_end = st.checkbox("Also cap how late it can run", value=False)
            pref_end = st.time_input("Latest end", value=time(9, 0), step=STEP)
            is_fixed = st.checkbox(
                "Fixed -- cannot be moved",
                help="A fixed task goes exactly where you pin it or not at all.",
            )

            if st.form_submit_button("Add task"):
                start = pref_start if wants_window else None
                end = pref_end if (wants_window and use_end) else None
                if not title.strip():
                    flash("err", "A task needs a title.")
                elif is_fixed and start is None:
                    # place_task has nowhere to pin a fixed task without a start
                    flash("err", "A fixed task needs a preferred start time.")
                elif end is not None and to_minutes(end) <= to_minutes(start):
                    flash("err", "The latest end has to come after the preferred start.")
                else:
                    try:
                        owner.add_task(
                            Task(
                                task_id=task_id.strip(),
                                title=title.strip(),
                                category=category,
                                priority=int(priority),
                                duration_minutes=int(duration),
                                preferred_start=start,
                                preferred_end=end,
                                is_fixed=is_fixed,
                                # the real Pet objects, looked back up from the ids
                                # the dropdown works in
                                pets=[owner.get_pet(pet_id) for pet_id in pet_choices],
                            )
                        )
                        flash("ok", f"Added {title.strip()}.")
                    except ValueError as problem:
                        # two tasks sharing an id would overwrite each other's slot
                        flash("err", str(problem))
                st.rerun()

    with event_col:
        st.markdown("**Add a fixed commitment**")
        st.caption(
            "Work, class, an appointment -- something the plan has to work around "
            "rather than move."
        )
        with st.form("add_event", clear_on_submit=True):
            event_title = st.text_input("What is it?", placeholder="Work")
            event_start = st.time_input("Starts", value=time(9, 0), step=STEP)
            event_end = st.time_input("Ends", value=time(17, 0), step=STEP)
            if st.form_submit_button("Add commitment"):
                if not event_title.strip():
                    flash("err", "A commitment needs a name.")
                elif to_minutes(event_end) <= to_minutes(event_start):
                    flash("err", "A commitment has to end after it starts.")
                else:
                    owner.add_event(event_title.strip(), event_start, event_end)
                    flash("ok", f"Added {event_title.strip()}.")
                st.rerun()

        st.markdown("**Change a task**")
        edit_id = pick_task_id(owner, "Task to change", "edit_task")
        edit_task = owner.get_task(edit_id) if edit_id is not None else None
        if edit_task is None:
            st.caption("Add a task first.")
        else:
            st.caption(edit_task.describe())

            # the keys carry the task id, so each task keeps its own widget state.
            # With one shared key Streamlit would hold on to the last task's values
            # and offer them for the next task the user picks.
            suffix = edit_task.task_id
            new_priority = st.slider(
                "Priority", 1, 5, edit_task.priority, key=f"edit_priority_{suffix}"
            )
            if st.button("Save priority"):
                owner.set_priority(edit_task.task_id, int(new_priority))
                flash("ok", f"{edit_task.title} is now priority {int(new_priority)}.")
                st.rerun()

            new_duration = st.number_input(
                "Duration (minutes)",
                min_value=5,
                max_value=480,
                value=edit_task.duration_minutes,
                step=5,
                key=f"edit_duration_{suffix}",
            )
            keep_window = st.checkbox(
                "Keep a preferred window",
                value=edit_task.preferred_start is not None,
                key=f"edit_keep_window_{suffix}",
            )
            edit_start = st.time_input(
                "Preferred start",
                value=edit_task.preferred_start or time(8, 0),
                step=STEP,
                key=f"edit_start_{suffix}",
            )
            edit_end = st.time_input(
                "Latest end",
                value=edit_task.preferred_end or time(9, 0),
                step=STEP,
                key=f"edit_end_{suffix}",
            )
            cap_end = st.checkbox(
                "Use that latest end",
                value=edit_task.preferred_end is not None,
                key=f"edit_cap_end_{suffix}",
            )
            if st.button("Save time preference"):
                window = (edit_start, edit_end if cap_end else None) if keep_window else (None, None)
                if window[0] is not None and window[1] is not None and to_minutes(window[1]) <= to_minutes(window[0]):
                    flash("err", "The latest end has to come after the preferred start.")
                elif edit_task.is_fixed and window[0] is None:
                    flash("err", "A fixed task cannot give up its start time.")
                else:
                    owner.set_time_preference(edit_task.task_id, window, int(new_duration))
                    flash("ok", f"Updated when {edit_task.title} should happen.")
                st.rerun()

            link_pet_id = pick_pet_id(owner, "Pet to link or unlink", "link_pet")
            if link_pet_id is not None:
                link_pet = owner.get_pet(link_pet_id)
                link_col, unlink_col = st.columns(2)
                if link_col.button("Link pet", width="stretch"):
                    # one walk or vet trip can cover more than one animal
                    edit_task.add_pet(link_pet)
                    flash("ok", f"{link_pet.name} is now part of {edit_task.title}.")
                    st.rerun()
                if unlink_col.button("Unlink pet", width="stretch"):
                    edit_task.remove_pet(link_pet.pet_id)
                    flash("ok", f"{link_pet.name} is no longer part of {edit_task.title}.")
                    st.rerun()

            if st.button("Delete this task", type="secondary"):
                # delete_task also clears the id out of every other task's
                # depends_on, so nothing is left waiting on a task that is gone
                owner.delete_task(edit_task.task_id)
                flash("ok", f"Deleted {edit_task.title}.")
                st.rerun()


# ----------------------------------------------------------------------- order tab

with deps_tab:
    st.subheader("What has to happen first")
    st.caption(
        "Medicine after food, a walk after breakfast. A task that depends on another "
        "is never placed before it, and is left out entirely if the task it waits on "
        "could not be placed."
    )

    if len(owner.tasks) < 2:
        st.info("Add at least two tasks to put them in order.")
    else:
        pick_col, show_col = st.columns(2)

        with pick_col:
            st.markdown("**Add a rule**")
            later_id = pick_task_id(owner, "This task", "dep_later")
            later = owner.get_task(later_id)
            earlier_id = pick_task_id(
                owner,
                "...comes after this one",
                "dep_earlier",
                # a task cannot come after itself, so it is not offered as its own
                # prerequisite
                tasks=[task for task in owner.tasks if task.task_id != later_id],
            )
            earlier = owner.get_task(earlier_id) if earlier_id is not None else None
            if later is not None and earlier is not None and st.button("Add rule"):
                try:
                    owner.set_dependency(later.task_id, earlier.task_id)
                    flash("ok", f"{later.title} now comes after {earlier.title}.")
                except ValueError as problem:
                    # set_dependency refuses a link that would close a loop, which
                    # would leave both tasks permanently unplaceable
                    flash("err", str(problem))
                st.rerun()

        with show_col:
            st.markdown("**Rules on this task**")
            if later is not None:
                prerequisites = owner.dependencies_of(later.task_id)
                if prerequisites:
                    for prerequisite in prerequisites:
                        row, button = st.columns([3, 1])
                        row.write(f"{later.title} waits on **{prerequisite.title}**")
                        if button.button("Remove", key=f"clear_{prerequisite.task_id}"):
                            owner.clear_dependency(later.task_id, prerequisite.task_id)
                            flash("ok", f"{later.title} no longer waits on {prerequisite.title}.")
                            st.rerun()
                else:
                    st.caption(f"{later.title} can be placed whenever it fits.")

        st.markdown("**Everything with an order rule**")
        table(
            task_rows([task for task in owner.tasks if task.has_dependencies()]),
            "No ordering rules yet.",
        )


# ----------------------------------------------------------------------- plans tab

with plans_tab:
    st.subheader("Plans")
    st.caption(
        "Build one plan, then an alternative under a different strategy, and compare "
        "what each one made room for."
    )

    if not owner.tasks:
        st.info("Add some tasks first -- there is nothing to plan yet.")
    else:
        a_col, b_col = st.columns(2)
        with a_col:
            strategy_a = st.selectbox("Plan A sorts by", STRATEGIES, index=0)
            if st.button("Build Plan A", width="stretch"):
                # asking for a first plan again starts the comparison over
                owner.request_schedule(strategy_a)
                flash("ok", f"Built Plan A, sorted by {strategy_a}.")
                st.rerun()
        with b_col:
            strategy_b = st.selectbox("Plan B sorts by", STRATEGIES, index=1)
            if st.button("Build Plan B", width="stretch"):
                owner.request_alternative(strategy_b)
                flash("ok", f"Built Plan B, sorted by {strategy_b}.")
                st.rerun()

        if not owner.candidates:
            st.info("No plans yet -- build Plan A to start.")
        else:
            columns = st.columns(len(owner.candidates))
            for column, candidate in zip(columns, owner.candidates):
                with column:
                    numbers = candidate.summary()
                    st.markdown(f"### {candidate.label}")
                    top, middle, bottom = st.columns(3)
                    top.metric("Placed", numbers["tasks_placed"])
                    middle.metric("Left out", numbers["tasks_dropped"])
                    bottom.metric("Free minutes", numbers["minutes_free"])

                    table(
                        placement_rows(candidate, candidate.placed_tasks()),
                        "Nothing could be placed.",
                    )

                    blocked = candidate.blocked_tasks()
                    if blocked:
                        st.warning(
                            "Waiting on something that never got scheduled: "
                            + ", ".join(task.title for task in blocked)
                        )
                    no_room = [
                        task for task in candidate.unplaced_tasks() if task not in blocked
                    ]
                    if no_room:
                        st.info(
                            "No room in the day for: "
                            + ", ".join(
                                f"{task.title} ({task.duration_minutes} min)"
                                for task in no_room
                            )
                        )

                    with st.expander("Why this plan looks like this"):
                        st.code(candidate.explain(), language=None)

            st.divider()
            st.markdown("### Choosing between them")
            st.code(owner.compare_candidates(), language=None)

            keep = st.radio(
                "Keep which plan?",
                [candidate.schedule_id for candidate in owner.candidates],
                format_func=lambda schedule_id: next(
                    candidate.label
                    for candidate in owner.candidates
                    if candidate.schedule_id == schedule_id
                ),
                horizontal=True,
            )
            drop_other = st.checkbox("Throw the other one away", value=False)
            if st.button("Save this plan", type="primary"):
                saved = owner.choose_schedule(keep)
                if drop_other:
                    owner.discard_unchosen(keep)
                flash("ok", f"Saved {saved.label}.")
                st.rerun()

    st.divider()
    st.markdown("### Saved plan")
    saved_schedule = owner.get_saved_schedule()
    if saved_schedule is None:
        st.caption("Nothing saved yet. There is no history -- saving again replaces it.")
    else:
        st.success(f"{saved_schedule.label} for {saved_schedule.day}")
        st.code(saved_schedule.explain(), language=None)


# -------------------------------------------------------------------- day view tab

with day_tab:
    st.subheader("Day view")

    if not owner.candidates and owner.get_saved_schedule() is None:
        st.info("Build a plan first, then come back to look through the day.")
    else:
        # the saved plan is usually one of the candidates, so key the plans by id to
        # offer each of them once
        schedules = {candidate.schedule_id: candidate for candidate in owner.candidates}
        saved_schedule = owner.get_saved_schedule()
        if saved_schedule is not None:
            schedules.setdefault(saved_schedule.schedule_id, saved_schedule)

        def plan_label(schedule_id: str) -> str:
            """Name a plan in the dropdown, marking the one that was saved."""
            plan = schedules[schedule_id]
            return plan.label + (" -- saved" if plan.is_saved else "")

        schedule = schedules[
            st.selectbox("Which plan?", list(schedules), format_func=plan_label)
        ]

        moment_col, window_col = st.columns(2)

        with moment_col:
            st.markdown("**What am I doing at...**")
            moment = st.time_input("Time", value=time(12, 0), step=STEP, key="at_moment")
            now_tasks = schedule.tasks_at(moment)
            if now_tasks:
                for task in now_tasks:
                    start, end = schedule.get_placement(task.task_id)
                    st.write(f"**{clock(start)}-{clock(end)}** {task.describe()}")
            else:
                st.caption(f"Nothing planned at {clock(moment)}.")

        with window_col:
            st.markdown("**One slice of the day**")
            slice_start = st.time_input(
                "From", value=owner.awake_window()[0], step=STEP, key="slice_start"
            )
            slice_end = st.time_input(
                "To", value=time(12, 0), step=STEP, key="slice_end"
            )
            if to_minutes(slice_end) <= to_minutes(slice_start):
                st.caption("Pick an end time after the start time.")
            else:
                table(
                    placement_rows(schedule, schedule.tasks_in_window(slice_start, slice_end)),
                    f"Nothing planned between {clock(slice_start)} and {clock(slice_end)}.",
                )
                # a fixed task defends its window, which is the usual reason a slice
                # of the day has no room left in it
                defenders = [
                    task for task in owner.tasks if task.blocks(slice_start, slice_end)
                ]
                if defenders:
                    st.caption(
                        "Fixed commitments across this window: "
                        + ", ".join(task.title for task in defenders)
                    )

        st.divider()
        st.markdown("**Look up one task**")
        looked_up_id = pick_task_id(
            owner, "Task", "lookup_task", tasks=schedule.tasks or owner.tasks
        )
        # the plan is asked first, so a task deleted since the plan was built can
        # still be looked up as the plan saw it
        looked_up = None
        if looked_up_id is not None:
            looked_up = schedule.get_task(looked_up_id) or owner.get_task(looked_up_id)
        if looked_up is not None:
            if schedule.contains_task(looked_up.task_id):
                start, end = schedule.get_placement(looked_up.task_id)
                st.success(f"{looked_up.title}: {clock(start)}-{clock(end)}")
            elif schedule.get_task(looked_up.task_id) is None:
                st.warning(f"{looked_up.title} was not part of this plan.")
            elif not schedule.dependencies_met(looked_up):
                missing = [
                    prerequisite_id
                    for prerequisite_id in looked_up.depends_on
                    if prerequisite_id not in schedule.placements
                ]
                st.error(
                    f"{looked_up.title} was left out -- it needs "
                    f"{', '.join(missing)} scheduled first."
                )
            else:
                st.error(
                    f"{looked_up.title} was left out -- no {looked_up.duration_minutes} "
                    "minute gap was free."
                )
