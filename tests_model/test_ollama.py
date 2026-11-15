
from models.agent import ask_smartplan

message = "I have three tasks: Python assignment, ML revision, and SQL practice. Help me organise my day."

response = ask_smartplan(message)

print("\nSmartPlan AI:")
print(response)
