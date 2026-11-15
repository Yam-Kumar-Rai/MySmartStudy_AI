
from models.task_manager import get_tasks
from models.decision_engine import rank_tasks

# Get tasks from the database
tasks = get_tasks()

# Calculate and rank task priorities
ranked_tasks = rank_tasks(tasks)

# Display results
print("\nSMARTPLAN AI - TASK PRIORITY RANKING")
print("=" * 45)

for position, task in enumerate(ranked_tasks, start=1):

    print(f"\nPriority Rank: {position}")
    print(f"Task: {task['title']}")
    print(f"Importance: {task['importance']}")
    print(f"Urgency: {task['urgency']}")
    print(f"Deadline: {task['deadline']}")
    print(f"Priority Score: {task['priority_score']}/5")
