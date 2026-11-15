
from models.memory import (
    save_memory,
    get_memories,
    search_memories,
    save_conversation,
    get_recent_conversations
)

print("=" * 45)
print("SMARTPLAN AI - MEMORY MODULE TEST")
print("=" * 45)


# Test 1: Save memory
print("\nTEST 1: Saving memory")

save_memory(
    "test_preference",
    "This is a test memory.",
    "test"
)

print("Memory saved successfully!")


# Test 2: Retrieve memory
print("\nTEST 2: Retrieving memories")

memories = get_memories()

for memory in memories:
    print(memory)


# Test 3: Search memory
print("\nTEST 3: Searching memory")

results = search_memories("test memory")

for result in results:
    print(result)


# Test 4: Save conversation
print("\nTEST 4: Saving conversation")

save_conversation(
    "How should I organize my tasks?",
    "Start by prioritizing your most important tasks."
)

print("Conversation saved successfully!")


# Test 5: Retrieve recent conversations
print("\nTEST 5: Recent conversations")

conversations = get_recent_conversations(5)

for conversation in conversations:
    print(conversation)


print("\n" + "=" * 45)
print("MEMORY MODULE TEST COMPLETED")
print("=" * 45)
