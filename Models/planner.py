
from datetime import datetime, timedelta

from task_manager import get_tasks
from decision_engine import rank_tasks


def generate_daily_plan(
    start_time,
    available_minutes=None,
    end_time=None
):
    """
    Generate a daily schedule from pending tasks.

    Supported calls:
        generate_daily_plan("06:00", 780)
        generate_daily_plan("06:00", end_time="19:00")
    """

    try:
        current_time = datetime.strptime(start_time, "%H:%M")
    except (ValueError, TypeError):
        raise ValueError("Start time must use HH:MM format.")

    # Calculate available minutes using the ending time
    if end_time is not None:

        try:
            finish_time = datetime.strptime(end_time, "%H:%M")
        except (ValueError, TypeError):
            raise ValueError("End time must use HH:MM format.")

        available_minutes = int(
            (finish_time - current_time).total_seconds() / 60
        )

    if (
        not isinstance(available_minutes, int)
        or isinstance(available_minutes, bool)
        or available_minutes <= 0
    ):
        raise ValueError("Available minutes must be a positive integer.")

    # Retrieve tasks and rank them by priority
    tasks = rank_tasks(get_tasks())

    remaining_minutes = available_minutes
    daily_plan = []

    for task in tasks:

        duration = task.get("duration")

        # Ignore tasks without valid durations
        if (
            not isinstance(duration, int)
            or isinstance(duration, bool)
            or duration <= 0
        ):
            continue

        # Skip tasks that cannot fit into the remaining time
        if duration > remaining_minutes:
            continue

        task_end_time = current_time + timedelta(
            minutes=duration
        )

        daily_plan.append({
            "task": task["title"],
            "start": current_time.strftime("%I:%M %p"),
            "end": task_end_time.strftime("%I:%M %p"),
            "duration": duration,
            "priority_score": task["priority_score"]
        })

        current_time = task_end_time
        remaining_minutes -= duration

    return daily_plan
