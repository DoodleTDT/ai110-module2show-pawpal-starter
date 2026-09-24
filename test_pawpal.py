"""
This is where to test the code from pawpal_system.py and main.py

Every test below checks one promise a docstring or comment in pawpal_system.py
makes, so the tests fail if the code ever stops doing what it says it does.
"""
from datetime import date, time

import pytest

from pawpal_system import (
    Pet,
    Schedule,
    Task,
    User,
    overlaps,
    to_minutes,
    to_time,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def make_task(task_id, **overrides):
    """Build a plain task with sensible defaults, so each test only has to spell
    out the one or two fields it actually cares about."""
    fields = {
        "task_id": task_id,
        "title": task_id.replace("_", " "),
        "category": "chore",
        "priority": 3,
        "duration_minutes": 30,
    }
    fields.update(overrides)
    return Task(**fields)


def make_schedule(strategy="priority"):
    """Build an empty schedule for a single day under one strategy."""
    return Schedule(
        schedule_id="test-plan",
        label="Test Plan",
        day=date(2025, 1, 1),
        strategy=strategy,
    )


@pytest.fixture
def owner():
    """A user awake 07:00-20:00 with one dog and one cat."""
    user = User("Tionna", time(7, 0), time(20, 0))
    user.add_pet("pet_1", "Mochi", "dog", 3)
    user.add_pet("pet_2", "Whiskers", "cat", 2)
    return user


# ---------------------------------------------------------------------------
# module-level time helpers
# ---------------------------------------------------------------------------

class TestTimeHelpers:
    """to_minutes / to_time say they are inverses, and overlaps says touching
    windows do not count as a conflict."""

    def test_to_minutes_counts_from_midnight(self):
        assert to_minutes(time(0, 0)) == 0
        assert to_minutes(time(9, 30)) == 570

    def test_to_time_is_the_inverse_of_to_minutes(self):
        # "the inverse of to_minutes"
        for moment in (time(0, 0), time(7, 5), time(13, 45), time(23, 59)):
            assert to_time(to_minutes(moment)) == moment

    def test_overlapping_windows_are_reported(self):
        assert overlaps(time(9, 0), time(10, 0), time(9, 30), time(10, 30)) is True

    def test_touching_windows_do_not_overlap(self):
        # "a walk ending at 09:00 and work starting at 09:00 both fit"
        assert overlaps(time(8, 0), time(9, 0), time(9, 0), time(10, 0)) is False

    def test_separate_windows_do_not_overlap(self):
        assert overlaps(time(8, 0), time(9, 0), time(11, 0), time(12, 0)) is False

    def test_a_window_fully_inside_another_overlaps(self):
        assert overlaps(time(8, 0), time(12, 0), time(9, 0), time(10, 0)) is True


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

class TestPet:
    """Pet is described as pure data: it stores the profile it is given."""

    def test_pet_stores_its_profile(self):
        pet = Pet("pet_1", "Mochi", "dog", 3, "scared of the vacuum")
        assert pet.pet_id == "pet_1"
        assert pet.name == "Mochi"
        assert pet.species == "dog"
        assert pet.age == 3
        assert pet.notes == "scared of the vacuum"

    def test_notes_default_to_empty(self):
        assert Pet("pet_2", "Whiskers", "cat", 2).notes == ""


# ---------------------------------------------------------------------------
# Task -- pets
# ---------------------------------------------------------------------------

class TestTaskPets:
    """is_pet_task, is_for_pet, add_pet, remove_pet and pet_names."""

    def test_task_with_a_pet_is_a_pet_task(self):
        mochi = Pet("pet_1", "Mochi", "dog", 3)
        assert make_task("t1", pets=[mochi]).is_pet_task() is True

    def test_task_without_pets_is_not_a_pet_task(self):
        # "False if it is a personal task or fixed event"
        assert make_task("t1").is_pet_task() is False

    def test_pets_default_to_an_empty_list_per_task(self):
        # the default must not be shared between tasks
        first, second = make_task("t1"), make_task("t2")
        first.add_pet(Pet("pet_1", "Mochi", "dog", 3))
        assert second.pets == []

    def test_is_for_pet_finds_a_linked_pet(self):
        mochi = Pet("pet_1", "Mochi", "dog", 3)
        task = make_task("t1", pets=[mochi])
        assert task.is_for_pet("pet_1") is True
        assert task.is_for_pet("pet_2") is False

    def test_add_pet_links_another_animal(self):
        # "one task (a shared walk, a vet trip) can cover more than one animal"
        task = make_task("t1", pets=[Pet("pet_1", "Mochi", "dog", 3)])
        task.add_pet(Pet("pet_2", "Whiskers", "cat", 2))
        assert task.pet_names() == ["Mochi", "Whiskers"]

    def test_add_pet_ignores_a_pet_already_linked(self):
        # "is_for_pet keeps the same pet from being linked twice"
        mochi = Pet("pet_1", "Mochi", "dog", 3)
        task = make_task("t1", pets=[mochi])
        task.add_pet(mochi)
        task.add_pet(Pet("pet_1", "Mochi", "dog", 3))
        assert len(task.pets) == 1

    def test_remove_pet_leaves_the_other_pets_in_place(self):
        task = make_task(
            "t1",
            pets=[Pet("pet_1", "Mochi", "dog", 3), Pet("pet_2", "Whiskers", "cat", 2)],
        )
        task.remove_pet("pet_1")
        assert task.pet_names() == ["Whiskers"]

    def test_remove_pet_that_was_never_linked_changes_nothing(self):
        task = make_task("t1", pets=[Pet("pet_1", "Mochi", "dog", 3)])
        task.remove_pet("pet_9")
        assert task.pet_names() == ["Mochi"]


# ---------------------------------------------------------------------------
# Task -- dependencies
# ---------------------------------------------------------------------------

class TestTaskDependencies:
    """add_dependency, remove_dependency and has_dependencies."""

    def test_add_dependency_records_a_prerequisite(self):
        task = make_task("medicine")
        task.add_dependency("breakfast")
        assert task.depends_on == ["breakfast"]

    def test_add_dependency_ignores_a_repeat(self):
        # "Ignores a repeat of a dependency that is already there"
        task = make_task("medicine")
        task.add_dependency("breakfast")
        task.add_dependency("breakfast")
        assert task.depends_on == ["breakfast"]

    def test_remove_dependency_keeps_the_others(self):
        task = make_task("medicine", depends_on=["breakfast", "walk"])
        task.remove_dependency("breakfast")
        assert task.depends_on == ["walk"]

    def test_remove_dependency_that_is_not_there_is_harmless(self):
        task = make_task("medicine", depends_on=["breakfast"])
        task.remove_dependency("nap")
        assert task.depends_on == ["breakfast"]

    def test_has_dependencies_reports_whether_the_task_is_waiting(self):
        assert make_task("t1").has_dependencies() is False
        assert make_task("t2", depends_on=["t1"]).has_dependencies() is True


# ---------------------------------------------------------------------------
# Task -- blocks() and describe()
# ---------------------------------------------------------------------------

class TestTaskBlocksAndDescribe:
    """blocks() defends a fixed task's window; describe() is the one-line summary."""

    def test_a_fixed_task_blocks_an_overlapping_window(self):
        work = make_task(
            "work",
            is_fixed=True,
            preferred_start=time(9, 0),
            preferred_end=time(17, 0),
        )
        assert work.blocks(time(10, 0), time(11, 0)) is True

    def test_a_fixed_task_does_not_block_a_window_that_only_touches_it(self):
        work = make_task(
            "work",
            is_fixed=True,
            preferred_start=time(9, 0),
            preferred_end=time(17, 0),
        )
        assert work.blocks(time(8, 0), time(9, 0)) is False

    def test_a_flexible_task_never_blocks(self):
        # "Return True if this task is fixed and ..."
        walk = make_task("walk", preferred_start=time(9, 0), preferred_end=time(17, 0))
        assert walk.blocks(time(10, 0), time(11, 0)) is False

    def test_a_fixed_task_without_both_times_has_no_window_to_defend(self):
        # "a fixed task without both times set has no window to defend"
        vague = make_task("vague", is_fixed=True, preferred_start=time(9, 0))
        assert vague.blocks(time(9, 30), time(10, 0)) is False

    def test_describe_lists_the_basics(self):
        task = make_task("walk", title="Walk Mochi", category="exercise",
                         priority=4, duration_minutes=45)
        assert task.describe() == "Walk Mochi (exercise, 45 min, priority 4)"

    def test_describe_names_the_pets_a_task_is_for(self):
        task = make_task(
            "walk",
            title="Walk",
            pets=[Pet("pet_1", "Mochi", "dog", 3), Pet("pet_2", "Whiskers", "cat", 2)],
        )
        assert "for Mochi, Whiskers" in task.describe()

    def test_describe_marks_a_fixed_task(self):
        task = make_task("work", is_fixed=True, preferred_start=time(9, 0),
                         preferred_end=time(17, 0))
        assert "[fixed]" in task.describe()

    def test_describe_names_what_a_task_waits_on(self):
        task = make_task("medicine", depends_on=["breakfast"])
        assert task.describe().endswith("after breakfast")


# ---------------------------------------------------------------------------
# Schedule -- strategy ordering
# ---------------------------------------------------------------------------

class TestSortByStrategy:
    """sort_by_strategy reorders tasks for the named strategy, with fixed tasks
    always first and the strategy order kept inside each group."""

    def ids(self, schedule, tasks):
        return [task.task_id for task in schedule.sort_by_strategy(tasks)]

    def test_priority_puts_the_most_important_first(self):
        # "a bigger priority number means more important"
        tasks = [make_task("low", priority=1), make_task("high", priority=5),
                 make_task("mid", priority=3)]
        assert self.ids(make_schedule("priority"), tasks) == ["high", "mid", "low"]

    def test_shortest_puts_the_quickest_first(self):
        tasks = [make_task("long", duration_minutes=90),
                 make_task("short", duration_minutes=10)]
        assert self.ids(make_schedule("shortest"), tasks) == ["short", "long"]

    def test_longest_puts_the_biggest_first(self):
        tasks = [make_task("short", duration_minutes=10),
                 make_task("long", duration_minutes=90)]
        assert self.ids(make_schedule("longest"), tasks) == ["long", "short"]

    def test_earliest_sorts_by_preferred_start(self):
        tasks = [make_task("noon", preferred_start=time(12, 0)),
                 make_task("dawn", preferred_start=time(6, 0))]
        assert self.ids(make_schedule("earliest"), tasks) == ["dawn", "noon"]

    def test_earliest_puts_untimed_tasks_after_every_timed_one(self):
        # "tasks with no preferred start go last, after every timed task"
        tasks = [make_task("anytime"), make_task("late", preferred_start=time(23, 0))]
        assert self.ids(make_schedule("earliest"), tasks) == ["late", "anytime"]

    def test_an_unknown_strategy_keeps_the_order_it_was_given(self):
        # "any other strategy name keeps the order the tasks came in"
        tasks = [make_task("b", priority=1), make_task("a", priority=5)]
        assert self.ids(make_schedule("whatever"), tasks) == ["b", "a"]

    def test_fixed_tasks_claim_their_slots_before_anything_flexible(self):
        tasks = [make_task("urgent", priority=9),
                 make_task("work", priority=1, is_fixed=True,
                           preferred_start=time(9, 0), preferred_end=time(17, 0))]
        assert self.ids(make_schedule("priority"), tasks) == ["work", "urgent"]

    def test_the_strategy_order_survives_inside_each_group(self):
        # "Python's sort is stable, so this keeps the strategy order inside each group"
        tasks = [
            make_task("flex_low", priority=1),
            make_task("fixed_low", priority=2, is_fixed=True,
                      preferred_start=time(8, 0), preferred_end=time(9, 0)),
            make_task("flex_high", priority=9),
            make_task("fixed_high", priority=8, is_fixed=True,
                      preferred_start=time(9, 0), preferred_end=time(10, 0)),
        ]
        assert self.ids(make_schedule("priority"), tasks) == [
            "fixed_high", "fixed_low", "flex_high", "flex_low",
        ]


# ---------------------------------------------------------------------------
# Schedule -- dependency ordering
# ---------------------------------------------------------------------------

class TestSortByDependencies:
    """sort_by_dependencies puts prerequisites first without scrambling the rest."""

    def test_a_prerequisite_comes_before_the_task_that_needs_it(self):
        schedule = make_schedule()
        breakfast = make_task("breakfast")
        medicine = make_task("medicine", depends_on=["breakfast"])
        ordered = schedule.sort_by_dependencies([medicine, breakfast])
        assert [task.task_id for task in ordered] == ["breakfast", "medicine"]

    def test_a_whole_chain_is_untangled(self):
        schedule = make_schedule()
        first = make_task("first")
        second = make_task("second", depends_on=["first"])
        third = make_task("third", depends_on=["second"])
        ordered = schedule.sort_by_dependencies([third, second, first])
        assert [task.task_id for task in ordered] == ["first", "second", "third"]

    def test_independent_tasks_keep_the_strategy_order(self):
        # "keeping the strategy order among tasks that do not depend on each other"
        schedule = make_schedule()
        tasks = [make_task("a"), make_task("b"), make_task("c")]
        ordered = schedule.sort_by_dependencies(tasks)
        assert [task.task_id for task in ordered] == ["a", "b", "c"]

    def test_a_prerequisite_outside_this_day_does_not_hold_a_task_back(self):
        # "A prerequisite that is not part of this day at all is handled later"
        schedule = make_schedule()
        orphan = make_task("orphan", depends_on=["not_today"])
        ordered = schedule.sort_by_dependencies([orphan])
        assert [task.task_id for task in ordered] == ["orphan"]

    def test_a_dependency_loop_keeps_every_task_instead_of_dropping_them(self):
        # "keep the rest in strategy order rather than dropping them"
        schedule = make_schedule()
        left = make_task("left", depends_on=["right"])
        right = make_task("right", depends_on=["left"])
        ordered = schedule.sort_by_dependencies([left, right])
        assert [task.task_id for task in ordered] == ["left", "right"]


# ---------------------------------------------------------------------------
# Schedule -- placing tasks
# ---------------------------------------------------------------------------

class TestPlaceTask:
    """place_task finds a slot inside the awake window, or reports there is none."""

    def test_a_task_is_placed_inside_the_awake_window(self):
        schedule = make_schedule()
        walk = make_task("walk", duration_minutes=60)
        schedule.build([walk], time(7, 0), time(20, 0))
        assert schedule.get_placement("walk") == (time(7, 0), time(8, 0))

    def test_nothing_can_be_placed_before_build_sets_the_day(self):
        # place_task returns False while wake/sleep are still None
        assert make_schedule().place_task(make_task("walk")) is False

    def test_a_fixed_task_goes_where_the_user_pinned_it(self):
        # "a fixed task is an appointment, not a preference"
        schedule = make_schedule()
        work = make_task("work", is_fixed=True, duration_minutes=480,
                         preferred_start=time(9, 0), preferred_end=time(17, 0))
        schedule.build([work], time(7, 0), time(20, 0))
        assert schedule.get_placement("work") == (time(9, 0), time(17, 0))

    def test_a_fixed_task_outside_the_awake_window_is_not_placed(self):
        # "it goes where the user pinned it or it does not go at all"
        schedule = make_schedule()
        night_shift = make_task("night", is_fixed=True, duration_minutes=120,
                                preferred_start=time(21, 0), preferred_end=time(23, 0))
        schedule.build([night_shift], time(7, 0), time(20, 0))
        assert schedule.get_placement("night") is None

    def test_two_fixed_tasks_on_the_same_slot_cannot_both_be_placed(self):
        schedule = make_schedule()
        first = make_task("work", is_fixed=True, duration_minutes=60,
                          preferred_start=time(9, 0), preferred_end=time(10, 0))
        second = make_task("class", is_fixed=True, duration_minutes=60,
                           preferred_start=time(9, 30), preferred_end=time(10, 30))
        schedule.build([first, second], time(7, 0), time(20, 0))
        assert len(schedule.placements) == 1

    def test_a_flexible_task_gets_the_window_it_asked_for(self):
        schedule = make_schedule()
        vet = make_task("vet", duration_minutes=30,
                        preferred_start=time(10, 0), preferred_end=time(11, 0))
        schedule.build([vet], time(7, 0), time(20, 0))
        assert schedule.get_placement("vet") == (time(10, 0), time(10, 30))

    def test_a_busy_preferred_window_slides_the_task_later_not_earlier(self):
        # "Without the middle try a 10am vet call whose window is busy would be
        # dragged back to breakfast time."
        schedule = make_schedule()
        blocker = make_task("blocker", is_fixed=True, duration_minutes=30,
                            preferred_start=time(10, 0), preferred_end=time(10, 30))
        vet = make_task("vet", duration_minutes=30,
                        preferred_start=time(10, 0), preferred_end=time(10, 30))
        schedule.build([blocker, vet], time(7, 0), time(20, 0))
        assert schedule.get_placement("vet") == (time(10, 30), time(11, 0))

    def test_a_task_that_cannot_fit_after_its_window_falls_back_to_anywhere(self):
        # the third and last try: "anywhere at all"
        schedule = make_schedule()
        errand = make_task("errand", duration_minutes=60,
                           preferred_start=time(19, 30), preferred_end=time(20, 0))
        schedule.build([errand], time(7, 0), time(20, 0))
        assert schedule.get_placement("errand") == (time(7, 0), time(8, 0))

    def test_a_task_longer_than_the_day_is_not_placed(self):
        schedule = make_schedule()
        impossible = make_task("impossible", duration_minutes=1000)
        schedule.build([impossible], time(7, 0), time(20, 0))
        assert schedule.unplaced_tasks()[0].task_id == "impossible"

    def test_a_task_starts_no_earlier_than_its_prerequisite_ends(self):
        # "nothing may start before the day does, or before its prerequisites end"
        schedule = make_schedule()
        breakfast = make_task("breakfast", is_fixed=True, duration_minutes=60,
                              preferred_start=time(8, 0), preferred_end=time(9, 0))
        medicine = make_task("medicine", duration_minutes=15,
                             depends_on=["breakfast"])
        schedule.build([breakfast, medicine], time(7, 0), time(20, 0))
        assert schedule.get_placement("medicine") == (time(9, 0), time(9, 15))

    def test_a_task_whose_prerequisite_never_got_placed_is_not_placed(self):
        # "a task whose prerequisites never got placed cannot be placed either"
        schedule = make_schedule()
        orphan = make_task("orphan", depends_on=["not_today"])
        schedule.build([orphan], time(7, 0), time(20, 0))
        assert schedule.contains_task("orphan") is False

    def test_placed_tasks_never_overlap_each_other(self):
        schedule = make_schedule()
        tasks = [make_task(f"t{n}", duration_minutes=60) for n in range(5)]
        schedule.build(tasks, time(7, 0), time(20, 0))
        windows = sorted(schedule.placements.values(), key=lambda pair: pair[0])
        for earlier, later in zip(windows, windows[1:]):
            assert overlaps(earlier[0], earlier[1], later[0], later[1]) is False


class TestIsFree:
    """is_free answers whether a window is still open."""

    def test_an_empty_schedule_is_free(self):
        schedule = make_schedule()
        assert schedule.is_free(time(9, 0), time(10, 0)) is True

    def test_an_occupied_window_is_not_free(self):
        schedule = make_schedule()
        schedule.placements["walk"] = (time(9, 0), time(10, 0))
        assert schedule.is_free(time(9, 30), time(10, 30)) is False

    def test_a_window_that_only_touches_a_placement_is_still_free(self):
        schedule = make_schedule()
        schedule.placements["walk"] = (time(9, 0), time(10, 0))
        assert schedule.is_free(time(10, 0), time(11, 0)) is True


# ---------------------------------------------------------------------------
# Schedule -- build() and the views over the result
# ---------------------------------------------------------------------------

class TestBuildAndViews:
    """build(), placed_tasks(), unplaced_tasks(), tasks_at() and friends."""

    def test_building_twice_does_not_stack_the_old_plan_under_the_new_one(self):
        schedule = make_schedule()
        walk = make_task("walk", duration_minutes=60)
        schedule.build([walk], time(7, 0), time(20, 0))
        schedule.build([walk], time(7, 0), time(20, 0))
        assert len(schedule.placements) == 1

    def test_build_remembers_the_awake_window_it_was_handed(self):
        schedule = make_schedule()
        schedule.build([], time(6, 30), time(22, 0))
        assert (schedule.wake_time, schedule.sleep_time) == (time(6, 30), time(22, 0))

    def test_build_keeps_every_task_it_was_given_placed_or_not(self):
        # "every task build() was given to consider, placed or not"
        schedule = make_schedule()
        tasks = [make_task("fits", duration_minutes=30),
                 make_task("too_big", duration_minutes=1000)]
        schedule.build(tasks, time(7, 0), time(20, 0))
        assert len(schedule.tasks) == 2

    def test_placed_tasks_come_back_in_time_order(self):
        schedule = make_schedule("earliest")
        late = make_task("late", duration_minutes=30, preferred_start=time(15, 0))
        early = make_task("early", duration_minutes=30, preferred_start=time(8, 0))
        schedule.build([late, early], time(7, 0), time(20, 0))
        assert [task.task_id for task in schedule.placed_tasks()] == ["early", "late"]

    def test_unplaced_tasks_lists_what_did_not_fit(self):
        schedule = make_schedule()
        schedule.build([make_task("too_big", duration_minutes=1000)],
                       time(7, 0), time(20, 0))
        assert [task.task_id for task in schedule.unplaced_tasks()] == ["too_big"]

    def test_blocked_tasks_are_the_ones_waiting_on_a_missing_prerequisite(self):
        # blocked is "as opposed to simply running out of room"
        schedule = make_schedule()
        blocked = make_task("blocked", depends_on=["not_today"])
        no_room = make_task("no_room", duration_minutes=1000)
        schedule.build([blocked, no_room], time(7, 0), time(20, 0))
        assert [task.task_id for task in schedule.blocked_tasks()] == ["blocked"]

    def test_contains_task_reports_whether_a_task_got_a_slot(self):
        schedule = make_schedule()
        schedule.build([make_task("walk", duration_minutes=30)], time(7, 0), time(20, 0))
        assert schedule.contains_task("walk") is True
        assert schedule.contains_task("nap") is False

    def test_get_task_finds_a_considered_task(self):
        schedule = make_schedule()
        schedule.build([make_task("walk")], time(7, 0), time(20, 0))
        found = schedule.get_task("walk")
        assert found is not None and found.task_id == "walk"

    def test_get_task_returns_none_for_a_task_never_considered(self):
        schedule = make_schedule()
        schedule.build([make_task("walk")], time(7, 0), time(20, 0))
        assert schedule.get_task("nap") is None

    def test_get_placement_returns_none_for_an_unplaced_task(self):
        schedule = make_schedule()
        schedule.build([make_task("too_big", duration_minutes=1000)],
                       time(7, 0), time(20, 0))
        assert schedule.get_placement("too_big") is None

    def test_tasks_at_answers_what_am_i_doing_right_now(self):
        schedule = make_schedule()
        walk = make_task("walk", duration_minutes=60, is_fixed=True,
                         preferred_start=time(9, 0), preferred_end=time(10, 0))
        schedule.build([walk], time(7, 0), time(20, 0))
        assert [task.task_id for task in schedule.tasks_at(time(9, 30))] == ["walk"]

    def test_a_task_that_ends_at_the_given_moment_is_over(self):
        # "a task that ends at 3pm is over, so the end is not included"
        schedule = make_schedule()
        walk = make_task("walk", duration_minutes=60, is_fixed=True,
                         preferred_start=time(9, 0), preferred_end=time(10, 0))
        schedule.build([walk], time(7, 0), time(20, 0))
        assert schedule.tasks_at(time(10, 0)) == []

    def test_tasks_at_includes_the_first_minute(self):
        schedule = make_schedule()
        walk = make_task("walk", duration_minutes=60, is_fixed=True,
                         preferred_start=time(9, 0), preferred_end=time(10, 0))
        schedule.build([walk], time(7, 0), time(20, 0))
        assert len(schedule.tasks_at(time(9, 0))) == 1

    def test_tasks_in_window_shows_one_slice_of_the_day(self):
        schedule = make_schedule()
        morning = make_task("morning", duration_minutes=60, is_fixed=True,
                            preferred_start=time(8, 0), preferred_end=time(9, 0))
        evening = make_task("evening", duration_minutes=60, is_fixed=True,
                            preferred_start=time(18, 0), preferred_end=time(19, 0))
        schedule.build([morning, evening], time(7, 0), time(20, 0))
        found = schedule.tasks_in_window(time(7, 0), time(12, 0))
        assert [task.task_id for task in found] == ["morning"]


class TestEarliestStartFor:
    """earliest_start_for is the floor place_task searches from."""

    def test_no_prerequisites_means_no_floor(self):
        schedule = make_schedule()
        assert schedule.earliest_start_for(make_task("walk")) is None

    def test_the_floor_is_the_end_of_the_latest_prerequisite(self):
        schedule = make_schedule()
        schedule.placements["early"] = (time(8, 0), time(9, 0))
        schedule.placements["late"] = (time(11, 0), time(12, 0))
        task = make_task("after", depends_on=["early", "late"])
        assert schedule.earliest_start_for(task) == time(12, 0)

    def test_prerequisites_that_are_not_placed_yet_are_skipped(self):
        schedule = make_schedule()
        schedule.placements["placed"] = (time(8, 0), time(9, 0))
        task = make_task("after", depends_on=["placed", "not_placed"])
        assert schedule.earliest_start_for(task) == time(9, 0)


class TestDependenciesMet:
    """dependencies_met decides whether a task is allowed to be placed yet."""

    def test_a_task_with_no_prerequisites_is_always_allowed(self):
        assert make_schedule().dependencies_met(make_task("walk")) is True

    def test_a_task_is_allowed_once_its_prerequisites_are_placed(self):
        schedule = make_schedule()
        schedule.placements["breakfast"] = (time(8, 0), time(8, 30))
        assert schedule.dependencies_met(make_task("medicine",
                                                   depends_on=["breakfast"])) is True

    def test_a_task_is_held_back_while_a_prerequisite_is_missing(self):
        schedule = make_schedule()
        assert schedule.dependencies_met(make_task("medicine",
                                                   depends_on=["breakfast"])) is False


# ---------------------------------------------------------------------------
# Schedule -- summary() and explain()
# ---------------------------------------------------------------------------

class TestSummaryAndExplain:
    """summary() is the headline numbers; explain() is the plain-language story."""

    def build_mixed_day(self):
        schedule = make_schedule()
        walk = make_task("walk", title="Walk Mochi", duration_minutes=60)
        blocked = make_task("blocked", title="Give medicine",
                            depends_on=["not_today"])
        no_room = make_task("no_room", title="Repaint the house",
                            duration_minutes=1000)
        schedule.build([walk, blocked, no_room], time(7, 0), time(20, 0))
        return schedule

    def test_summary_counts_what_was_considered_placed_and_dropped(self):
        numbers = self.build_mixed_day().summary()
        assert numbers["tasks_considered"] == 3
        assert numbers["tasks_placed"] == 1
        assert numbers["tasks_dropped"] == 2
        assert numbers["tasks_blocked"] == 1

    def test_summary_adds_up_the_minutes_booked(self):
        numbers = self.build_mixed_day().summary()
        assert numbers["minutes_booked"] == 60

    def test_free_minutes_are_the_awake_window_minus_what_is_booked(self):
        numbers = self.build_mixed_day().summary()
        assert numbers["minutes_free"] == (13 * 60) - 60

    def test_summary_carries_the_schedules_own_labels(self):
        numbers = self.build_mixed_day().summary()
        assert numbers["schedule_id"] == "test-plan"
        assert numbers["label"] == "Test Plan"
        assert numbers["strategy"] == "priority"

    def test_explain_lists_the_planned_tasks(self):
        text = self.build_mixed_day().explain()
        assert "Planned:" in text
        assert "Walk Mochi" in text

    def test_explain_separates_blocked_tasks_from_tasks_with_no_room(self):
        # "dropped for lack of room is a different story from dropped for a
        # missing prerequisite, so the two are listed separately"
        text = self.build_mixed_day().explain()
        assert "Waiting on something that never got scheduled:" in text
        assert "needs not_today first" in text
        assert "Left out, no room in the day:" in text
        assert "Repaint the house -- needs 1000 min" in text

    def test_explain_says_so_when_nothing_could_be_planned(self):
        schedule = make_schedule()
        schedule.build([make_task("too_big", duration_minutes=1000)],
                       time(7, 0), time(20, 0))
        assert "Nothing could be planned for this day." in schedule.explain()

    def test_explain_credits_a_fixed_task_for_being_immovable(self):
        schedule = make_schedule()
        work = make_task("work", title="Work", is_fixed=True, duration_minutes=480,
                         preferred_start=time(9, 0), preferred_end=time(17, 0))
        schedule.build([work], time(7, 0), time(20, 0))
        assert "fixed commitment, everything else worked around it" in schedule.explain()

    def test_explain_says_when_a_task_got_the_time_it_asked_for(self):
        schedule = make_schedule()
        vet = make_task("vet", title="Vet call", duration_minutes=30,
                        preferred_start=time(10, 0), preferred_end=time(11, 0))
        schedule.build([vet], time(7, 0), time(20, 0))
        assert "got the time you asked for" in schedule.explain()

    def test_explain_says_when_a_preferred_window_was_full(self):
        schedule = make_schedule()
        blocker = make_task("blocker", is_fixed=True, duration_minutes=30,
                            preferred_start=time(10, 0), preferred_end=time(10, 30))
        vet = make_task("vet", title="Vet call", duration_minutes=30,
                        preferred_start=time(10, 0), preferred_end=time(10, 30))
        schedule.build([blocker, vet], time(7, 0), time(20, 0))
        assert "asked for 10:00, that window was full" in schedule.explain()

    def test_explain_points_at_the_prerequisite_that_set_the_start_time(self):
        schedule = make_schedule()
        breakfast = make_task("breakfast", is_fixed=True, duration_minutes=60,
                              preferred_start=time(8, 0), preferred_end=time(9, 0))
        medicine = make_task("medicine", duration_minutes=15, depends_on=["breakfast"])
        schedule.build([breakfast, medicine], time(7, 0), time(20, 0))
        assert "could not start before 09:00" in schedule.explain()

    def test_explain_falls_back_to_the_strategy_for_an_untimed_task(self):
        schedule = make_schedule("priority")
        schedule.build([make_task("walk", duration_minutes=30)], time(7, 0), time(20, 0))
        assert "no time preference, placed by priority" in schedule.explain()


# ---------------------------------------------------------------------------
# User -- pets
# ---------------------------------------------------------------------------

class TestUserPets:
    """add_pet builds the Pet for the caller; the lookups are built on pet ids."""

    def test_add_pet_builds_the_pet_and_hands_it_back(self, owner):
        pet = owner.add_pet("pet_3", "Nibbles", "rabbit", 1, "shy")
        assert isinstance(pet, Pet)
        assert pet.name == "Nibbles"
        assert pet in owner.pets

    def test_a_duplicate_pet_id_is_refused(self, owner):
        # "two pets sharing an id would make get_pet ambiguous"
        with pytest.raises(ValueError):
            owner.add_pet("pet_1", "Copycat", "cat", 5)

    def test_get_pet_finds_a_pet_by_id(self, owner):
        assert owner.get_pet("pet_1").name == "Mochi"

    def test_get_pet_returns_none_when_there_is_no_such_pet(self, owner):
        assert owner.get_pet("pet_99") is None

    def test_tasks_for_pet_shows_one_animals_day(self, owner):
        mochi = owner.get_pet("pet_1")
        owner.add_task(make_task("walk", pets=[mochi]))
        owner.add_task(make_task("litter", pets=[owner.get_pet("pet_2")]))
        assert [task.task_id for task in owner.tasks_for_pet("pet_1")] == ["walk"]

    def test_tasks_for_species_covers_every_animal_of_that_kind(self, owner):
        owner.add_pet("pet_3", "Luna", "cat", 4)
        owner.add_task(make_task("litter", pets=[owner.get_pet("pet_2")]))
        owner.add_task(make_task("brush", pets=[owner.get_pet("pet_3")]))
        owner.add_task(make_task("walk", pets=[owner.get_pet("pet_1")]))
        found = [task.task_id for task in owner.tasks_for_species("cat")]
        assert found == ["litter", "brush"]

    def test_a_task_shared_by_two_cats_is_still_listed_once(self, owner):
        # "a task shared by two cats should still be listed once"
        owner.add_pet("pet_3", "Luna", "cat", 4)
        shared = make_task("feed", pets=[owner.get_pet("pet_2"), owner.get_pet("pet_3")])
        owner.add_task(shared)
        assert len(owner.tasks_for_species("cat")) == 1

    def test_tasks_by_pet_lists_a_shared_task_under_both_pets(self, owner):
        # "A task shared by two pets appears under both"
        shared = make_task("vet", pets=[owner.get_pet("pet_1"), owner.get_pet("pet_2")])
        owner.add_task(shared)
        grouped = owner.tasks_by_pet()
        assert grouped["pet_1"] == [shared]
        assert grouped["pet_2"] == [shared]

    def test_a_pet_with_nothing_to_do_still_gets_an_empty_day(self, owner):
        # "a pet with nothing to do shows an empty day rather than disappearing"
        owner.add_task(make_task("walk", pets=[owner.get_pet("pet_1")]))
        assert owner.tasks_by_pet()["pet_2"] == []

    def test_personal_tasks_are_the_complement_of_the_pet_tasks(self, owner):
        owner.add_task(make_task("walk", pets=[owner.get_pet("pet_1")]))
        owner.add_task(make_task("groceries"))
        assert [task.task_id for task in owner.personal_tasks()] == ["groceries"]


# ---------------------------------------------------------------------------
# User -- tasks
# ---------------------------------------------------------------------------

class TestUserTasks:
    """add_task, get_task, delete_task and the small editors."""

    def test_add_task_stores_the_task(self, owner):
        owner.add_task(make_task("walk"))
        found = owner.get_task("walk")
        assert found is not None and found.task_id == "walk"

    def test_a_duplicate_task_id_is_refused(self, owner):
        # "a duplicate id would let one task overwrite the other's slot"
        owner.add_task(make_task("walk"))
        with pytest.raises(ValueError):
            owner.add_task(make_task("walk"))

    def test_get_task_returns_none_when_there_is_no_such_task(self, owner):
        assert owner.get_task("nope") is None

    def test_delete_task_removes_it_from_the_list(self, owner):
        owner.add_task(make_task("walk"))
        owner.delete_task("walk")
        assert owner.get_task("walk") is None

    def test_delete_task_also_clears_the_id_from_other_tasks(self, owner):
        # "a leftover id points at a task that no longer exists, and the dependent
        # task would wait on a prerequisite that can never be placed"
        owner.add_task(make_task("breakfast"))
        owner.add_task(make_task("medicine"))
        owner.set_dependency("medicine", "breakfast")
        owner.delete_task("breakfast")
        medicine = owner.get_task("medicine")
        assert medicine is not None and medicine.depends_on == []

    def test_set_priority_changes_how_important_a_task_is(self, owner):
        owner.add_task(make_task("walk", priority=1))
        owner.set_priority("walk", 5)
        walk = owner.get_task("walk")
        assert walk is not None and walk.priority == 5

    def test_set_priority_on_an_unknown_task_is_harmless(self, owner):
        owner.set_priority("nope", 5)  # must not raise

    def test_set_time_preference_sets_the_window_and_the_duration(self, owner):
        owner.add_task(make_task("vet"))
        owner.set_time_preference("vet", (time(10, 0), time(11, 0)), 45)
        vet = owner.get_task("vet")
        assert (vet.preferred_start, vet.preferred_end) == (time(10, 0), time(11, 0))
        assert vet.duration_minutes == 45

    def test_set_time_preference_on_an_unknown_task_is_harmless(self, owner):
        owner.set_time_preference("nope", (time(10, 0), time(11, 0)), 45)


# ---------------------------------------------------------------------------
# User -- dependencies and cycles
# ---------------------------------------------------------------------------

class TestUserDependencies:
    """set_dependency refuses loops; creates_cycle is what it checks with."""

    @pytest.fixture
    def chain(self, owner):
        owner.add_task(make_task("breakfast"))
        owner.add_task(make_task("medicine"))
        owner.add_task(make_task("walk"))
        return owner

    def test_set_dependency_links_two_tasks(self, chain):
        chain.set_dependency("medicine", "breakfast")
        medicine = chain.get_task("medicine")
        assert medicine is not None and medicine.depends_on == ["breakfast"]

    def test_set_dependency_ignores_an_unknown_task(self, chain):
        chain.set_dependency("nope", "breakfast")
        chain.set_dependency("medicine", "nope")
        medicine = chain.get_task("medicine")
        assert medicine is not None and medicine.depends_on == []

    def test_a_task_cannot_come_before_itself(self, chain):
        # "a task that has to come before itself is the smallest possible loop"
        with pytest.raises(ValueError):
            chain.set_dependency("walk", "walk")

    def test_a_two_step_loop_is_refused(self, chain):
        chain.set_dependency("medicine", "breakfast")
        with pytest.raises(ValueError):
            chain.set_dependency("breakfast", "medicine")

    def test_a_longer_loop_is_refused(self, chain):
        # "Walk back through everything the prerequisite is itself waiting on"
        chain.set_dependency("medicine", "breakfast")
        chain.set_dependency("walk", "medicine")
        with pytest.raises(ValueError):
            chain.set_dependency("breakfast", "walk")

    def test_the_refused_link_never_gets_added(self, chain):
        chain.set_dependency("medicine", "breakfast")
        with pytest.raises(ValueError):
            chain.set_dependency("breakfast", "medicine")
        breakfast = chain.get_task("breakfast")
        assert breakfast is not None and breakfast.depends_on == []

    def test_creates_cycle_says_no_for_an_unrelated_pair(self, chain):
        assert chain.creates_cycle("walk", "breakfast") is False

    def test_clear_dependency_frees_the_scheduler(self, chain):
        chain.set_dependency("medicine", "breakfast")
        chain.clear_dependency("medicine", "breakfast")
        medicine = chain.get_task("medicine")
        assert medicine is not None and medicine.has_dependencies() is False

    def test_clear_dependency_on_an_unknown_task_is_harmless(self, chain):
        chain.clear_dependency("nope", "breakfast")

    def test_dependencies_of_returns_the_prerequisite_tasks(self, chain):
        chain.set_dependency("medicine", "breakfast")
        found = chain.dependencies_of("medicine")
        assert [task.task_id for task in found] == ["breakfast"]

    def test_dependencies_of_an_unknown_task_is_empty(self, chain):
        assert chain.dependencies_of("nope") == []


# ---------------------------------------------------------------------------
# User -- fixed events and the awake window
# ---------------------------------------------------------------------------

class TestUserEvents:
    """add_event adds a commitment the scheduler must plan around."""

    def test_an_event_is_a_fixed_task_with_the_given_window(self, owner):
        owner.add_event("Work", time(9, 0), time(17, 0))
        event = owner.tasks[0]
        assert event.is_fixed is True
        assert event.category == "event"
        assert (event.preferred_start, event.preferred_end) == (time(9, 0), time(17, 0))

    def test_an_events_duration_is_the_length_of_its_window(self, owner):
        owner.add_event("Work", time(9, 0), time(17, 0))
        assert owner.tasks[0].duration_minutes == 480

    def test_events_are_numbered_in_order(self, owner):
        owner.add_event("Work", time(9, 0), time(17, 0))
        owner.add_event("Class", time(18, 0), time(19, 0))
        assert [task.task_id for task in owner.tasks] == ["event_1", "event_2"]

    def test_a_new_event_skips_an_id_still_in_use(self, owner):
        # "so deleting an event does not cause the next one to collide with a
        # name still in use"
        owner.add_event("Work", time(9, 0), time(17, 0))
        owner.add_event("Class", time(18, 0), time(19, 0))
        owner.delete_task("event_1")
        owner.add_event("Gym", time(7, 30), time(8, 30))
        second, third = owner.get_task("event_2"), owner.get_task("event_3")
        assert second is not None and second.title == "Class"
        assert third is not None and third.title == "Gym"

    def test_an_event_is_not_a_pet_task(self, owner):
        owner.add_event("Work", time(9, 0), time(17, 0))
        assert owner.tasks[0].is_pet_task() is False

    def test_awake_window_is_the_pair_the_scheduler_may_use(self, owner):
        assert owner.awake_window() == (time(7, 0), time(20, 0))


# ---------------------------------------------------------------------------
# User -- the request / compare / save workflow
# ---------------------------------------------------------------------------

class TestUserWorkflow:
    """request a schedule, request an alternative, compare, then save one."""

    @pytest.fixture
    def busy(self, owner):
        owner.add_task(make_task("walk", title="Walk Mochi", priority=5,
                                 duration_minutes=60, pets=[owner.get_pet("pet_1")]))
        owner.add_task(make_task("litter", title="Litter box", priority=2,
                                 duration_minutes=10, pets=[owner.get_pet("pet_2")]))
        owner.add_event("Work", time(9, 0), time(17, 0))
        return owner

    def test_request_schedule_builds_and_keeps_plan_a(self, busy):
        plan = busy.request_schedule("priority")
        assert plan.schedule_id == "plan-a"
        assert plan.strategy == "priority"
        assert busy.candidates == [plan]

    def test_the_plans_label_names_the_strategy(self, busy):
        assert busy.request_schedule("shortest").label == "Plan A (shortest)"

    def test_a_plan_is_built_over_the_users_tasks_and_awake_window(self, busy):
        plan = busy.request_schedule("priority")
        assert len(plan.tasks) == len(busy.tasks)
        assert (plan.wake_time, plan.sleep_time) == busy.awake_window()

    def test_asking_for_a_first_plan_again_starts_the_comparison_over(self, busy):
        busy.request_schedule("priority")
        busy.request_alternative("shortest")
        busy.request_schedule("longest")
        assert [plan.schedule_id for plan in busy.candidates] == ["plan-a"]

    def test_request_alternative_adds_a_second_plan_to_compare(self, busy):
        busy.request_schedule("priority")
        alternative = busy.request_alternative("shortest")
        assert alternative.schedule_id == "plan-b"
        assert len(busy.candidates) == 2

    def test_an_alternative_with_nothing_to_compare_to_becomes_plan_a(self, busy):
        # "nothing to be an alternative to yet"
        plan = busy.request_alternative("shortest")
        assert plan.schedule_id == "plan-a"
        assert len(busy.candidates) == 1

    def test_a_new_alternative_replaces_the_old_one(self, busy):
        # "there are only ever two candidates"
        busy.request_schedule("priority")
        busy.request_alternative("shortest")
        busy.request_alternative("longest")
        assert len(busy.candidates) == 2
        assert busy.candidates[1].strategy == "longest"

    def test_compare_says_so_when_there_are_no_plans(self, owner):
        assert owner.compare_candidates() == "No plans yet -- ask for a schedule first."

    def test_compare_with_one_plan_asks_for_an_alternative(self, busy):
        busy.request_schedule("priority")
        text = busy.compare_candidates()
        assert "Ask for an alternative to have something to compare this to." in text

    def test_compare_shows_both_plans_and_how_to_choose(self, busy):
        busy.request_schedule("priority")
        busy.request_alternative("shortest")
        text = busy.compare_candidates()
        assert "Plan A (priority)" in text
        assert "Plan B (shortest)" in text
        assert "Choosing between them:" in text

    def test_compare_says_when_both_plans_fit_the_same_tasks(self, busy):
        # "Both plans fit the same tasks -- only the order differs."
        busy.request_schedule("priority")
        busy.request_alternative("shortest")
        assert "only the order differs" in busy.compare_candidates()

    def test_compare_names_a_task_only_one_plan_made_room_for(self, owner):
        # "what settles the choice is which tasks one plan made room for and the
        # other did not"
        owner.add_task(make_task("huge", title="Huge job", priority=1,
                                 duration_minutes=700))
        owner.add_task(make_task("small", title="Small job", priority=9,
                                 duration_minutes=600))
        owner.request_schedule("priority")   # small first, then huge will not fit
        owner.request_alternative("longest")  # huge first, then small will not fit
        text = owner.compare_candidates()
        assert "Only Plan A (priority) fits: Small job" in text
        assert "Only Plan B (longest) fits: Huge job" in text

    def test_choose_schedule_saves_the_plan_the_user_picked(self, busy):
        busy.request_schedule("priority")
        busy.request_alternative("shortest")
        chosen = busy.choose_schedule("plan-b")
        assert chosen.is_saved is True
        assert busy.get_saved_schedule() is chosen

    def test_choosing_again_unsaves_the_plan_it_replaces(self, busy):
        # "there is no history, so the plan being replaced stops being saved"
        busy.request_schedule("priority")
        busy.request_alternative("shortest")
        first = busy.choose_schedule("plan-a")
        busy.choose_schedule("plan-b")
        assert first.is_saved is False
        assert busy.get_saved_schedule().schedule_id == "plan-b"

    def test_choosing_a_plan_that_is_not_on_offer_is_refused(self, busy):
        busy.request_schedule("priority")
        with pytest.raises(ValueError):
            busy.choose_schedule("plan-z")

    def test_there_is_no_saved_schedule_until_one_is_chosen(self, busy):
        busy.request_schedule("priority")
        assert busy.get_saved_schedule() is None

    def test_discard_unchosen_drops_the_plans_the_user_did_not_pick(self, busy):
        busy.request_schedule("priority")
        busy.request_alternative("shortest")
        busy.discard_unchosen("plan-a")
        assert [plan.schedule_id for plan in busy.candidates] == ["plan-a"]


# ---------------------------------------------------------------------------
# a whole day, end to end
# ---------------------------------------------------------------------------

class TestWholeDay:
    """One realistic day exercising the pieces together, the way main.py does."""

    @pytest.fixture
    def day(self, owner):
        mochi = owner.get_pet("pet_1")
        whiskers = owner.get_pet("pet_2")
        owner.add_event("Work", time(9, 0), time(17, 0))
        owner.add_task(make_task("breakfast", title="Feed the pets", priority=5,
                                 duration_minutes=15, preferred_start=time(7, 30),
                                 pets=[mochi, whiskers]))
        owner.add_task(make_task("medicine", title="Give Mochi medicine", priority=5,
                                 duration_minutes=5, pets=[mochi]))
        owner.add_task(make_task("walk", title="Evening walk", priority=4,
                                 duration_minutes=45, preferred_start=time(17, 30),
                                 pets=[mochi]))
        owner.set_dependency("medicine", "breakfast")
        return owner

    def test_the_fixed_event_keeps_its_own_hours(self, day):
        plan = day.request_schedule("priority")
        assert plan.get_placement("event_1") == (time(9, 0), time(17, 0))

    def test_medicine_lands_after_breakfast(self, day):
        plan = day.request_schedule("priority")
        breakfast = plan.get_placement("breakfast")
        medicine = plan.get_placement("medicine")
        assert breakfast is not None and medicine is not None
        assert to_minutes(medicine[0]) >= to_minutes(breakfast[1])

    def test_nothing_is_scheduled_during_work(self, day):
        plan = day.request_schedule("priority")
        during_work = plan.tasks_in_window(time(9, 0), time(17, 0))
        assert [task.task_id for task in during_work] == ["event_1"]

    def test_every_task_fits_in_this_day(self, day):
        plan = day.request_schedule("priority")
        assert plan.unplaced_tasks() == []

    def test_the_explanation_mentions_every_placed_task(self, day):
        plan = day.request_schedule("priority")
        text = plan.explain()
        for task in plan.placed_tasks():
            assert task.title in text

    def test_the_day_can_be_planned_compared_and_saved(self, day):
        day.request_schedule("priority")
        day.request_alternative("earliest")
        assert "Choosing between them:" in day.compare_candidates()
        saved = day.choose_schedule("plan-b")
        day.discard_unchosen("plan-b")
        assert day.get_saved_schedule() is saved
        assert [plan.schedule_id for plan in day.candidates] == ["plan-b"]
