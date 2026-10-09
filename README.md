# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
Owner Information:
Name: John Doe
Awake: 07:00 to 20:00

Pets Information:
Name: Buddy, Species: dog, Age: 3, Notes: golden retriever
Name: Whiskers, Species: cat, Age: 2, Notes: siamese

Tasks for Buddy:
  Take Buddy for a walk (exercise, 60 min, priority 4) for Buddy
  Feed Buddy (feeding, 15 min, priority 5) for Buddy
  Play fetch with Buddy (playtime, 30 min, priority 3) for Buddy
  Give Buddy a bath (grooming, 30 min, priority 3) for Buddy after task_1 (weekly on Sat)

Tasks for Whiskers:
  Clean Whiskers' litter box (cleaning, 10 min, priority 3) for Whiskers
  Feed Whiskers (feeding, 15 min, priority 5) for Whiskers

Tasks for Owner:
  Schedule vet appointment for Buddy (errand, 10 min, priority 4) (once on 2026-10-05)
  Buy pet food (errand, 55 min, priority 2) (weekly on Sat)
  Morning class (event, 90 min, priority 5) [fixed] (weekly on Mon, Wed, Fri)

On Monday 2026-10-05:
  Take Buddy for a walk (daily)
  Feed Buddy (daily)
  Play fetch with Buddy (daily)
  Clean Whiskers' litter box (daily)
  Feed Whiskers (daily)
  Schedule vet appointment for Buddy (once on 2026-10-05)
  Morning class (weekly on Mon, Wed, Fri)

On Saturday 2026-10-10:
  Take Buddy for a walk (daily)
  Feed Buddy (daily)
  Play fetch with Buddy (daily)
  Clean Whiskers' litter box (daily)
  Feed Whiskers (daily)
  Give Buddy a bath (weekly on Sat)
  Buy pet food (weekly on Sat)

Building the PawPal System for Monday...
Plan A (priority) (2026-10-05) -- sorted by priority
7 of 7 tasks placed, 230 minutes booked, 550 minutes free.

Planned:
  07:00-08:00  Take Buddy for a walk (exercise, 60 min, priority 4) for Buddy -- no time preference, placed by priority
  08:00-09:30  Morning class (event, 90 min, priority 5) [fixed] (weekly on Mon, Wed, Fri) -- fixed commitment, everything else worked around it
  09:30-09:40  Clean Whiskers' litter box (cleaning, 10 min, priority 3) for Whiskers -- no time preference, placed by priority
  10:00-10:10  Schedule vet appointment for Buddy (errand, 10 min, priority 4) (once on 2026-10-05) -- got the time you asked for
  11:00-11:30  Play fetch with Buddy (playtime, 30 min, priority 3) for Buddy -- got the time you asked for
  13:00-13:15  Feed Buddy (feeding, 15 min, priority 5) for Buddy -- got the time you asked for
  13:15-13:30  Feed Whiskers (feeding, 15 min, priority 5) for Whiskers -- asked for 13:00, that window was full

Building an alternative plan...
Plan B (shortest) (2026-10-05) -- sorted by shortest
7 of 7 tasks placed, 230 minutes booked, 550 minutes free.

Planned:
  07:00-07:10  Clean Whiskers' litter box (cleaning, 10 min, priority 3) for Whiskers -- no time preference, placed by shortest
  08:00-09:30  Morning class (event, 90 min, priority 5) [fixed] (weekly on Mon, Wed, Fri) -- fixed commitment, everything else worked around it
  10:00-10:10  Schedule vet appointment for Buddy (errand, 10 min, priority 4) (once on 2026-10-05) -- got the time you asked for
  11:00-11:30  Play fetch with Buddy (playtime, 30 min, priority 3) for Buddy -- got the time you asked for
  11:30-12:30  Take Buddy for a walk (exercise, 60 min, priority 4) for Buddy -- no time preference, placed by shortest
  13:00-13:15  Feed Buddy (feeding, 15 min, priority 5) for Buddy -- got the time you asked for
  13:15-13:30  Feed Whiskers (feeding, 15 min, priority 5) for Whiskers -- asked for 13:00, that window was full

Comparing the plans:
Plan A (priority) (2026-10-05) -- sorted by priority
7 of 7 tasks placed, 230 minutes booked, 550 minutes free.

