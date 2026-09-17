"""PawPal+ core system classes.

Skeleton generated from diagrams/uml.mmd. Attributes and method signatures only --
no scheduling logic yet.
"""

from datetime import date, time

# how far the scheduler slides a task when a slot is taken, in minutes
SEARCH_STEP = 5


def to_minutes(moment: time) -> int:
    """Turn a time into minutes since midnight, so times can be compared and added
    with plain arithmetic. A day is assumed not to cross midnight."""
    return moment.hour * 60 + moment.minute


def to_time(minutes: int) -> time:
    """Turn minutes since midnight back into a time, the inverse of to_minutes."""
    return time(hour=minutes // 60, minute=minutes % 60)


class Pet:
    """A single animal the user cares for. Pure data: tasks reference pets so the
    schedule can say which pet each task is for."""

    def __init__(
        self,
        pet_id: str,
        name: str,
        species: str,
        age: int,
        notes: str = "",
    ) -> None:
        """Store the pet's identity and basic profile details."""
        self.pet_id: str = pet_id
        self.name: str = name
        self.species: str = species
        self.age: int = age
        self.notes: str = notes


class Task:
    """One thing that needs to happen during the day (a walk, a vet call, a work
    meeting). Holds how long it takes, how important it is, and when the user would
    prefer it to happen."""

    def __init__(
        self,
        task_id: str,
        title: str,
        category: str,
        priority: int,
        duration_minutes: int,
        preferred_start: time | None = None,
        preferred_end: time | None = None,
        is_fixed: bool = False,
        pets: list["Pet"] | None = None,
        depends_on: list[str] | None = None,
    ) -> None:
        """Store the task's identity, cost in time, priority, time preference,
        which pets (if any) it belongs to, and which tasks must happen first."""
        self.task_id: str = task_id
        self.title: str = title
        self.category: str = category
        self.priority: int = priority
        self.duration_minutes: int = duration_minutes
        self.preferred_start: time | None = preferred_start
        self.preferred_end: time | None = preferred_end
        self.is_fixed: bool = is_fixed
        self.pets: list["Pet"] = pets if pets is not None else []
        # ids of tasks that must be placed before this one (e.g. "give medicine"
        # after "feed breakfast"). Ids, not Task objects, so the links stay flat.
        self.depends_on: list[str] = depends_on if depends_on is not None else []

    def is_pet_task(self) -> bool:
        """Return True if this task is for at least one pet, False if it is a
        personal task or fixed event."""
        return len(self.pets) > 0

    def is_for_pet(self, pet_id: str) -> bool:
        """Return True if the pet with the given id is one of this task's pets.
        This is the single check the user-level pet lookups are built on."""
        for pet in self.pets:
            if pet.pet_id == pet_id:
                return True
        return False

    def add_pet(self, pet: "Pet") -> None:
        """Link another pet to this task, so one task (a shared walk, a vet trip)
        can cover more than one animal."""
        # is_for_pet keeps the same pet from being linked twice
        if not self.is_for_pet(pet.pet_id):
            self.pets.append(pet)

    def remove_pet(self, pet_id: str) -> None:
        """Unlink the pet with the given id from this task, leaving the task's other
        pets in place."""
        self.pets = [pet for pet in self.pets if pet.pet_id != pet_id]

    def pet_names(self) -> list[str]:
        """Return the names of the pets this task is for, used when describing or
        explaining the task."""
        return [pet.name for pet in self.pets]

    def add_dependency(self, task_id: str) -> None:
        """Record that the given task must happen before this one. Ignores a repeat
        of a dependency that is already there."""
        if task_id not in self.depends_on:
            self.depends_on.append(task_id)

    def remove_dependency(self, task_id: str) -> None:
        """Drop the given prerequisite, leaving this task's other dependencies in
        place."""
        if task_id in self.depends_on:
            self.depends_on.remove(task_id)

    def has_dependencies(self) -> bool:
        """Return True if this task is waiting on any other task, which means the
        scheduler cannot place it freely."""
        return len(self.depends_on) > 0

    def blocks(self, start: time, end: time) -> bool:
        """Return True if this task is fixed and its time overlaps the given
        start/end window, meaning nothing else can be placed there."""
        if not self.is_fixed:
            return False
        # a fixed task without both times set has no window to defend
        if self.preferred_start is None or self.preferred_end is None:
            return False
        # two windows overlap when each one starts before the other one ends
        return self.preferred_start < end and start < self.preferred_end

    def describe(self) -> str:
        """Return a short human-readable line about this task, used when the
        schedule explains itself."""
        line = f"{self.title} ({self.category}, {self.duration_minutes} min, priority {self.priority})"
        if self.is_pet_task():
            line += " for " + ", ".join(self.pet_names())
        if self.is_fixed:
            line += " [fixed]"
        if self.has_dependencies():
            line += " after " + ", ".join(self.depends_on)
        return line


class Schedule:
    """One candidate plan for a day. Takes a list of tasks and tries to place each
    one in the user's awake window according to a strategy, then reports what fit,
    what did not, and why."""

    def __init__(
        self,
        schedule_id: str,
        label: str,
        day: date,
        strategy: str,
    ) -> None:
        """Set up an empty candidate schedule for one day under one strategy."""
        self.schedule_id: str = schedule_id
        self.label: str = label
        self.day: date = day
        self.strategy: str = strategy
        self.is_saved: bool = False
        # every task build() was given to consider, placed or not
        self.tasks: list["Task"] = []
        # task_id -> (start_time, end_time) for every task that got placed
        self.placements: dict[str, tuple] = {}
        # the awake window build() was handed. place_task searches inside it, so it
        # is remembered here instead of being passed down through every call.
        self.wake_time: time | None = None
        self.sleep_time: time | None = None

    def build(self, tasks: list["Task"], wake_time: time, sleep_time: time) -> None:
        """Fill in this schedule: sort the tasks by strategy, reorder them so
        prerequisites come first, then try to place each one between wake_time and
        sleep_time."""
        self.tasks = list(tasks)
        self.wake_time = wake_time
        self.sleep_time = sleep_time
        # building twice should not stack the old plan under the new one
        self.placements = {}

        ordered = self.sort_by_strategy(self.tasks)
        ordered = self.sort_by_dependencies(ordered)
        for task in ordered:
            self.place_task(task)

    def place_task(self, task: "Task") -> bool:
        """Try to find an open slot for one task and record it in placements.
        Return True if it was placed, False if there was no room."""
        if self.wake_time is None or self.sleep_time is None:
            return False
        # a task whose prerequisites never got placed cannot be placed either
        if not self.dependencies_met(task):
            return False

        day_start = to_minutes(self.wake_time)
        day_end = to_minutes(self.sleep_time)
        length = task.duration_minutes

        # nothing may start before the day does, or before its prerequisites end
        floor = day_start
        after = self.earliest_start_for(task)
        if after is not None:
            floor = max(floor, to_minutes(after))

        # a fixed task is an appointment, not a preference: it goes where the user
        # pinned it or it does not go at all
        if task.is_fixed and task.preferred_start is not None:
            start = to_minutes(task.preferred_start)
            if task.preferred_end is not None:
                end = to_minutes(task.preferred_end)
            else:
                end = start + length
            if start < floor or end > day_end:
                return False
            if not self.is_free(to_time(start), to_time(end)):
                return False
            self.placements[task.task_id] = (to_time(start), to_time(end))
            return True

        # A flexible task gets three tries, in order of how close they stay to what
        # the user wanted: the window they asked for, any time after it, and only
        # then anywhere at all. Without the middle try a 10am vet call whose window
        # is busy would be dragged back to breakfast time.
        windows = []
        if task.preferred_start is not None:
            wanted_start = max(floor, to_minutes(task.preferred_start))
            wanted_end = day_end
            if task.preferred_end is not None:
                wanted_end = min(day_end, to_minutes(task.preferred_end))
            windows.append((wanted_start, wanted_end))
            windows.append((wanted_start, day_end))
        windows.append((floor, day_end))

        for window_start, window_end in windows:
            start = window_start
            while start + length <= window_end:
                if self.is_free(to_time(start), to_time(start + length)):
                    self.placements[task.task_id] = (
                        to_time(start),
                        to_time(start + length),
                    )
                    return True
                start += SEARCH_STEP
        return False

    def is_free(self, start: time, end: time) -> bool:
        """Return True if no already-placed task overlaps the given window."""
        new_start = to_minutes(start)
        new_end = to_minutes(end)
        for placed_start, placed_end in self.placements.values():
            # same overlap test as Task.blocks: touching edges do not count
            if to_minutes(placed_start) < new_end and new_start < to_minutes(placed_end):
                return False
        return True

    def sort_by_strategy(self, tasks: list["Task"]) -> list["Task"]:
        """Return the tasks reordered for this schedule's strategy (for example
        highest priority first, or shortest task first)."""
        ordered = list(tasks)
        if self.strategy == "priority":
            # a bigger priority number means more important
            ordered.sort(key=lambda task: -task.priority)
        elif self.strategy == "shortest":
            ordered.sort(key=lambda task: task.duration_minutes)
        elif self.strategy == "longest":
            ordered.sort(key=lambda task: -task.duration_minutes)
        elif self.strategy == "earliest":
            # tasks with no preferred start go last, after every timed task
            ordered.sort(
                key=lambda task: to_minutes(task.preferred_start)
                if task.preferred_start is not None
                else 24 * 60
            )
        # any other strategy name keeps the order the tasks came in

        # fixed tasks cannot move, so they claim their slots before anything
        # flexible does. Python's sort is stable, so this keeps the strategy order
        # inside each group.
        ordered.sort(key=lambda task: 0 if task.is_fixed else 1)
        return ordered

    def sort_by_dependencies(self, tasks: list["Task"]) -> list["Task"]:
        """Return the tasks reordered so every prerequisite comes before the task
        that needs it, keeping the strategy order among tasks that do not depend on
        each other. build() runs this after sort_by_strategy."""
        remaining = list(tasks)
        ordered: list["Task"] = []

        while remaining:
            ready = []
            for task in remaining:
                # only prerequisites still waiting in this list hold a task back.
                # A prerequisite that is not part of this day at all is handled
                # later, by dependencies_met.
                waiting = False
                for prerequisite_id in task.depends_on:
                    for other in remaining:
                        if other.task_id == prerequisite_id and other is not task:
                            waiting = True
                if not waiting:
                    ready.append(task)

            if not ready:
                # a dependency loop: nothing can go first, so keep the rest in
                # strategy order rather than dropping them
                ordered.extend(remaining)
                break

            ordered.extend(ready)
            remaining = [task for task in remaining if task not in ready]

        return ordered

    def dependencies_met(self, task: "Task") -> bool:
        """Return True if all of this task's prerequisites are already placed in
        this schedule, so it is allowed to be placed now."""
        for prerequisite_id in task.depends_on:
            if prerequisite_id not in self.placements:
                return False
        return True

    def earliest_start_for(self, task: "Task") -> time | None:
        """Return the earliest time this task may start -- the end of its latest
        prerequisite, or None if it has no prerequisites placed yet. place_task uses
        this as the floor when it searches for a slot."""
        latest_end: time | None = None
        for prerequisite_id in task.depends_on:
            placement = self.placements.get(prerequisite_id)
            if placement is None:
                continue
            end = placement[1]
            if latest_end is None or to_minutes(end) > to_minutes(latest_end):
                latest_end = end
        return latest_end

    def blocked_tasks(self) -> list["Task"]:
        """Return the tasks that could not be placed because a prerequisite was
        never placed, as opposed to simply running out of room. explain() reports
        these differently."""
        return [
            task for task in self.unplaced_tasks() if not self.dependencies_met(task)
        ]

    def placed_tasks(self) -> list["Task"]:
        """Return the tasks that made it into the schedule, in time order."""
        placed = [task for task in self.tasks if task.task_id in self.placements]
        placed.sort(key=lambda task: to_minutes(self.placements[task.task_id][0]))
        return placed

    def unplaced_tasks(self) -> list["Task"]:
        """Return the tasks that could not fit in the day."""
        return [task for task in self.tasks if task.task_id not in self.placements]

    def contains_task(self, task_id: str) -> bool:
        """Return True if the given task actually got placed in this schedule.
        Useful when comparing candidates: 'candidate A made room for the vet call,
        candidate B did not.'"""
        return task_id in self.placements

    def get_task(self, task_id: str) -> "Task | None":
        """Look up one of this schedule's tasks by id, or return None if the task
        was never considered for this day."""
        for task in self.tasks:
            if task.task_id == task_id:
                return task
        return None

    def get_placement(self, task_id: str) -> tuple | None:
        """Return the (start, end) times this task was scheduled for, or None if it
        was not placed."""
        return self.placements.get(task_id)

    def tasks_at(self, moment: time) -> list["Task"]:
        """Return the tasks scheduled across the given moment -- the 'what am I
        doing at 3pm?' view."""
        now = to_minutes(moment)
        found = []
        for task in self.placed_tasks():
            start, end = self.placements[task.task_id]
            # a task that ends at 3pm is over, so the end is not included
            if to_minutes(start) <= now < to_minutes(end):
                found.append(task)
        return found

    def tasks_in_window(self, start: time, end: time) -> list["Task"]:
        """Return the placed tasks that overlap the given time window, for showing
        one slice of the day (a morning block, an afternoon block)."""
        window_start = to_minutes(start)
        window_end = to_minutes(end)
        found = []
        for task in self.placed_tasks():
            task_start, task_end = self.placements[task.task_id]
            if to_minutes(task_start) < window_end and window_start < to_minutes(task_end):
                found.append(task)
        return found

    def summary(self) -> dict:
        """Return the schedule's headline numbers -- things like tasks placed,
        tasks dropped, and total minutes booked."""
        placed = self.placed_tasks()
        minutes_booked = 0
        for task in placed:
            start, end = self.placements[task.task_id]
            minutes_booked += to_minutes(end) - to_minutes(start)

        minutes_awake = 0
        if self.wake_time is not None and self.sleep_time is not None:
            minutes_awake = to_minutes(self.sleep_time) - to_minutes(self.wake_time)

        return {
            "schedule_id": self.schedule_id,
            "label": self.label,
            "strategy": self.strategy,
            "tasks_considered": len(self.tasks),
            "tasks_placed": len(placed),
            "tasks_dropped": len(self.unplaced_tasks()),
            "tasks_blocked": len(self.blocked_tasks()),
            "minutes_booked": minutes_booked,
            "minutes_free": minutes_awake - minutes_booked,
        }

    def explain(self) -> str:
        """Return a plain-language explanation of the plan: why each task landed
        where it did, and why anything was left out."""
        numbers = self.summary()
        lines = [
            f"{self.label} ({self.day}) -- sorted by {self.strategy}",
            f"{numbers['tasks_placed']} of {numbers['tasks_considered']} tasks placed, "
            f"{numbers['minutes_booked']} minutes booked, "
            f"{numbers['minutes_free']} minutes free.",
            "",
        ]

        placed = self.placed_tasks()
        if placed:
            lines.append("Planned:")
            for task in placed:
                start, end = self.placements[task.task_id]
                reason = self._reason_for(task, start)
                lines.append(
                    f"  {start.strftime('%H:%M')}-{end.strftime('%H:%M')}  "
                    f"{task.describe()} -- {reason}"
                )
        else:
            lines.append("Nothing could be planned for this day.")

        blocked = self.blocked_tasks()
        if blocked:
            lines.append("")
            lines.append("Waiting on something that never got scheduled:")
            for task in blocked:
                missing = [
                    prerequisite_id
                    for prerequisite_id in task.depends_on
                    if prerequisite_id not in self.placements
                ]
                lines.append(
                    f"  {task.title} -- needs {', '.join(missing)} first"
                )

        # dropped for lack of room is a different story from dropped for a
        # missing prerequisite, so the two are listed separately
        no_room = [task for task in self.unplaced_tasks() if task not in blocked]
        if no_room:
            lines.append("")
            lines.append("Left out, no room in the day:")
            for task in no_room:
                lines.append(f"  {task.title} -- needs {task.duration_minutes} min")

        return "\n".join(lines)

    def _reason_for(self, task: "Task", start: time) -> str:
        """Return the one-line 'why here' note explain() prints beside a task."""
        if task.is_fixed:
            return "fixed commitment, everything else worked around it"
        after = self.earliest_start_for(task)
        if after is not None:
            return f"could not start before {after.strftime('%H:%M')}, when what it depends on ends"
        if task.preferred_start is not None and start == task.preferred_start:
            return "got the time you asked for"
        if task.preferred_start is not None:
            return f"asked for {task.preferred_start.strftime('%H:%M')}, that window was full"
        return f"no time preference, placed by {self.strategy}"


class User:
    """The pet owner. Owns the pets and tasks, knows their own awake window, and
    drives the workflow: request a schedule, request an alternative, compare the two
    candidates, then save the one they want."""

    def __init__(
        self,
        name: str,
        wake_time: time,
        sleep_time: time,
    ) -> None:
        """Store the owner's name and daily awake window, and start with empty pet,
        task, and candidate-schedule lists."""
        self.name: str = name
        self.pets: list["Pet"] = []
        self.tasks: list["Task"] = []
        self.wake_time: time = wake_time
        self.sleep_time: time = sleep_time
        # up to two generated schedules waiting to be compared
        self.candidates: list["Schedule"] = []
        self.saved_schedule: "Schedule | None" = None

    def add_pet(self, pet: "Pet") -> None:
        """Add a pet to this user's list of pets."""
        pass

    def add_task(self, task: "Task") -> None:
        """Add a task to this user's list of tasks."""
        pass

    def delete_task(self, task_id: str) -> None:
        """Remove the task with the given id from this user's task list, and also
        drop it from every other task's depends_on list. Without that cleanup a
        leftover id points at a task that no longer exists, and the dependent task
        would wait on a prerequisite that can never be placed."""
        pass

    def set_priority(self, task_id: str, priority: int) -> None:
        """Change how important a task is, which affects where it lands in a
        schedule."""
        pass

    def set_time_preference(self, task_id: str, window: tuple, duration: int) -> None:
        """Set a task's preferred time window and how long it should take."""
        pass

    def set_dependency(self, task_id: str, prerequisite_id: str) -> None:
        """Say that one task must happen before another -- 'walk Mochi only after
        breakfast'. The schedule then orders them that way instead of by strategy
        alone. Refuses a dependency that would create a loop, since a loop would
        leave both tasks permanently unplaceable."""
        pass

    def clear_dependency(self, task_id: str, prerequisite_id: str) -> None:
        """Remove one prerequisite from a task, freeing the scheduler to place it
        wherever the strategy prefers."""
        pass

    def dependencies_of(self, task_id: str) -> list["Task"]:
        """Return the tasks that must happen before the given task, for showing the
        user what a task is waiting on."""
        pass

    def creates_cycle(self, task_id: str, prerequisite_id: str) -> bool:
        """Return True if adding this dependency would make a task depend on itself
        through some chain. Checked by set_dependency before it commits."""
        pass

    def add_event(self, title: str, start: time, end: time) -> None:
        """Add a fixed commitment (work, class, an appointment) that the scheduler
        must plan around instead of move."""
        pass

    def get_pet(self, pet_id: str) -> "Pet | None":
        """Look up one of this user's pets by id, or return None if there is no
        such pet."""
        pass

    def tasks_for_pet(self, pet_id: str) -> list["Task"]:
        """Return every task that is for the given pet -- the 'what does Mochi need
        today?' view."""
        pass

    def tasks_for_species(self, species: str) -> list["Task"]:
        """Return every task belonging to any pet of the given species, for a user
        with more than one kind of animal."""
        pass

    def tasks_by_pet(self) -> dict[str, list["Task"]]:
        """Group this user's pet tasks by pet id, so the whole day can be shown one
        pet at a time. A task shared by two pets appears under both."""
        pass

    def personal_tasks(self) -> list["Task"]:
        """Return the tasks that are not tied to any pet (the user's own errands and
        fixed events), the complement of the pet tasks."""
        pass

    def awake_window(self) -> tuple:
        """Return the (wake_time, sleep_time) pair the scheduler is allowed to use."""
        pass

    def request_schedule(self, strategy: str) -> "Schedule":
        """Build a first candidate schedule from this user's tasks using the given
        strategy, store it in candidates, and return it."""
        pass

    def request_alternative(self, strategy: str) -> "Schedule":
        """Build a second candidate schedule using a different strategy so the user
        has something to compare against."""
        pass

    def compare_candidates(self) -> str:
        """Return a side-by-side explanation of the candidate schedules so the user
        can decide between them."""
        pass

    def choose_schedule(self, schedule_id: str) -> "Schedule":
        """Mark the chosen candidate as saved, set it as saved_schedule, and return
        it."""
        pass

    def discard_unchosen(self, schedule_id: str) -> None:
        """Drop the candidate schedules the user did not pick."""
        pass

    def get_saved_schedule(self) -> "Schedule | None":
        """Return the one schedule the user has saved, or None if they have not
        chosen one yet. There is no history -- choosing again replaces this."""
        pass

