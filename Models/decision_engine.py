
from datetime import date, datetime


def calculate_priority(task):

    # 1. Get importance and urgency
    importance = int(task.get("importance", 1))
    urgency = int(task.get("urgency", 1))

    # Keep scores within the 1–5 range
    importance = max(1, min(5, importance))
    urgency = max(1, min(5, urgency))

    # 2. Calculate deadline proximity
    deadline = task.get("deadline")

    if deadline:
        try:
            deadline_date = datetime.strptime(
                deadline, "%Y-%m-%d"
            ).date()

            days_left = (deadline_date - date.today()).days

            if days_left <= 0:
                deadline_score = 5
            elif days_left <= 2:
                deadline_score = 4
            elif days_left <= 5:
                deadline_score = 3
            elif days_left <= 7:
                deadline_score = 2
            else:
                deadline_score = 1

        except (ValueError, TypeError):
            deadline_score = 1
    else:
        deadline_score = 1

    # 3. Weighted decision matrix
    # Importance: 45%
    # Urgency: 45%
    # Deadline: 10%

    priority_score = (
        importance * 0.45
        + urgency * 0.45
        + deadline_score * 0.10
    )

    return round(priority_score, 2)


def rank_tasks(tasks):

    # Only rank pending tasks
    pending_tasks = [
        task for task in tasks
        if task.get("status") == "Pending"
    ]

    # Calculate priority scores
    for task in pending_tasks:
        task["priority_score"] = calculate_priority(task)

    # Sort by score, then urgency, then importance
    ranked_tasks = sorted(
        pending_tasks,
        key=lambda task: (
            task["priority_score"],
            task.get("urgency", 1),
            task.get("importance", 1)
        ),
        reverse=True
    )

    return ranked_tasks
