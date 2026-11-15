
from models.planner import generate_daily_plan

plan = generate_daily_plan(
    start_time="09:00",
    available_minutes=240
)

print("\nSMARTPLAN AI - DAILY STUDY PLAN")
print("=" * 45)

if not plan:
    print("No tasks could fit into the available time.")

for item in plan:

    print(f"\nTask: {item['task']}")
    print(f"Time: {item['start']} - {item['end']}")
    print(f"Duration: {item['duration']} minutes")
    print(f"Priority: {item['priority_score']}/5")
