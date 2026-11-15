
from models.agent import ask_smartplan
from models.memory import get_memories, get_recent_conversations

print("=" * 50)
print("SMARTPLAN AI - AGENT MEMORY INTEGRATION TEST")
print("=" * 50)

# TEST 1: Ask the agent to remember a preference
print("\nTEST 1: Saving a user preference")

response1 = ask_smartplan(
    "Remember that I prefer studying in the morning."
)

print("Agent:", response1)

# TEST 2: Check saved memories
print("\nTEST 2: Checking stored memories")

for memory in get_memories():
    print(memory)

# TEST 3: Ask about the saved preference
print("\nTEST 3: Retrieving previous information")

response2 = ask_smartplan(
    "When do I prefer to study?"
)

print("Agent:", response2)

# TEST 4: Check conversation history
print("\nTEST 4: Checking conversation history")

for conversation in get_recent_conversations(limit=5):
    print(conversation)

print("\n" + "=" * 50)
print("AGENT MEMORY INTEGRATION TEST COMPLETED")
print("=" * 50)
