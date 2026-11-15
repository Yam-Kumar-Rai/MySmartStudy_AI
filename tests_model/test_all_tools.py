
from models.agent import execute_tool

print("=" * 50)
print("SMARTPLAN AI - INDIVIDUAL TOOL TEST")
print("=" * 50)

# TEST 1: Add task
print("\nTEST 1: Add Task")

result = execute_tool(
    "add_task",
    {
        "title": "Complete AI Agent Assignment",
        "deadline": "2026-11-15",
        "duration": 120,
        "importance": 5,
        "urgency": 5
    }
)

print(result)

# TEST 2: List tasks
print("\nTEST 2: List Tasks")

result = execute_tool("list_tasks", {})

print(result)

# TEST 3: Prioritize tasks
print("\nTEST 3: Prioritize Tasks")

result = execute_tool("prioritize_tasks", {})

print(result)

# TEST 4: Create daily plan
print("\nTEST 4: Create Daily Plan")

result = execute_tool(
    "create_daily_plan",
    {
        "start_time": "09:00",
        "available_minutes": 300
    }
)

print(result)

# TEST 5: Complete task
print("\nTEST 5: Complete Task")

task_id = result[0]["task_id"] if False else None

tasks = execute_tool("list_tasks", {})

if tasks:
    result = execute_tool(
        "complete_task",
        {"task_id": tasks[0]["id"]}
    )
    print(result)
else:
    print("No pending tasks available.")

print("\n" + "=" * 50)
print("INDIVIDUAL TOOL TEST COMPLETED")
print("=" * 50)
