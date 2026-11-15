import streamlit as st
import pandas as pd
import time
import math
import html
import uuid
import sys
from pathlib import Path
from datetime import datetime, date, time as dt_time, timedelta

# ==========================================================
# 0. PROJECT PATH CONFIGURATION
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = Path(__file__).resolve().parent

for directory in [PROJECT_ROOT, MODELS_DIR]:
    directory_string = str(directory)

    if directory_string not in sys.path:
        sys.path.insert(0, directory_string)


# ==========================================================
# 1. CORE IMPORTS
# ==========================================================

from study_notes_ui import render_study_notes_page

from task_manager import (
    add_task,
    get_tasks,
    complete_task,
    delete_task
)

from decision_engine import rank_tasks
from planner import generate_daily_plan
from agent import ask_smartplan

from memory import (
    get_memories,
    get_recent_conversations
)

from feedback_manager import (
    create_feedback_table,
    save_feedback,
    get_recent_feedback,
    get_feedback_statistics
)


# ==========================================================
# 2. OPTIONAL MODULES
# ==========================================================

try:
    from study_manager import (
        save_study_session,
        get_study_sessions,
        get_study_statistics
    )
    STUDY_MANAGER_AVAILABLE = True

except ImportError as error:
    STUDY_MANAGER_AVAILABLE = False
    print("Study Manager unavailable:", error)


try:
    from notification_manager import (
        schedule_notification,
        get_notifications,
        cancel_notification
    )
    NOTIFICATION_MANAGER_AVAILABLE = True

except ImportError as error:
    NOTIFICATION_MANAGER_AVAILABLE = False
    print("Notification Manager unavailable:", error)


try:
    from notification_manager import (
        get_alarm_status,
        request_stop_alarm
    )
    ALARM_CONTROL_AVAILABLE = True

except ImportError as error:
    ALARM_CONTROL_AVAILABLE = False
    print("Alarm controls unavailable:", error)

    def get_alarm_status():
        return {"is_active": False}

    def request_stop_alarm():
        return False


try:
    from daily_schedule_manager import (
        add_activity,
        get_activities,
        get_activity,
        update_activity,
        complete_activity,
        delete_activity
    )

    DAILY_SCHEDULE_AVAILABLE = True
    DAILY_SCHEDULE_ERROR = None

except Exception as error:
    DAILY_SCHEDULE_AVAILABLE = False
    DAILY_SCHEDULE_ERROR = str(error)
    print("Daily Schedule Manager unavailable:", error)


# ==========================================================
# 3. PAGE CONFIGURATION
# ==========================================================

