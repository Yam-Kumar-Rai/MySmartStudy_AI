
from models.agent import ask_smartplan

print("SMARTPLAN AI AGENT TEST")
print("=" * 40)

response = ask_smartplan(
    "Show me my pending tasks and recommend which one I should complete first."
)

print("\nAgent Response:")
print(response)
