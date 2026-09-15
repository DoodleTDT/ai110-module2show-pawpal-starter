"""PawPal+ core system classes.

Skeleton generated from diagrams/uml.mmd. Attributes and method signatures only --
no scheduling logic yet.
"""

from datetime import date, time


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
        pass

    def is_for_pet(self, pet_id: str) -> bool:
        """Return True if the pet with the given id is one of this task's pets.
        This is the single check the user-level pet lookups are built on."""
        pass

    def add_pet(self, pet: "Pet") -> None:
        """Link another pet to this task, so one task (a shared walk, a vet trip)
        can cover more than one animal."""
        pass

    def remove_pet(self, pet_id: str) -> None:
        """Unlink the pet with the given id from this task, leaving the task's other
        pets in place."""
        pass

    def pet_names(self) -> list[str]:
        """Return the names of the pets this task is for, used when describing or
        explaining the task."""
        pass

    def add_dependency(self, task_id: str) -> None:
        """Record that the given task must happen before this one. Ignores a repeat
        of a dependency that is already there."""
        pass

    def remove_dependency(self, task_id: str) -> None:
        """Drop the given prerequisite, leaving this task's other dependencies in
        place."""
        pass

    def has_dependencies(self) -> bool:
        """Return True if this task is waiting on any other task, which means the
        scheduler cannot place it freely."""
        pass

    def blocks(self, start: time, end: time) -> bool:
        """Return True if this task is fixed and its time overlaps the given
        start/end window, meaning nothing else can be placed there."""
        pass

    def describe(self) -> str:
        """Return a short human-readable line about this task, used when the
        schedule explains itself."""
        pass


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

    def build(self, tasks: list["Task"], wake_time: time, sleep_time: time) -> None:
        """Fill in this schedule: sort the tasks by strategy, reorder them so
        prerequisites come first, then try to place each one between wake_time and
        sleep_time."""
        pass

    def place_task(self, task: "Task") -> bool:
        """Try to find an open slot for one task and record it in placements.
        Return True if it was placed, False if there was no room."""
        pass

    def is_free(self, start: time, end: time) -> bool:
        """Return True if no already-placed task overlaps the given window."""
        pass

    def sort_by_strategy(self, tasks: list["Task"]) -> list["Task"]:
        """Return the tasks reordered for this schedule's strategy (for example
        highest priority first, or shortest task first)."""
        pass

    def sort_by_dependencies(self, tasks: list["Task"]) -> list["Task"]:
        """Return the tasks reordered so every prerequisite comes before the task
        that needs it, keeping the strategy order among tasks that do not depend on
        each other. build() runs this after sort_by_strategy."""
        pass

    def dependencies_met(self, task: "Task") -> bool:
        """Return True if all of this task's prerequisites are already placed in
        this schedule, so it is allowed to be placed now."""
        pass

    def earliest_start_for(self, task: "Task") -> time | None:
        """Return the earliest time this task may start -- the end of its latest
        prerequisite, or None if it has no prerequisites placed yet. place_task uses
        this as the floor when it searches for a slot."""
        pass

    def blocked_tasks(self) -> list["Task"]:
        """Return the tasks that could not be placed because a prerequisite was
        never placed, as opposed to simply running out of room. explain() reports
        these differently."""
        pass

    def placed_tasks(self) -> list["Task"]:
        """Return the tasks that made it into the schedule, in time order."""
        pass

    def unplaced_tasks(self) -> list["Task"]:
        """Return the tasks that could not fit in the day."""
        pass

    def contains_task(self, task_id: str) -> bool:
        """Return True if the given task actually got placed in this schedule.
        Useful when comparing candidates: 'candidate A made room for the vet call,
        candidate B did not.'"""
        pass

    def get_task(self, task_id: str) -> "Task | None":
        """Look up one of this schedule's tasks by id, or return None if the task
        was never considered for this day."""
        pass

    def get_placement(self, task_id: str) -> tuple | None:
        """Return the (start, end) times this task was scheduled for, or None if it
        was not placed."""
        pass

    def tasks_at(self, moment: time) -> list["Task"]:
        """Return the tasks scheduled across the given moment -- the 'what am I
        doing at 3pm?' view."""
        pass

    def tasks_in_window(self, start: time, end: time) -> list["Task"]:
        """Return the placed tasks that overlap the given time window, for showing
        one slice of the day (a morning block, an afternoon block)."""
        pass

    def summary(self) -> dict:
        """Return the schedule's headline numbers -- things like tasks placed,
        tasks dropped, and total minutes booked."""
        pass

    def explain(self) -> str:
        """Return a plain-language explanation of the plan: why each task landed
        where it did, and why anything was left out."""
        pass


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


# 4. **Task Dependencies**: If certain tasks depend on the completion of others, 
# it might be useful to establish a relationship between tasks to represent 
# dependencies. This could help in scheduling tasks in a logical order.