st.set_page_config(
    page_title="SmartPlan AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==========================================================
# 4. FOCUS STUDIO DARK THEME
# ==========================================================

st.markdown("""
<style>

:root {
    --bg: #0B1020;
    --surface: #141D31;
    --surface2: #1B2740;
    --blue: #7893FF;
    --purple: #A78BFA;
    --cyan: #38BDF8;
    --text: #F1F5F9;
    --muted: #94A3B8;
    --border: #293650;
}

.stApp {
    background-color: var(--bg);
    color: var(--text);
    font-family: 'Segoe UI', sans-serif;
}

[data-testid="stMain"] {
    background-color: var(--bg);
}

h1, h2, h3, h4, h5 {
    color: var(--text) !important;
    font-weight: 700 !important;
}

p, li {
    color: #CBD5E1;
}

[data-testid="stSidebar"] {
    background-color: #10182A;
    border-right: 1px solid var(--border);
}

[data-testid="stSidebar"] * {
    color: var(--text);
}

[data-testid="stMetric"] {
    background-color: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 16px;
}

[data-testid="stMetricValue"] {
    color: var(--blue);
}

[data-testid="stMetricLabel"] {
    color: var(--muted);
}

.stButton button {
    background-color: #4169E1;
    color: white !important;
    border: 1px solid #5879E8;
    border-radius: 9px;
    font-weight: 600;
    padding: 0.55rem 1rem;
}

.stButton button:hover {
    background-color: #3457C5;
    border-color: var(--blue);
    color: white !important;
}

.stButton button[kind="secondary"] {
    background-color: var(--surface2);
    color: var(--text) !important;
}

.stTextInput input,
.stNumberInput input,
.stDateInput input,
.stTimeInput input,
.stTextArea textarea {
    background-color: var(--surface);
    color: var(--text);
    border: 1px solid var(--border);
    border-radius: 8px;
}

[data-baseweb="select"] {
    background-color: var(--surface);
    color: var(--text);
}

[data-testid="stExpander"],
[data-testid="stForm"] {
    background-color: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
}

button[data-baseweb="tab"] {
    color: var(--muted);
    font-weight: 600;
}

hr {
    border-color: var(--border);
}

[data-testid="stDataFrame"] {
    border: 1px solid var(--border);
    border-radius: 10px;
}

[data-testid="stAlert"] {
    border-radius: 10px;
}

[data-testid="stMarkdownContainer"] {
    color: var(--text);
}

footer {
    visibility: hidden;
}

</style>
""", unsafe_allow_html=True)


# ==========================================================
# 5. SESSION STATE
# ==========================================================

DEFAULT_STATE = {
    "chat_messages": [],
    "delete_task_id": None,
    "daily_plan": None,

    # Feedback system
    "feedback_submitted": {},
    "feedback_db_initialized": False,

    # Study timer
    "study_timer_status": "idle",
    "study_timer_end": None,
    "study_timer_remaining": 1500,
    "study_timer_alert_id": None,
    "study_timer_saved": False,
    "study_timer_subject": "General Study",
    "study_timer_duration_minutes": 25,
    "study_timer_started_minutes": 25,

    # Break timer
    "break_timer_status": "idle",
    "break_timer_end": None,
    "break_timer_remaining": 300,
    "break_timer_alert_id": None,
    "break_timer_duration_seconds": 300
}

for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value


# Initialize the feedback table once per app session.
if not st.session_state.feedback_db_initialized:

    try:
        create_feedback_table()
        st.session_state.feedback_db_initialized = True

    except Exception as error:
        st.error(
            f"Feedback database initialization failed: {error}"
        )


# ==========================================================
# 6. HELPER FUNCTIONS
# ==========================================================

def safe_text(value):
    return "" if value is None else str(value)


def format_duration(minutes):
    minutes = int(minutes)
    hours = minutes // 60
    remaining = minutes % 60

    if hours > 0:
        return f"{hours}h {remaining}m"

    return f"{remaining} min"


def format_timer_time(total_seconds):
    total_seconds = max(0, int(total_seconds))

    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    return f"{minutes:02d}:{seconds:02d}"


def display_table(data):
    if data:
        st.dataframe(
            pd.DataFrame(data),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Nothing to display yet.")


# ==========================================================
# 7. NOTIFICATION FUNCTIONS
# ==========================================================

def schedule_timer_alert(
    title,
    message,
    seconds,
    notification_type
):
    if not NOTIFICATION_MANAGER_AVAILABLE:
        return None

    unique_key = f"timer-{uuid.uuid4().hex}"

    try:
        scheduled_time = datetime.now() + timedelta(
            seconds=max(1, int(seconds))
        )

        schedule_notification(
            title=title,
            message=message,
            scheduled_at=scheduled_time,
            notification_type=notification_type,
            dedupe_key=unique_key
        )

        notifications = get_notifications(200)

        for item in notifications:
            if item.get("dedupe_key") == unique_key:
                return item.get("id")

    except Exception as error:
        print("Notification scheduling error:", error)

    return None


def cancel_timer_alert(timer_prefix):
    key = f"{timer_prefix}_timer_alert_id"
    alert_id = st.session_state.get(key)

    if alert_id and NOTIFICATION_MANAGER_AVAILABLE:
        try:
            cancel_notification(alert_id)
        except Exception as error:
            print("Could not cancel notification:", error)

    st.session_state[key] = None


# ==========================================================
# 8. TIMER CONTROL FUNCTIONS
# ==========================================================

def timer_start(
    timer_prefix,
    duration_seconds,
    title,
    message,
    notification_type
):
    cancel_timer_alert(timer_prefix)

    duration_seconds = max(1, int(duration_seconds))

    st.session_state[f"{timer_prefix}_timer_status"] = "running"
    st.session_state[f"{timer_prefix}_timer_remaining"] = duration_seconds
    st.session_state[f"{timer_prefix}_timer_end"] = (
        time.time() + duration_seconds
    )

    if timer_prefix == "study":
        st.session_state.study_timer_saved = False
        st.session_state.study_timer_started_minutes = (
            math.ceil(duration_seconds / 60)
        )

    st.session_state[f"{timer_prefix}_timer_alert_id"] = (
        schedule_timer_alert(
            title,
            message,
            duration_seconds,
            notification_type
        )
    )


def timer_pause(timer_prefix):
    end_time = st.session_state.get(
        f"{timer_prefix}_timer_end"
    )

    if end_time is not None:
        remaining = max(
            0,
            math.ceil(end_time - time.time())
        )
    else:
        remaining = st.session_state.get(
            f"{timer_prefix}_timer_remaining", 0
        )

    st.session_state[f"{timer_prefix}_timer_remaining"] = remaining
    st.session_state[f"{timer_prefix}_timer_status"] = "paused"
    st.session_state[f"{timer_prefix}_timer_end"] = None

    cancel_timer_alert(timer_prefix)


def timer_resume(
    timer_prefix,
    title,
    message,
    notification_type
):
    remaining = int(
        st.session_state.get(
            f"{timer_prefix}_timer_remaining", 0
        )
    )

    if remaining <= 0:
        st.session_state[f"{timer_prefix}_timer_status"] = "finished"
        st.session_state[f"{timer_prefix}_timer_end"] = None
        return

    st.session_state[f"{timer_prefix}_timer_status"] = "running"

    st.session_state[f"{timer_prefix}_timer_end"] = (
        time.time() + remaining
    )

    st.session_state[f"{timer_prefix}_timer_alert_id"] = (
        schedule_timer_alert(
            title,
            message,
            remaining,
            notification_type
        )
    )


def timer_reset(timer_prefix):
    cancel_timer_alert(timer_prefix)

    st.session_state[f"{timer_prefix}_timer_status"] = "idle"
    st.session_state[f"{timer_prefix}_timer_end"] = None

    if timer_prefix == "study":
        duration = (
            int(st.session_state.study_timer_duration_minutes) * 60
        )
        st.session_state.study_timer_saved = False
    else:
        duration = int(
            st.session_state.break_timer_duration_seconds
        )

    st.session_state[f"{timer_prefix}_timer_remaining"] = duration


# ==========================================================
# 9. TIMER DISPLAY
# ==========================================================

def timer_display_card(
    label,
    remaining,
    color,
    accent,
    subtitle
):
    safe_label = html.escape(safe_text(label))
    safe_subtitle = html.escape(safe_text(subtitle))
    formatted_time = format_timer_time(remaining)

    timer_html = f"""
    <div style="
        background: linear-gradient(135deg, #141D31, #1B2740);
        border: 1px solid #293650;
        border-radius: 18px;
        padding: 26px 18px;
        text-align: center;
        margin-top: 10px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.20);
        width: 100%;
        box-sizing: border-box;
    ">
        <div style="
            color: {color};
            font-size: 14px;
            font-weight: 700;
            letter-spacing: 3px;
        ">
            {safe_label}
        </div>

        <div style="
            color: #F1F5F9;
            font-size: 56px;
            font-weight: 800;
            margin: 10px 0;
            font-family: monospace;
            line-height: 1.3;
        ">
            {formatted_time}
        </div>

        <div style="
            color: #94A3B8;
            font-size: 14px;
        ">
            {safe_subtitle}
        </div>

        <div style="
            width: 76px;
            height: 4px;
            background: {accent};
            border-radius: 10px;
            margin: 18px auto 0 auto;
        ">
        </div>
    </div>
    """

    st.html(timer_html)


# ==========================================================
# 10. LIVE TIMER DASHBOARD — COUNTDOWN FIX
# ==========================================================

@st.fragment(run_every=1)
def live_timer_dashboard():

    # Get the current time on every fragment refresh.
    current_time = time.time()

    # ------------------------------------------------------
    # 1. STUDY TIMER
    # ------------------------------------------------------

    study_status = st.session_state.study_timer_status
    study_end = st.session_state.study_timer_end

    if study_status == "running":

        if study_end is None:
            study_end = (
                current_time
                + int(st.session_state.study_timer_remaining)
            )
            st.session_state.study_timer_end = study_end

        study_remaining = max(
            0,
            math.ceil(study_end - current_time)
        )

        st.session_state.study_timer_remaining = study_remaining

        if study_remaining <= 0:

            st.session_state.study_timer_remaining = 0
            st.session_state.study_timer_status = "finished"
            st.session_state.study_timer_end = None

            if (
                STUDY_MANAGER_AVAILABLE
                and not st.session_state.study_timer_saved
            ):
                try:
                    save_study_session(
                        st.session_state.study_timer_subject,
                        st.session_state.study_timer_started_minutes
                    )

                    st.session_state.study_timer_saved = True

                except Exception as error:
                    st.error(f"Could not save study session: {error}")

    # ------------------------------------------------------
    # 2. BREAK TIMER
    # ------------------------------------------------------

    break_status = st.session_state.break_timer_status
    break_end = st.session_state.break_timer_end

    if break_status == "running":

        if break_end is None:
            break_end = (
                current_time
                + int(st.session_state.break_timer_remaining)
            )
            st.session_state.break_timer_end = break_end

        break_remaining = max(
            0,
            math.ceil(break_end - current_time)
        )

        st.session_state.break_timer_remaining = break_remaining

        if break_remaining <= 0:

            st.session_state.break_timer_remaining = 0
            st.session_state.break_timer_status = "finished"
            st.session_state.break_timer_end = None

    # ------------------------------------------------------
    # 3. GET DISPLAY VALUES
    # ------------------------------------------------------

    study_status = st.session_state.study_timer_status
    break_status = st.session_state.break_timer_status

    study_remaining = int(
        st.session_state.study_timer_remaining
    )

    break_remaining = int(
        st.session_state.break_timer_remaining
    )

    if study_status == "idle":

        study_remaining = (
            int(st.session_state.study_timer_duration_minutes) * 60
        )

        st.session_state.study_timer_remaining = study_remaining

    if break_status == "idle":

        break_remaining = int(
            st.session_state.break_timer_duration_seconds
        )

        st.session_state.break_timer_remaining = break_remaining

    # ------------------------------------------------------
    # 4. DISPLAY TIMER CARDS
    # ------------------------------------------------------

    study_col, break_col = st.columns(2)

    with study_col:

        timer_display_card(
            "STUDY TIME",
            study_remaining,
            "#F1F5F9",
            "#A78BFA",
            st.session_state.study_timer_subject
        )

        if study_status == "running":
            st.caption("📚 Study session in progress.")

        elif study_status == "paused":
            st.caption("⏸ Study timer paused.")

        elif study_status == "finished":
            st.success("🎉 Study session completed!")

        else:
            st.caption("Set your duration and press Start Study.")

    with break_col:

        timer_display_card(
            "BREAK TIME",
            break_remaining,
            "#F1F5F9",
            "#7893FF",
            "Take a moment to relax"
        )

        if break_status == "running":
            st.caption("☕ Break in progress.")

        elif break_status == "paused":
            st.caption("⏸ Break timer paused.")

        elif break_status == "finished":
            st.success("☕ Break completed!")

        else:
            st.caption("Choose a duration and press Start Break.")

    # ------------------------------------------------------
    # 5. LIVE REFRESH DEBUG INFORMATION
    # ------------------------------------------------------

    st.caption(
        f"🟢 Live timer refresh: "
        f"{datetime.now().strftime('%H:%M:%S')}"
    )

    with st.expander("Timer diagnostics"):

        st.write({
            "Current time": datetime.now().strftime("%H:%M:%S"),
            "Study status": study_status,
            "Study remaining seconds": study_remaining,
            "Study end timestamp": st.session_state.study_timer_end,
            "Break status": break_status,
            "Break remaining seconds": break_remaining,
            "Break end timestamp": st.session_state.break_timer_end
        })


# =========================================================
# 11. ALARM STOP CONTROLS
# =========================================================

@st.fragment(run_every="1s")
def alarm_sidebar_control():

    if not NOTIFICATION_MANAGER_AVAILABLE:
        return

    if not ALARM_CONTROL_AVAILABLE:
        st.caption(
            "Update notification_manager.py to enable alarm controls."
        )
        return

    try:
        alarm = get_alarm_status()

        if alarm and alarm.get("is_active"):

            st.warning("🔔 An alarm is currently ringing!")

            if st.button(
                "🔇 STOP ALARM",
                type="primary",
                use_container_width=True,
                key="stop_active_alarm"
            ):
                request_stop_alarm()
                st.success("Stop request sent.")
                st.rerun(scope="fragment")

    except Exception as error:
        st.caption(f"Alarm status unavailable: {error}")


@st.fragment(run_every="1s")
def alarm_timer_page_control():

    if not NOTIFICATION_MANAGER_AVAILABLE:
        return

    if not ALARM_CONTROL_AVAILABLE:
        return

    try:
        alarm = get_alarm_status()

        if alarm and alarm.get("is_active"):

            st.warning(
                "🔔 Your reminder alarm is ringing! "
                "Press the button below to stop it."
            )

            if st.button(
                "🔇 OFF — STOP RINGING",
                type="primary",
                use_container_width=True,
                key="stop_active_alarm_timer_page"
            ):
                request_stop_alarm()
                st.success("Alarm stop request sent.")
                st.rerun(scope="fragment")

    except Exception as error:
        st.caption(
            f"Could not check alarm status: {error}"
        )


# ==========================================================
# 12. SIDEBAR
# ==========================================================

with st.sidebar:

    st.markdown("# 🧠 SmartStudy AI")

    st.caption(
        "Your personal intelligent planning assistant"
    )

    st.divider()

    selected_page = st.radio(
        "NAVIGATION",
        [
            "🏠 Overview",
            "📝 My Tasks",
            "🤖 AI Assistant",
            "🎯 Priorities",
            "📅 Daily Planner",
            "⏱️ Study Timer",
            "🧠 My Memory",
            "🔔 Notifications",
            "📚 Study Notes"
        ],
        label_visibility="visible"
    )

    st.divider()

    st.markdown("### Your productivity assistant")

    st.caption(
        "Plan smarter. Focus better. Achieve more."
    )

    if NOTIFICATION_MANAGER_AVAILABLE:

        st.success("Notification system connected")

        st.caption(
            "Keep reminder_service.py running in another terminal."
        )

        alarm_sidebar_control()

    else:
        st.warning("Notification manager not found")

    st.divider()

    st.caption(
        "SmartPlan AI | Your personal productivity assistant"
    )


# ==========================================================
# 13. OVERVIEW
# ==========================================================

if selected_page == "🏠 Overview":

    st.title("Good day! 👋")

    st.write(
        "Welcome to your personal productivity dashboard."
    )

    tasks = get_tasks()

    pending = [
        task for task in tasks
        if task.get("status") == "Pending"
    ]

    completed = [
        task for task in tasks
        if task.get("status") == "Completed"
    ]

    total = len(tasks)

    completion_rate = (
        len(completed) / total * 100
        if total > 0 else 0
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Tasks", total)
    col2.metric("Pending", len(pending))
    col3.metric("Completed", len(completed))
    col4.metric("Completion Rate", f"{completion_rate:.1f}%")

    st.divider()

    left, right = st.columns(2)

    with left:

        st.markdown(
            '<h3 style="color:#B8C5D9;">📌 Pending Tasks</h3>',
            unsafe_allow_html=True
        )

        if pending:

            for task in pending[:5]:

                title = html.escape(
                    safe_text(task.get("title", "Untitled"))
                )

                st.markdown(
                    f'<p style="color:#C5D0E0;'
                    f'font-size:16px;font-weight:600;">'
                    f'{title}</p>',
                    unsafe_allow_html=True
                )

                st.caption(
                    f"Deadline: {task.get('deadline', 'Not set')}"
                )

                st.divider()

        else:
            st.success("You have no pending tasks!")

    with right:

        st.markdown(
            '<h3 style="color:#B8C5D9;">🏆 Recent Completed Tasks</h3>',
            unsafe_allow_html=True
        )

        if completed:

            for task in completed[-5:][::-1]:

                title = html.escape(
                    safe_text(task.get("title", "Untitled"))
                )

                st.markdown(
                    f'<p style="color:#C5D0E0;'
                    f'font-size:16px;font-weight:600;">'
                    f'{title}</p>',
                    unsafe_allow_html=True
                )

                st.caption("Completed")
                st.divider()

        else:
            st.info("No completed tasks yet.")

    if STUDY_MANAGER_AVAILABLE:

        st.divider()
        st.subheader("📚 Study Statistics")

        try:
            stats = get_study_statistics()

            a, b, c = st.columns(3)

            a.metric(
                "Study Sessions",
                stats["completed_sessions"]
            )

            b.metric(
                "Total Study Time",
                format_duration(stats["total_minutes"])
            )

            c.metric(
                "Today's Study Time",
                format_duration(stats["today_minutes"])
            )

        except Exception as error:
            st.warning(
                f"Could not load study statistics: {error}"
            )


# ==========================================================
# 14. MY TASKS
# ==========================================================

elif selected_page == "📝 My Tasks":

    st.title("📝 My Tasks")

    st.caption(
        "Create, manage, complete and delete your tasks."
    )

    with st.expander("➕ Add a New Task", expanded=True):

        with st.form("add_task_form"):

            task_title = st.text_input(
                "Task title",
                placeholder="Example: Complete Python assignment"
            )

            task_deadline = st.date_input(
                "Deadline",
                value=date.today() + timedelta(days=1),
                min_value=date.today()
            )

            task_duration = st.number_input(
                "Estimated duration (minutes)",
                min_value=1,
                max_value=1440,
                value=60
            )

            col1, col2 = st.columns(2)

            with col1:
                importance = st.slider(
                    "Importance", 1, 5, 3
                )

            with col2:
                urgency = st.slider(
                    "Urgency", 1, 5, 3
                )

            submitted = st.form_submit_button(
                "Add Task",
                use_container_width=True
            )

            if submitted:

                if not task_title.strip():
                    st.error("Please enter a task title.")

                else:

                    try:
                        result = add_task(
                            task_title.strip(),
                            task_deadline.strftime("%Y-%m-%d"),
                            int(task_duration),
                            int(importance),
                            int(urgency)
                        )

                        if result:
                            st.success("Task added successfully!")
                            st.rerun()
                        else:
                            st.error("Task could not be added.")

                    except Exception as error:
                        st.error(f"Error adding task: {error}")

    st.divider()

    tasks = get_tasks()

    pending = [
        task for task in tasks
        if task.get("status") == "Pending"
    ]

    completed = [
        task for task in tasks
        if task.get("status") == "Completed"
    ]

    tab1, tab2 = st.tabs([
        f"Pending ({len(pending)})",
        f"Completed ({len(completed)})"
    ])

    with tab1:

        if not pending:
            st.info("No pending tasks.")

        for task in pending:

            with st.container(border=True):

                col1, col2, col3 = st.columns([5, 1, 1])

                with col1:

                    st.markdown(f"### {task['title']}")

                    st.caption(
                        f"Deadline: {task.get('deadline', 'Not set')} "
                        f"| Duration: {task.get('duration', 0)} minutes"
                    )

                    st.caption(
                        f"Importance: {task.get('importance', '-')} / 5 "
                        f"| Urgency: {task.get('urgency', '-')} / 5"
                    )

                with col2:

                    if st.button(
                        "✓",
                        key=f"complete_{task['id']}",
                        help="Mark as completed"
                    ):

                        try:
                            complete_task(task["id"])
                            st.success("Task completed!")
                            st.rerun()

                        except Exception as error:
                            st.error(str(error))

                with col3:

                    if st.button(
                        "🗑️",
                        key=f"delete_{task['id']}",
                        help="Delete task"
                    ):
                        st.session_state.delete_task_id = task["id"]
                        st.rerun()

    with tab2:

        if not completed:
            st.info("No completed tasks yet.")

        for task in completed:

            with st.container(border=True):

                col1, col2 = st.columns([5, 1])

                with col1:
                    st.markdown(f"~~{task['title']}~~")
                    st.caption("Completed")

                with col2:

                    if st.button(
                        "🗑️",
                        key=f"delete_completed_{task['id']}",
                        help="Delete task"
                    ):
                        st.session_state.delete_task_id = task["id"]
                        st.rerun()

    delete_id = st.session_state.delete_task_id

    if delete_id is not None:

        st.divider()

        st.warning(
            "Are you sure you want to permanently delete this task?"
        )

        yes, no = st.columns(2)

        with yes:

            if st.button(
                "Yes, delete task",
                type="primary",
                use_container_width=True
            ):

                try:
                    delete_task(delete_id)
                    st.session_state.delete_task_id = None
                    st.success("Task deleted.")
                    st.rerun()

                except Exception as error:
                    st.error(f"Could not delete task: {error}")

        with no:

            if st.button(
                "Cancel",
                use_container_width=True
            ):
                st.session_state.delete_task_id = None
                st.rerun()


# ==========================================================
# 15. AI ASSISTANT WITH USER FEEDBACK
# ==========================================================

elif selected_page == "🤖 AI Assistant":

    st.markdown("""
    <style>

    [data-testid="stChatInput"] {
        background-color: #141D31 !important;
        border: 1px solid #7893FF !important;
        border-radius: 12px !important;
    }

    [data-testid="stChatInput"] textarea {
        background-color: #1B2740 !important;
        color: #F1F5F9 !important;
        -webkit-text-fill-color: #F1F5F9 !important;
        caret-color: #FFFFFF !important;
    }

    [data-testid="stChatInput"] textarea::placeholder {
        color: #94A3B8 !important;
        -webkit-text-fill-color: #94A3B8 !important;
        opacity: 1 !important;
    }

    [data-testid="stChatMessage"] {
        background-color: #141D31 !important;
        border: 1px solid #293650 !important;
        border-radius: 14px !important;
        padding: 15px !important;
        margin-bottom: 12px !important;
    }

    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] li {
        color: #F1F5F9 !important;
    }

    </style>
    """, unsafe_allow_html=True)

    st.title("🤖 SmartPlan AI Assistant")

    st.caption(
        "Ask me to manage tasks, prioritize your work or plan your day."
    )

    st.divider()

    # Display existing conversation and feedback controls.
    for message_index, message in enumerate(
        st.session_state.chat_messages
    ):

        with st.chat_message(message["role"]):
            st.markdown(message["content"])

        if message["role"] != "assistant":
            continue

        # Use a unique ID for each assistant message.
        # Older messages without IDs receive one automatically.
        if "message_id" not in message:
            message["message_id"] = uuid.uuid4().hex

        feedback_key = message["message_id"]

        # Find the user message associated with this response.
        previous_user_message = ""

        for previous_message in reversed(
            st.session_state.chat_messages[:message_index]
        ):

            if previous_message["role"] == "user":
                previous_user_message = previous_message["content"]
                break

        if feedback_key in st.session_state.feedback_submitted:

            rating = st.session_state.feedback_submitted[feedback_key]

            if rating == 1:
                st.caption("✓ You marked this response as helpful.")
            else:
                st.caption("✓ Your feedback has been recorded.")

        else:

            with st.container(border=True):

                st.markdown("**Was this response helpful?**")

                feedback_comment = st.text_area(
                    "Optional feedback",
                    placeholder=(
                        "Tell SmartPlan AI what was helpful "
                        "or what could be improved..."
                    ),
                    key=f"feedback_comment_{feedback_key}",
                    height=80
                )

                feedback_col1, feedback_col2 = st.columns(2)

                with feedback_col1:

                    if st.button(
                        "👍 Helpful",
                        key=f"positive_feedback_{feedback_key}",
                        use_container_width=True
                    ):

                        try:

                            save_feedback(
                                previous_user_message,
                                message["content"],
                                1,
                                feedback_comment.strip()
                            )

                            st.session_state.feedback_submitted[
                                feedback_key
                            ] = 1

                            st.success(
                                "Thank you for your feedback!"
                            )

                            st.rerun()

                        except Exception as error:

                            st.error(
                                f"Could not save feedback: {error}"
                            )

                with feedback_col2:

                    if st.button(
                        "👎 Not Helpful",
                        key=f"negative_feedback_{feedback_key}",
                        use_container_width=True
                    ):

                        try:

                            save_feedback(
                                previous_user_message,
                                message["content"],
                                -1,
                                feedback_comment.strip()
                            )

                            st.session_state.feedback_submitted[
                                feedback_key
                            ] = -1

                            st.success(
                                "Thank you! Your feedback will help "
                                "identify areas for improvement."
                            )

                            st.rerun()

                        except Exception as error:

                            st.error(
                                f"Could not save feedback: {error}"
                            )

    # Chat input.
    user_prompt = st.chat_input(
        "What would you like me to help you with?"
    )

    if user_prompt:

        st.session_state.chat_messages.append({
            "role": "user",
            "content": user_prompt,
            "message_id": uuid.uuid4().hex
        })

        with st.chat_message("user"):
            st.markdown(user_prompt)

        with st.chat_message("assistant"):

            with st.spinner("SmartPlan AI is thinking..."):

                try:

                    response = ask_smartplan(user_prompt)

                    if isinstance(response, dict):

                        answer = (
                            response.get("response")
                            or response.get("message")
                            or response.get("answer")
                            or str(response)
                        )

                    else:
                        answer = str(response)

                    st.markdown(answer)

                except Exception as error:

                    answer = (
                        "I encountered an error while processing "
                        f"your request: {error}"
                    )

                    st.error(answer)

        st.session_state.chat_messages.append({
            "role": "assistant",
            "content": answer,
            "message_id": uuid.uuid4().hex
        })

        st.rerun()

    # Clear conversation.
    st.divider()

    if st.button(
        "🗑️ Clear Chat",
        use_container_width=True,
        key="clear_ai_chat"
    ):

        st.session_state.chat_messages = []
        st.session_state.feedback_submitted = {}

        st.rerun()

# ==========================================================
# 16. PRIORITIES
# ==========================================================

elif selected_page == "🎯 Priorities":

    st.title("🎯 Task Priorities")

    st.caption(
        "Your tasks ranked according to urgency, importance "
        "and deadline proximity."
    )

    tasks = get_tasks()

    try:
        ranked_tasks = rank_tasks(tasks)

        if ranked_tasks:

            st.subheader("Recommended Task Order")

            for index, task in enumerate(ranked_tasks, start=1):

                with st.container(border=True):

                    col1, col2 = st.columns([4, 1])

                    with col1:

                        st.markdown(
                            f"### {index}. {task['title']}"
                        )

                        st.caption(
                            f"Deadline: {task.get('deadline', 'Not set')}"
                        )

                    with col2:

                        score = task.get("priority_score")

                        if score is not None:
                            st.metric(
                                "Priority Score",
                                f"{float(score):.2f}"
                            )

        else:
            st.info("No pending tasks to prioritize.")

    except Exception as error:
        st.error(f"Could not rank tasks: {error}")


# ==========================================================
# 17. DAILY PLANNER — MORNING, EVENING & NIGHT
# ==========================================================

elif selected_page == "📅 Daily Planner":

    st.title("📅 My Daily Planner")

    st.caption(
        "Organise your day into three focused sessions: "
        "learn in the morning, practise in the evening, "
        "and complete assignments at night."
    )

    if not DAILY_SCHEDULE_AVAILABLE:

        st.error(
            "Daily Schedule Manager is unavailable. "
            "Please check daily_schedule_manager.py."
        )

        st.code(DAILY_SCHEDULE_ERROR or "Unknown import error")

    else:

        selected_date = st.date_input(
            "📅 Select planning date",
            value=date.today(),
            key="daily_planner_date"
        )

        st.divider()

        sessions = {
            "Morning": {
                "start": "06:00",
                "end": "12:00",
                "title": "Theory & Revision",
                "description": (
                    "Start your day by learning, reading "
                    "and revising important concepts."
                ),
                "icon": "🌅",
                "color": "#FBBF24",
                "image": (
                    "https://images.unsplash.com/"
                    "photo-1434030216411-0b793f4b4173"
                    "?auto=format&fit=crop&w=1400&q=85"
                ),
                "suggestions": [
                    "Revise theoretical modules",
                    "Read lecture notes",
                    "Review previous lessons",
                    "Prepare for examinations",
                    "Memorise important concepts"
                ],
                "default_start": dt_time(6, 0),
                "default_end": dt_time(7, 0)
            },

            "Evening": {
                "start": "16:00",
                "end": "20:00",
                "title": "Practice & Skill Development",
                "description": (
                    "Strengthen your knowledge through "
                    "practical exercises and problem-solving."
                ),
                "icon": "🌇",
                "color": "#38BDF8",
                "image": (
                    "https://images.unsplash.com/"
                    "photo-1516321318423-f06f85e504b3"
                    "?auto=format&fit=crop&w=1400&q=85"
                ),
                "suggestions": [
                    "Mathematics practice",
                    "Statistics exercises",
                    "Python programming",
                    "Machine learning practice",
                    "Solve coding problems"
                ],
                "default_start": dt_time(16, 0),
                "default_end": dt_time(17, 0)
            },

            "Night": {
                "start": "20:00",
                "end": "23:30",
                "title": "Assignments & Projects",
                "description": (
                    "Use your evening focus time to complete "
                    "academic work and make project progress."
                ),
                "icon": "🌙",
                "color": "#A78BFA",
                "image": (
                    "https://images.unsplash.com/"
                    "photo-1498050108023-c5249f4df085"
                    "?auto=format&fit=crop&w=1400&q=85"
                ),
                "suggestions": [
                    "Complete university assignments",
                    "Work on group projects",
                    "Develop AI projects",
                    "Prepare reports and documentation",
                    "Finish unfinished tasks"
                ],
                "default_start": dt_time(20, 0),
                "default_end": dt_time(21, 0)
            }
        }

        category_options = [
            "Study",
            "Classes",
            "Assignment",
            "Personal",
            "Exercise",
            "Break",
            "Meals",
            "Work",
            "Other"
        ]

        category_icons = {
            "Study": "📚",
            "Classes": "🎓",
            "Assignment": "📝",
            "Personal": "👤",
            "Exercise": "🏃",
            "Break": "☕",
            "Meals": "🍽️",
            "Work": "💻",
            "Other": "📌"
        }

        try:
            activities = get_activities(selected_date)

            activities = sorted(
                activities,
                key=lambda item: str(
                    item.get("start_time", "")
                )
            )

        except Exception as error:
            activities = []
            st.error(
                f"Could not load activities: {error}"
            )

        def get_activity_session(activity):

            start_value = str(
                activity.get("start_time", "")
            )[:5]

            try:
                start_minutes = (
                    int(start_value[:2]) * 60
                    + int(start_value[3:5])
                )
            except (ValueError, IndexError):
                return "Other"

            if 360 <= start_minutes < 720:
                return "Morning"

            elif 960 <= start_minutes < 1200:
                return "Evening"

            elif 1200 <= start_minutes <= 1410:
                return "Night"

            return "Other"

        session_activities = {
            "Morning": [],
            "Evening": [],
            "Night": [],
            "Other": []
        }

        for activity in activities:

            session_name = get_activity_session(activity)

            session_activities[session_name].append(activity)

        total_activities = len(activities)

        completed_activities = [
            item for item in activities
            if item.get("status") == "Completed"
        ]

        pending_activities = [
            item for item in activities
            if item.get("status") != "Completed"
        ]

        completed_count = len(completed_activities)

        progress = (
            completed_count / total_activities
            if total_activities else 0
        )

        st.subheader("📊 Your Daily Progress")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Total Activities",
            total_activities
        )

        col2.metric(
            "Completed",
            completed_count
        )

        col3.metric(
            "Remaining",
            len(pending_activities)
        )

        col4.metric(
            "Daily Progress",
            f"{progress * 100:.0f}%"
        )

        st.progress(progress)

        st.caption(
            f"You have completed {completed_count} "
            f"out of {total_activities} planned activities."
        )

        st.divider()

        st.subheader("🗓️ Plan Your Day")

        st.caption(
            "Choose a session below to add activities, "
            "view your timetable and track your progress."
        )

        tab_morning, tab_evening, tab_night, tab_other = st.tabs([
            "🌅 Morning",
            "🌇 Evening",
            "🌙 Night",
            "📌 Other Times"
        ])

        def render_session(session_name):

            session = sessions[session_name]
            session_icon = session["icon"]
            session_items = session_activities[session_name]

            session_completed = [
                item for item in session_items
                if item.get("status") == "Completed"
            ]

            session_total = len(session_items)
            session_done = len(session_completed)

            session_progress = (
                session_done / session_total
                if session_total else 0
            )

            st.image(
                session["image"],
                use_container_width=True
            )

            st.markdown(
                f"## {session_icon} {session_name} Session"
            )

            st.markdown(
                f"### {session['title']}"
            )

            st.write(session["description"])

            st.markdown(
                f"**Usual time:** "
                f"{session['start']} – {session['end']}"
            )

            progress_col1, progress_col2 = st.columns(2)

            progress_col1.metric(
                "Activities",
                session_total
            )

            progress_col2.metric(
                "Completed",
                session_done
            )

            st.progress(session_progress)

            st.caption(
                f"Session completion: "
                f"{session_progress * 100:.0f}%"
            )

            with st.expander(
                "💡 Suggested activities for this session"
            ):

                for suggestion in session["suggestions"]:
                    st.markdown(f"- {suggestion}")

            st.divider()

            with st.expander(
                f"➕ Add {session_name} Activity",
                expanded=(session_total == 0)
            ):

                with st.form(
                    f"add_activity_{session_name}"
                ):

                    new_title = st.text_input(
                        "Activity name",
                        placeholder="What do you want to accomplish?"
                    )

                    new_description = st.text_area(
                        "Description (optional)",
                        placeholder=(
                            "Write what you want to complete "
                            "during this activity."
                        )
                    )

                    new_category = st.selectbox(
                        "Category",
                        category_options,
                        key=f"new_category_{session_name}"
                    )

                    time_col1, time_col2 = st.columns(2)

                    with time_col1:

                        new_start = st.time_input(
                            "Start time",
                            value=session["default_start"],
                            key=f"new_start_{session_name}"
                        )

                    with time_col2:

                        new_end = st.time_input(
                            "End time",
                            value=session["default_end"],
                            key=f"new_end_{session_name}"
                        )

                    new_reminder = st.checkbox(
                        "🔔 Enable desktop reminders",
                        value=True,
                        key=f"new_reminder_{session_name}"
                    )

                    submitted = st.form_submit_button(
                        "➕ Save Activity",
                        use_container_width=True
                    )

                    if submitted:

                        if not new_title.strip():

                            st.error(
                                "Please enter an activity name."
                            )

                        elif new_end <= new_start:

                            st.error(
                                "Ending time must be later "
                                "than starting time."
                            )

                        else:

                            try:

                                activity_id = add_activity(
                                    title=new_title.strip(),
                                    description=new_description.strip(),
                                    activity_date=selected_date,
                                    start_time=new_start,
                                    end_time=new_end,
                                    category=new_category,
                                    reminder_enabled=new_reminder
                                )

                                if activity_id is not None and activity_id is not False:

                                    st.success(
                                        "Activity saved successfully!"
                                    )

                                    st.rerun()

                                else:

                                    st.error(
                                        "Activity could not be saved."
                                    )

                            except Exception as error:

                                st.error(
                                    f"Could not add activity: {error}"
                                )

            st.divider()

            st.markdown(
                f"### 📋 Your {session_name} Activities"
            )

            if not session_items:

                st.info(
                    f"No activities planned for your "
                    f"{session_name.lower()} session yet."
                )

            for activity in session_items:

                activity_id = activity.get("id")
                title = activity.get("title", "Untitled")
                description = activity.get("description", "")

                start_value = str(
                    activity.get("start_time", "")
                )[:5]

                end_value = str(
                    activity.get("end_time", "")
                )[:5]

                category = activity.get(
                    "category", "Other"
                )

                status = activity.get(
                    "status", "Pending"
                )

                is_completed = status == "Completed"

                icon = category_icons.get(category, "📌")

                with st.container(border=True):

                    col1, col2, col3 = st.columns(
                        [1.5, 4.5, 1.5]
                    )

                    with col1:

                        st.markdown(
                            f"### {start_value}"
                        )

                        st.caption(
                            f"Until {end_value}"
                        )

                    with col2:

                        if is_completed:

                            st.markdown(
                                f"~~{icon} {title}~~"
                            )

                            st.success("Completed")

                        else:

                            st.markdown(
                                f"### {icon} {title}"
                            )

                            st.caption(
                                f"Category: {category}"
                            )

                        if description:
                            st.write(description)

                        if activity.get("reminder_enabled"):
                            st.caption("🔔 Reminders enabled")
                        else:
                            st.caption("🔕 Reminders disabled")

                    with col3:

                        if not is_completed:

                            if st.button(
                                "✓ Complete",
                                key=f"complete_{session_name}_{activity_id}",
                                use_container_width=True
                            ):

                                try:

                                    complete_activity(activity_id)

                                    st.success(
                                        "Activity completed!"
                                    )

                                    st.rerun()

                                except Exception as error:

                                    st.error(
                                        f"Could not complete activity: {error}"
                                    )

                    with st.expander(
                        "⚙️ Edit or Delete Activity"
                    ):

                        with st.form(
                            f"edit_form_{session_name}_{activity_id}"
                        ):

                            edited_title = st.text_input(
                                "Activity name",
                                value=title,
                                key=f"edit_title_{activity_id}"
                            )

                            edited_description = st.text_area(
                                "Description",
                                value=description,
                                key=f"edit_description_{activity_id}"
                            )

                            category_index = (
                                category_options.index(category)
                                if category in category_options
                                else category_options.index("Other")
                            )

                            edited_category = st.selectbox(
                                "Category",
                                category_options,
                                index=category_index,
                                key=f"edit_category_{activity_id}"
                            )

                            try:

                                current_start = datetime.strptime(
                                    start_value,
                                    "%H:%M"
                                ).time()

                                current_end = datetime.strptime(
                                    end_value,
                                    "%H:%M"
                                ).time()

                            except ValueError:

                                current_start = dt_time(6, 0)
                                current_end = dt_time(7, 0)

                            edit_col1, edit_col2 = st.columns(2)

                            with edit_col1:

                                edited_start = st.time_input(
                                    "Start time",
                                    value=current_start,
                                    key=f"edit_start_{activity_id}"
                                )

                            with edit_col2:

                                edited_end = st.time_input(
                                    "End time",
                                    value=current_end,
                                    key=f"edit_end_{activity_id}"
                                )

                            edited_reminder = st.checkbox(
                                "Enable reminders",
                                value=bool(
                                    activity.get("reminder_enabled", 1)
                                ),
                                key=f"edit_reminder_{activity_id}"
                            )

                            save_changes = st.form_submit_button(
                                "💾 Save Changes",
                                use_container_width=True
                            )

                            if save_changes:

                                if not edited_title.strip():

                                    st.error(
                                        "Activity name cannot be empty."
                                    )

                                elif edited_end <= edited_start:

                                    st.error(
                                        "Ending time must be later "
                                        "than starting time."
                                    )

                                else:

                                    try:

                                        update_activity(
                                            activity_id=activity_id,
                                            title=edited_title.strip(),
                                            description=edited_description.strip(),
                                            activity_date=selected_date,
                                            start_time=edited_start,
                                            end_time=edited_end,
                                            category=edited_category,
                                            reminder_enabled=edited_reminder
                                        )

                                        st.success(
                                            "Activity updated!"
                                        )

                                        st.rerun()

                                    except Exception as error:

                                        st.error(
                                            f"Could not update activity: {error}"
                                        )

                        st.divider()

                        if st.button(
                            "🗑️ Delete Activity",
                            key=f"delete_{session_name}_{activity_id}",
                            use_container_width=True
                        ):

                            try:

                                delete_activity(activity_id)

                                st.success(
                                    "Activity deleted."
                                )

                                st.rerun()

                            except Exception as error:

                                st.error(
                                    f"Could not delete activity: {error}"
                                )

        with tab_morning:
            render_session("Morning")

        with tab_evening:
            render_session("Evening")

        with tab_night:
            render_session("Night")

        with tab_other:

            st.markdown("## 📌 Other Activities")

            st.write(
                "Activities scheduled outside the three "
                "main sessions appear here."
            )

            other_items = session_activities["Other"]

            if not other_items:

                st.info(
                    "No activities outside your main sessions."
                )

            for activity in other_items:

                with st.container(border=True):

                    st.markdown(
                        f"### 📌 {activity.get('title', 'Untitled')}"
                    )

                    st.caption(
                        f"{activity.get('start_time', '')} – "
                        f"{activity.get('end_time', '')}"
                    )

                    st.write(
                        activity.get("description", "")
                    )

                    if activity.get("status") != "Completed":

                        if st.button(
                            "✓ Complete",
                            key=f"complete_other_{activity.get('id')}"
                        ):

                            complete_activity(
                                activity.get("id")
                            )

                            st.rerun()

                    with st.expander("⚙️ Manage activity"):

                        if st.button(
                            "🗑️ Delete",
                            key=f"delete_other_{activity.get('id')}"
                        ):

                            delete_activity(
                                activity.get("id")
                            )

                            st.rerun()

        st.divider()

        st.subheader("🔔 Daily Activity Reminders")

        if NOTIFICATION_MANAGER_AVAILABLE:

            st.success(
                "Your notification system is connected."
            )

            st.info(
                "Keep reminder_service.py running in a "
                "separate terminal to receive desktop reminders. "
                "Activities with reminders enabled are scheduled "
                "for five minutes before and at their start time."
            )

        else:

            st.warning(
                "Notification manager is unavailable. "
                "Activity reminders cannot currently be scheduled."
            )

        st.divider()

        with st.expander(
            "🤖 Generate an AI Suggested Task Plan"
        ):

            st.write(
                "Use your existing pending tasks to generate "
                "an additional suggested timetable."
            )

            ai_col1, ai_col2 = st.columns(2)

            with ai_col1:

                ai_start_time = st.time_input(
                    "AI plan starting time",
                    value=dt_time(6, 0),
                    key="ai_plan_start"
                )

            with ai_col2:

                ai_end_time = st.time_input(
                    "AI plan ending time",
                    value=dt_time(23, 0),
                    key="ai_plan_end"
                )

            if st.button(
                "✨ Generate AI Suggested Plan",
                use_container_width=True
            ):

                start_minutes = (
                    ai_start_time.hour * 60
                    + ai_start_time.minute
                )

                end_minutes = (
                    ai_end_time.hour * 60
                    + ai_end_time.minute
                )

                if end_minutes <= start_minutes:

                    st.error(
                        "Ending time must be later than starting time."
                    )

                else:

                    try:

                        available_minutes = (
                            end_minutes - start_minutes
                        )

                        suggested_plan = generate_daily_plan(
                            ai_start_time.strftime("%H:%M"),
                            available_minutes,
                            ai_end_time.strftime("%H:%M")
                        )

                        st.session_state.daily_plan = suggested_plan

                    except Exception as error:

                        st.error(
                            f"Could not generate AI plan: {error}"
                        )

            if st.session_state.daily_plan is not None:

                st.markdown("### Suggested Task Schedule")

                suggested_plan = st.session_state.daily_plan

                if suggested_plan:

                    for index, item in enumerate(
                        suggested_plan,
                        start=1
                    ):

                        st.markdown(
                            f"**{index}. {item['task']}**"
                        )

                        st.caption(
                            f"{item['start']} – {item['end']} "
                            f"| {item['duration']} minutes "
                            f"| Priority: {item['priority_score']:.2f}"
                        )

                else:

                    st.info(
                        "No pending tasks could be fitted into "
                        "the selected time period."
                    )


# ==========================================================
# 18. STUDY TIMER
# ==========================================================

elif selected_page == "⏱️ Study Timer":

    st.title("⏱️ Study Timer")

    st.caption(
        "Study and break timers work independently. "
        "Completing one will not automatically start the other."
    )

    if not STUDY_MANAGER_AVAILABLE:
        st.warning(
            "study_manager.py is missing. Study history "
            "and statistics will not be available."
        )

    if not NOTIFICATION_MANAGER_AVAILABLE:
        st.warning(
            "notification_manager.py is unavailable. "
            "Desktop notifications cannot be scheduled."
        )
    else:
        st.caption(
            "Keep reminder_service.py running in another terminal "
            "for desktop alarms."
        )

    st.subheader("📚 Study Settings")

    study_duration_options = [
        1, 2, 3, 5, 10, 15, 20, 25,
        30, 45, 60, 90, 120
    ]

    subject = st.text_input(
        "What are you studying?",
        value=st.session_state.study_timer_subject,
        key="study_subject_input"
    )

    study_choice = st.selectbox(
        "Study duration",
        options=study_duration_options + ["Custom"],
        index=study_duration_options.index(25),
        format_func=lambda value: (
            f"{value} minutes"
            if isinstance(value, int)
            else value
        ),
        key="study_duration_choice"
    )

    if study_choice == "Custom":

        study_minutes = st.number_input(
            "Custom study duration (minutes)",
            min_value=1,
            max_value=300,
            value=25,
            step=1,
            key="custom_study_duration"
        )

    else:
        study_minutes = int(study_choice)

    st.session_state.study_timer_subject = (
        subject.strip() or "General Study"
    )

    st.session_state.study_timer_duration_minutes = int(
        study_minutes
    )

    if st.session_state.study_timer_status == "idle":
        st.session_state.study_timer_remaining = (
            int(study_minutes) * 60
        )

    st.divider()

    st.subheader("📚 Study Timer")

    study_status = st.session_state.study_timer_status

    study_col1, study_col2, study_col3 = st.columns(3)

    with study_col1:

        if study_status in ("idle", "finished"):

            if st.button(
                "▶ Start Study",
                use_container_width=True,
                key="start_study_timer"
            ):

                timer_start(
                    "study",
                    int(study_minutes) * 60,
                    "Study session completed! 🎉",
                    (
                        f"Your {st.session_state.study_timer_subject} "
                        "study session has finished."
                    ),
                    "study"
                )

                st.rerun()

        elif study_status == "paused":

            if st.button(
                "▶ Resume Study",
                use_container_width=True,
                key="resume_study_timer"
            ):

                timer_resume(
                    "study",
                    "Study session completed! 🎉",
                    (
                        f"Your {st.session_state.study_timer_subject} "
                        "study session has finished."
                    ),
                    "study"
                )

                st.rerun()

        elif study_status == "running":

            if st.button(
                "⏸ Pause Study",
                use_container_width=True,
                key="pause_study_timer"
            ):
                timer_pause("study")
                st.rerun()

    with study_col2:

        if study_status in ("running", "paused", "finished"):

            if st.button(
                "↻ Reset Study",
                use_container_width=True,
                key="reset_study_timer"
            ):
                timer_reset("study")
                st.rerun()

    with study_col3:
        st.caption(f"Status: **{study_status.title()}**")

    st.divider()

    st.subheader("☕ Break Timer")

    break_duration_options = [
        10, 30, 60, 120, 180,
        300, 600, 900, 1200, "Custom"
    ]

    break_choice = st.selectbox(
        "Break duration",
        options=break_duration_options,
        index=5,
        format_func=lambda value: (
            f"{value} seconds"
            if isinstance(value, int) and value < 60
            else f"{value // 60} minute(s)"
            if isinstance(value, int)
            else value
        ),
        key="break_duration_choice"
    )

    if break_choice == "Custom":

        custom_break_seconds = st.number_input(
            "Custom break duration (seconds)",
            min_value=1,
            max_value=7200,
            value=300,
            step=1,
            key="custom_break_duration_seconds"
        )

        break_seconds = int(custom_break_seconds)

    else:
        break_seconds = int(break_choice)

    st.session_state.break_timer_duration_seconds = int(
        break_seconds
    )

    if st.session_state.break_timer_status == "idle":
        st.session_state.break_timer_remaining = int(
            break_seconds
        )

    st.markdown("---")

    break_status = st.session_state.break_timer_status

    break_col1, break_col2, break_col3 = st.columns(3)

    with break_col1:

        if break_status in ("idle", "finished"):

            if st.button(
                "▶ Start Break",
                use_container_width=True,
                key="start_break_timer"
            ):

                timer_start(
                    "break",
                    int(break_seconds),
                    "Break completed! ⏰",
                    "Your break is over. Time to focus again!",
                    "break"
                )

                st.rerun()

        elif break_status == "paused":

            if st.button(
                "▶ Resume Break",
                use_container_width=True,
                key="resume_break_timer"
            ):

                timer_resume(
                    "break",
                    "Break completed! ⏰",
                    "Your break is over. Time to focus again!",
                    "break"
                )

                st.rerun()

        elif break_status == "running":

            if st.button(
                "⏸ Pause Break",
                use_container_width=True,
                key="pause_break_timer"
            ):
                timer_pause("break")
                st.rerun()

    with break_col2:

        if break_status in ("running", "paused", "finished"):

            if st.button(
                "↻ Reset Break",
                use_container_width=True,
                key="reset_break_timer"
            ):
                timer_reset("break")
                st.rerun()

    with break_col3:
        st.caption(f"Status: **{break_status.title()}**")

    st.divider()

    live_timer_dashboard()

    alarm_timer_page_control()

    st.divider()

    st.subheader("📚 Study History")

    if STUDY_MANAGER_AVAILABLE:

        try:
            stats = get_study_statistics()

            a, b, c = st.columns(3)

            a.metric(
                "Completed Sessions",
                stats["completed_sessions"]
            )

            b.metric(
                "Total Study Time",
                format_duration(stats["total_minutes"])
            )

            c.metric(
                "Today's Study Time",
                format_duration(stats["today_minutes"])
            )

            sessions = get_study_sessions(20)

            with st.expander(
                "📚 Recent Sessions",
                expanded=False
            ):

                if sessions:
                    display_table(sessions)
                else:
                    st.info(
                        "Your completed study sessions will appear here."
                    )

        except Exception as error:
            st.warning(
                f"Could not load study history: {error}"
            )


# ==========================================================
# 19. MY MEMORY
# ==========================================================

elif selected_page == "🧠 My Memory":

    st.title("🧠 My Memory")

    st.caption(
        "SmartPlan AI can use saved information and conversation history."
    )

    tab1, tab2 = st.tabs([
        "Saved Memories",
        "Recent Conversations"
    ])

    with tab1:

        st.subheader("Saved Memories")

        try:
            memories = get_memories()

            if memories:
                display_table(memories)
            else:
                st.info("No saved memories yet.")

        except Exception as error:
            st.error(
                f"Could not retrieve memories: {error}"
            )

    with tab2:

        st.subheader("Recent Conversations")

        try:
            conversations = get_recent_conversations()

            if conversations:
                display_table(conversations)
            else:
                st.info("No recent conversations found.")

        except Exception as error:
            st.error(
                f"Could not retrieve conversation history: {error}"
            )


# ==========================================================
# 20. NOTIFICATIONS
# ==========================================================

elif selected_page == "🔔 Notifications":

    st.title("🔔 Notifications")

    st.caption(
        "View reminders and scheduled alerts from SmartPlan AI."
    )

    if not NOTIFICATION_MANAGER_AVAILABLE:

        st.warning(
            "notification_manager.py is not available."
        )

    else:

        try:
            notifications = get_notifications(100)

            if notifications:

                for item in notifications:

                    with st.container(border=True):

                        col1, col2 = st.columns([5, 1])

                        with col1:

                            status = item.get("status", "pending")

                            if status == "sent":
                                st.success(item["title"])

                            elif status == "pending":
                                st.info(item["title"])

                            elif status == "cancelled":
                                st.caption(
                                    f"Cancelled: {item['title']}"
                                )

                            else:
                                st.caption(item["title"])

                            st.write(item["message"])

                            st.caption(
                                f"Type: {item.get('notification_type', 'general')} "
                                f"| Scheduled: {item.get('scheduled_at', '-')}"
                            )

                        with col2:

                            if status == "pending":

                                if st.button(
                                    "Cancel",
                                    key=f"cancel_notification_{item['id']}"
                                ):

                                    cancel_notification(item["id"])
                                    st.rerun()

            else:
                st.info("You have no notifications yet.")

        except Exception as error:
            st.error(
                f"Could not load notifications: {error}"
            )


# ==========================================================
# 21. STUDY NOTES
# ==========================================================

elif selected_page == "📚 Study Notes":

    render_study_notes_page()
