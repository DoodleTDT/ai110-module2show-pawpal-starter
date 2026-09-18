# Import classes from pawpal_system.py
from datetime import time
from pawpal_system import Task
from pawpal_system import User

# Create an instance of a user (pet owner)
owner = User("John Doe", time(7, 0), time(20, 0))

# Create instances of at least two pets
pet1 = owner.add_pet("pet_1", "Buddy", "dog", 3, "golden retriever")
pet2 = owner.add_pet("pet_2", "Whiskers", "cat", 2, "siamese")

# Display the owner's information and their pets
wake_time, sleep_time = owner.awake_window()
print("Owner Information:")
print(f"Name: {owner.name}")
print(f"Awake: {wake_time.strftime('%H:%M')} to {sleep_time.strftime('%H:%M')}")

print("\nPets Information:")
for pet in owner.pets:
    print(f"Name: {pet.name}, Species: {pet.species}, Age: {pet.age}, Notes: {pet.notes}")

# Create two tasks per pet
owner.add_task(
    Task(
        task_id="task_1",
        title="Take Buddy for a walk",
        category="exercise",
        priority=4,
        duration_minutes=60,
        pets=[pet1],
    )
)
owner.add_task(
    Task(
        task_id="task_2",
        title="Feed Buddy",
        category="feeding",
        priority=5,
        duration_minutes=15,
        preferred_start=time(12, 0),
        pets=[pet1],
    )
)
owner.add_task(
    Task(
        task_id="task_3",
        title="Clean Whiskers' litter box",
        category="cleaning",
        priority=3,
        duration_minutes=10,
        pets=[pet2],
    )
)
owner.add_task(
    Task(
        task_id="task_4",
        title="Feed Whiskers",
        category="feeding",
        priority=5,
        duration_minutes=15,
        preferred_start=time(13, 0),
        pets=[pet2],
    )
)

# Display the tasks for each pet
for pet in owner.pets:
    print(f"\nTasks for {pet.name}:")
    for task in owner.tasks_for_pet(pet.pet_id):
        print(f"  {task.describe()}")

# Create tasks for the owner
owner.add_task(
    Task(
        task_id="task_5",
        title="Schedule vet appointment for Buddy",
        category="errand",
        priority=4,
        duration_minutes=10,
        preferred_start=time(10, 0),
    )
)
owner.add_task(
    Task(
        task_id="task_6",
        title="Buy pet food",
        category="errand",
        priority=2,
        duration_minutes=55,
    )
)

# Display the tasks for the owner
print("\nTasks for Owner:")
for task in owner.personal_tasks():
    print(f"  {task.describe()}")

# Call the build method in pawpal_system.py to build the PawPal system
print("\nBuilding the PawPal System...")
plan_a = owner.request_schedule("priority")
print(plan_a.explain())

# Ask for a second plan, built with a different strategy, to compare against
print("\nBuilding an alternative plan...")
plan_b = owner.request_alternative("shortest")
print(plan_b.explain())

# Show the two candidates side by side
print("\nComparing the plans:")
print(owner.compare_candidates())

# Save whichever plan fit more tasks, keeping Plan A if they tie
if plan_b.summary()["tasks_placed"] > plan_a.summary()["tasks_placed"]:
    chosen_id = plan_b.schedule_id
else:
    chosen_id = plan_a.schedule_id

chosen = owner.choose_schedule(chosen_id)
print(f"\nSaved plan: {chosen.label} (is_saved={chosen.is_saved})")
