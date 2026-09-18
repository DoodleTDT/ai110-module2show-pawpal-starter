# Import classes from pawpal_system.py
from pawpal_system import Pet
from pawpal_system import Task
from pawpal_system import Schedule
from pawpal_system import User

# Create an instance of a user (pet owner)
owner = User("John Doe", "123-456-7890", "john.doe@example.com")

# Create instances of at least two pets
pet1 = owner.add_pet("Buddy", "Dog", 3, "Golden Retriever")
pet2 = owner.add_pet("Whiskers", "Cat", 2, "Siamese")

# Display the owner's information and their pets
print("Owner Information:")
print(f"Name: {owner.name}")
print(f"Phone: {owner.phone}")
print(f"Email: {owner.email}")

print("\nPets Information:")
for pet in owner.pets:
    print(f"Name: {pet.name}, Species: {pet.species}, Age: {pet.age}, Breed: {pet.breed}")

# Create two tasks per pet
task1_pet1 = pet1.add_task("Take Buddy for a walk", "2024-06-15 08:00")
task2_pet1 = pet1.add_task("Feed Buddy", "2024-06-15 12:00")
task1_pet2 = pet2.add_task("Clean Whiskers' litter box", "2024-06-15 09:00")
task2_pet2 = pet2.add_task("Feed Whiskers", "2024-06-15 13:00")

# Display the tasks for each pet
print("\nTasks for Buddy:")
for task in pet1.tasks:
    print(f"Task: {task.description}, Due: {task.due_date}")

print("\nTasks for Whiskers:")
for task in pet2.tasks:
    print(f"Task: {task.description}, Due: {task.due_date}")

# Create tasks for the owner
task1_owner = owner.add_task("Schedule vet appointment for Buddy", "2024-06-16 10:00")
task2_owner = owner.add_task("Buy pet food", "2024-06-15 14:00")

# Display the tasks for the owner
print("\nTasks for Owner:")
for task in owner.tasks:
    print(f"Task: {task.description}, Due: {task.due_date}")

# Call build method in scheduler.py to build the PawPal system
print("\nBuilding the PawPal System...")
owner.build_schedule()


