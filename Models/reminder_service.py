
import time
import platform
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root and Models folder to Python import path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = Path(__file__).resolve().parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if str(MODELS_DIR) not in sys.path:
    sys.path.insert(0, str(MODELS_DIR))
from plyer import notification

from notification_manager import (
    get_due_notifications,
    mark_notification_sent,
    schedule_notification,
    begin_alarm,
    end_alarm,
    alarm_stop_requested
)

from task_manager import get_tasks


def play_alarm():
    """Ring up to 10 times, unless the user stops the alarm."""

    if platform.system() == "Windows":
        import winsound

        try:
            for ring in range(10):

                if alarm_stop_requested():
                    print("Alarm stopped by user.")
                    break

                winsound.Beep(1000, 500)

                if alarm_stop_requested():
                    print("Alarm stopped by user.")
                    break

                if ring < 9:
                    time.sleep(0.3)

        except RuntimeError:
            print("\a")

    else:
        for ring in range(10):

            if alarm_stop_requested():
                break

            print("\a", end="", flush=True)
            time.sleep(0.7)


def show_desktop_notification(title, message):
    """Display a desktop notification."""

    try:
        notification.notify(
            title=title,
            message=message,
            app_name="SmartPlan AI",
            timeout=10
        )

        print(f"Notification sent: {title}")

    except Exception as error:
        print("Could not display desktop notification:", error)


def sync_task_deadline_reminders():
    """Create reminders one day before and on task deadlines."""

    try:
        tasks = get_tasks()
        now = datetime.now()

        for task in tasks:

            if task.get("status") != "Pending":
                continue

            deadline = task.get("deadline")

            if not deadline:
                continue

            try:
                due_date = datetime.strptime(
                    str(deadline)[:10],
                    "%Y-%m-%d"
                ).date()

            except ValueError:
                continue

            reminder_times = [
                (
                    due_date - timedelta(days=1),
                    "Tomorrow is the deadline"
                ),
                (
                    due_date,
                    "Task deadline is today"
                )
            ]

            for reminder_date, reminder_label in reminder_times:

                reminder_time = datetime.combine(
                    reminder_date,
                    datetime.min.time()
                ).replace(hour=9)

                if reminder_time <= now:
                    continue

                task_id = task.get("id")

                schedule_notification(
                    title=reminder_label,
                    message=(
                        f"{task.get('title', 'Your task')} "
                        f"is due on {due_date}."
                    ),
                    scheduled_at=reminder_time,
                    notification_type="task",
                    dedupe_key=(
                        f"task-{task_id}-{due_date}-{reminder_date}"
                    )
                )

    except Exception as error:
        print("Task reminder error:", error)


def check_notifications():
    """Process due notifications one at a time."""

    due_notifications = get_due_notifications()

    for item in due_notifications:

        notification_id = item["id"]

        # Display desktop notification.
        show_desktop_notification(
            item["title"],
            item["message"]
        )

        # Make the alarm visible to the Streamlit application.
        begin_alarm(notification_id)

        try:
            print(f"Alarm ringing: {item['title']}")

            # Up to 10 rings; can be stopped from the app.
            play_alarm()

        finally:
            # Always clear active alarm status.
            end_alarm()

        # Mark sent even if the user manually stopped the sound.
        mark_notification_sent(notification_id)

        print(f"Notification processed: {notification_id}")


def main():
    print("=" * 50)
    print("SMARTPLAN AI - BACKGROUND REMINDER SERVICE")
    print("=" * 50)

    print("Reminder service is running.")
    print("Alarms ring up to 10 times.")
    print("Use Stop Alarm in SmartPlan AI to silence them.")
    print("Press CTRL + C to stop the service.")

    last_task_sync = None

    while True:

        try:
            current_time = datetime.now()

            if (
                last_task_sync is None
                or (current_time - last_task_sync).total_seconds() >= 300
            ):
                sync_task_deadline_reminders()
                last_task_sync = current_time

            check_notifications()

        except Exception as error:
            print("Reminder service error:", error)

        # Check for due reminders every second.
        time.sleep(1)


if __name__ == "__main__":
    main()
