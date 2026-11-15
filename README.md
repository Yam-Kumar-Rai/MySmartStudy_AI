# SmartPlan AI – Intelligent Study Planning Agent

**SmartPlan AI** is an AI-powered study planning assistant designed to help students organize academic tasks, prioritize their workload, manage study sessions, and improve their productivity.

The project combines a local Large Language Model (LLM), an intelligent agent architecture, task-management tools, memory, feedback, and evaluation mechanisms to provide personalized study assistance.

## Key Features

- **AI Study Assistant:** Interacts with students using a locally running Qwen 2.5 model through Ollama.
- **Task Management:** Create, view, complete, and delete study tasks.
- **Intelligent Prioritization:** Ranks tasks to help students decide what to work on first.
- **Daily Planning:** Generates structured daily study plans.
- **Study Sessions:** Supports focused study and break sessions.
- **Study Notes:** Provides functionality for managing study notes.
- **Memory:** Stores relevant information and conversation history.
- **Feedback and Adaptation:** Uses student feedback to adjust future response guidance.
- **Agent Logging:** Records agent activities and tool execution events.
- **Agent Evaluation:** Includes test cases and evaluation utilities for assessing agent behaviour.
- **Notifications:** Supports study reminders and desktop notifications.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core development |
| Streamlit | User interface |
| Ollama | Local LLM integration |
| Qwen 2.5 (1.5B) | Language model |
| SQLite | Persistent data storage |
| Pandas | Data handling |
| Plyer | Desktop notifications |

## Project Architecture

SmartPlan AI follows an agent-based architecture:

1. **User Interface:** Receives student requests through Streamlit.
2. **Intelligent Agent:** Interprets requests and coordinates actions.
3. **LLM Integration:** Uses the local Qwen model for language understanding and response generation.
4. **Decision Engine:** Supports task prioritization and planning.
5. **Tool Execution:** Performs operations such as task creation, completion, and daily planning.
6. **Memory:** Stores relevant information and conversation history.
7. **Feedback and Evaluation:** Records feedback and evaluates agent behaviour.
8. **Database:** Stores tasks, notes, memory, and other application data.

## Project Structure

```text
MySmartStudy_AI/
│
├── agent/
├── database/
│   └── db.py
│
├── evaluation/
├── interface/
│
├── Models/
│   ├── agent.py
│   ├── agent_evaluator.py
│   ├── agent_logger.py
│   ├── agent_test_cases.py
│   ├── app.py
│   ├── daily_schedule_manager.py
│   ├── decision_engine.py
│   ├── feedback_analyzer.py
│   ├── feedback_manager.py
│   ├── memory.py
│   ├── notification_manager.py
│   ├── planner.py
│   ├── reminder_service.py
│   ├── study_manager.py
│   ├── study_notes_manager.py
│   ├── study_notes_ui.py
│   └── task_manager.py
│
├── tests_model/
│
├── .gitignore
├── requirements.txt
└── README.md
```

## Installation and Setup

### 1. Clone the Repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd MySmartStudy_AI
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it on Windows:

```powershell
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Ollama

Download and install Ollama from:

https://ollama.com/

Pull the Qwen 2.5 1.5B model:

```bash
ollama pull qwen2.5:1.5b
```

Make sure Ollama is running locally before starting the application.

### 5. Run the Application

```bash
streamlit run Models/app.py
```

The Streamlit application should open in your browser.

## Testing and Evaluation

The project includes Python test modules covering areas such as:

- Agent tools and operations
- Agent memory
- Decision-making and prioritization
- Planning
- Task management
- Study features
- Agent logging
- Ollama integration

The project also includes an agent evaluator and controlled test cases for examining agent behaviour.

Run the test suite with:

```bash
python -m unittest discover -s tests_model -v
```

## Limitations

- The local language model has limited capabilities compared with larger hosted models.
- The quality of generated plans depends on the information provided by the student.
- Feedback-based adaptation adjusts response guidance rather than retraining the language model.
- Desktop notifications depend on operating-system support and permissions.
- Agent performance should be interpreted using the project's evaluation results rather than assumed to be perfect.

## Future Improvements

- More advanced adaptive planning.
- Improved long-term memory management.
- Enhanced agent evaluation and benchmarking.
- More personalized recommendations.
- Improved scheduling and notification capabilities.
- Better support for additional local language models.

## Academic Project

Developed as part of the **DAT404 – Intelligent and Generative Agents** coursework.

**Project:** SmartPlan AI – Intelligent Study Planning Agent

---

*SmartPlan AI aims to make academic planning more organized, intelligent, and manageable through agent-based artificial intelligence.*
