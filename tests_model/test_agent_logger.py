
from models.agent_logger import log_agent_event, get_agent_logs

# Test saving an agent activity
log_agent_event(
    event_type="tool_selected",
    user_message="Show my pending tasks",
    tool_name="list_tasks",
    arguments={},
    status="selected"
)

# Retrieve recent activities
logs = get_agent_logs(limit=10)

for log in logs:
    print(log)