Planned:
  07:00-08:00  Take Buddy for a walk (exercise, 60 min, priority 4) for Buddy -- no time preference, placed by priority
  08:00-09:30  Morning class (event, 90 min, priority 5) [fixed] (weekly on Mon, Wed, Fri) -- fixed commitment, everything else worked around it
  09:30-09:40  Clean Whiskers' litter box (cleaning, 10 min, priority 3) for Whiskers -- no time preference, placed by priority
  10:00-10:10  Schedule vet appointment for Buddy (errand, 10 min, priority 4) (once on 2026-10-05) -- got the time you asked for
  11:00-11:30  Play fetch with Buddy (playtime, 30 min, priority 3) for Buddy -- got the time you asked for
  13:00-13:15  Feed Buddy (feeding, 15 min, priority 5) for Buddy -- got the time you asked for
  13:15-13:30  Feed Whiskers (feeding, 15 min, priority 5) for Whiskers -- asked for 13:00, that window was full

============================================================

Plan B (shortest) (2026-10-05) -- sorted by shortest
7 of 7 tasks placed, 230 minutes booked, 550 minutes free.

Planned:
  07:00-07:10  Clean Whiskers' litter box (cleaning, 10 min, priority 3) for Whiskers -- no time preference, placed by shortest
  08:00-09:30  Morning class (event, 90 min, priority 5) [fixed] (weekly on Mon, Wed, Fri) -- fixed commitment, everything else worked around it
  10:00-10:10  Schedule vet appointment for Buddy (errand, 10 min, priority 4) (once on 2026-10-05) -- got the time you asked for
  11:00-11:30  Play fetch with Buddy (playtime, 30 min, priority 3) for Buddy -- got the time you asked for
  11:30-12:30  Take Buddy for a walk (exercise, 60 min, priority 4) for Buddy -- no time preference, placed by shortest
  13:00-13:15  Feed Buddy (feeding, 15 min, priority 5) for Buddy -- got the time you asked for
  13:15-13:30  Feed Whiskers (feeding, 15 min, priority 5) for Whiskers -- asked for 13:00, that window was full

============================================================

Choosing between them:
  Both plans fit the same tasks -- only the order differs.
  Plan A (priority): 7 placed, 0 left out, 550 minutes free
  Plan B (shortest): 7 placed, 0 left out, 550 minutes free

Saved plan: Plan A (priority) for 2026-10-05 (is_saved=True)

Building the PawPal System for Saturday...
Plan A (priority) (2026-10-10) -- sorted by priority
7 of 7 tasks placed, 215 minutes booked, 565 minutes free.

Planned:
  07:00-08:00  Take Buddy for a walk (exercise, 60 min, priority 4) for Buddy -- no time preference, placed by priority
  08:00-08:10  Clean Whiskers' litter box (cleaning, 10 min, priority 3) for Whiskers -- no time preference, placed by priority
  08:10-09:05  Buy pet food (errand, 55 min, priority 2) (weekly on Sat) -- no time preference, placed by priority
  10:00-10:30  Give Buddy a bath (grooming, 30 min, priority 3) for Buddy after task_1 (weekly on Sat) -- got the time you asked for
  11:00-11:30  Play fetch with Buddy (playtime, 30 min, priority 3) for Buddy -- got the time you asked for
  13:00-13:15  Feed Buddy (feeding, 15 min, priority 5) for Buddy -- got the time you asked for
  13:15-13:30  Feed Whiskers (feeding, 15 min, priority 5) for Whiskers -- asked for 13:00, that window was full
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here

test_pawpalpy .............................................................................................................................................. [ 64%]
.......................................................................                                                                                                                                                        [100%]

======================================================================= 185 passed in 1.55s ========================================================================
```

## 📐 Smarter Scheduling

> Fill in once you've implemented scheduling logic.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | Two plans, one by priority, and other by duration | Plans do not override recurring tasks, set events, or preferred time slots|
| Filtering | Time based sorting | Keeps everything chronological|
| Conflict handling | Preferred time vs Priority | Tasks with a preferred time are placed in the spot, only if another of its kind doesn't have a higher priority rating|
| Recurring tasks | Daily vs. weekly | Daily tasks have to be placed everyday, and weekly tasks have to happen at least once in the schedule. These two cannot be discarded by the scheduler|

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. User logs all of their pets that will be considered during scheduling
2. User logs the time they will be awake to do the tasks
3. User will add tasks based on the pet, date, daily or weekly, preferred starting time (if any), priority, and possible duration
4. User will add conflicting tasks they need to do that may or may not be flexible
5. When the User submits these tasks to the scheduler, they will recieve two different plans based on what the schedule could fit
6. User chooses which schedule they prefer, saving it and discarding the other

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
