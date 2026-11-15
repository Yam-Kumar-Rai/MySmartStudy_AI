
from models.task_manager import add_task, get_tasks, complete_task

# Add sample tasks
task_id = add_task(
    title="Complete Python Assignment",
    deadline="2026-11-14",
    duration=120,
    importance=5,
    urgency=5
)

add_task(
    title="Revise Machine Learning",
    deadline="2026-11-15",
    duration=90,
    importance=4,
    urgency=3
)

# Display tasks
print("\nMY TASKS")

for task in get_tasks():
    print(task)

# Complete the first task
complete_task(task_id)

print("\nTASKS AFTER COMPLETION")

for task in get_tasks():
    print(task)
