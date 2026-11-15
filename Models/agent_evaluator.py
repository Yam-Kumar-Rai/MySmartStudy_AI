
from collections import defaultdict

from agent_logger import get_agent_logs


# ==========================================================
# CONFIGURATION
# ==========================================================

LOG_LIMIT = 10000


# ==========================================================
# HELPER FUNCTIONS
# ==========================================================

def count_events(logs, event_type):
    """Count occurrences of a specific event."""

    return sum(
        1 for log in logs
        if log.get("event_type") == event_type
    )


def calculate_percentage(numerator, denominator):
    """Calculate percentage safely."""

    if denominator == 0:
        return 0

    return round((numerator / denominator) * 100, 2)


# ==========================================================
# TOOL PERFORMANCE EVALUATION
# ==========================================================

def evaluate_tool_performance(logs):
    """Evaluate the performance of individual agent tools."""

    tool_statistics = defaultdict(
        lambda: {
            "selected": 0,
            "successful": 0,
            "failed": 0
        }
    )

    for log in logs:

        event_type = log.get("event_type")
        tool_name = log.get("tool_name")

        if not tool_name:
            continue

        if event_type == "tool_selected":
            tool_statistics[tool_name]["selected"] += 1

        elif event_type == "tool_completed":
            tool_statistics[tool_name]["successful"] += 1

        elif event_type == "tool_error":
            tool_statistics[tool_name]["failed"] += 1

    results = {}

    for tool_name, stats in tool_statistics.items():

        total_executions = (
            stats["successful"] + stats["failed"]
        )

        results[tool_name] = {
            "selected": stats["selected"],
            "successful": stats["successful"],
            "failed": stats["failed"],
            "success_rate": calculate_percentage(
                stats["successful"],
                total_executions
            )
        }

    return results


# ==========================================================
# MAIN AGENT EVALUATION
# ==========================================================

def evaluate_agent_performance():
    """Evaluate SmartPlan AI using its recorded activity."""

    logs = get_agent_logs(limit=LOG_LIMIT)

    # 1. Agent activity

    agent_started = count_events(
        logs, "agent_started"
    )

    agent_completed = count_events(
        logs, "agent_completed"
    )

    agent_errors = count_events(
        logs, "agent_error"
    )

    # 2. Agent performance

    total_outcomes = agent_completed + agent_errors

    completion_rate = calculate_percentage(
        agent_completed,
        total_outcomes
    )

    error_rate = calculate_percentage(
        agent_errors,
        total_outcomes
    )

    # 3. Tool activity

    tools_selected = count_events(
        logs, "tool_selected"
    )

    tools_completed = count_events(
        logs, "tool_completed"
    )

    tools_failed = count_events(
        logs, "tool_error"
    )

    total_tool_executions = (
        tools_completed + tools_failed
    )

    tool_success_rate = calculate_percentage(
        tools_completed,
        total_tool_executions
    )

    # 4. Individual tool performance

    tool_performance = evaluate_tool_performance(logs)

    # 5. Recent errors

    recent_errors = []

    for log in logs:

        if log.get("event_type") in (
            "agent_error",
            "tool_error"
        ):

            recent_errors.append({
                "event_type": log.get("event_type"),
                "user_message": log.get("user_message"),
                "tool_name": log.get("tool_name"),
                "error": log.get("error"),
                "created_at": log.get("created_at")
            })

    # 6. Recommendations

    recommendations = []

    if total_outcomes == 0:

        recommendations.append(
            "No completed or failed agent outcomes are available yet."
        )

    elif error_rate > 20:

        recommendations.append(
            "Agent error rate is high. Investigate recent agent errors."
        )

    elif agent_errors > 0:

        recommendations.append(
            "Review failed agent requests to identify possible improvements."
        )

    else:

        recommendations.append(
            "No agent-level errors were recorded in the available logs."
        )

    if total_tool_executions == 0:

        recommendations.append(
            "No completed tool executions are available for evaluation."
        )

    elif tool_success_rate < 80:

        recommendations.append(
            "Tool execution success rate needs improvement."
        )

    else:

        recommendations.append(
            "Tool execution success rate is satisfactory in the available logs."
        )

    for tool_name, stats in tool_performance.items():

        if stats["failed"] > 0:

            recommendations.append(
                f"Investigate {tool_name}: "
                f"{stats['failed']} failed execution(s)."
            )

    # 7. Return evaluation results

    return {
        "total_log_records": len(logs),

        "agent_statistics": {
            "started": agent_started,
            "completed": agent_completed,
            "failed": agent_errors,
            "completion_rate": completion_rate,
            "error_rate": error_rate
        },

        "tool_statistics": {
            "selected": tools_selected,
            "successful": tools_completed,
            "failed": tools_failed,
            "success_rate": tool_success_rate
        },

        "individual_tools": tool_performance,

        "recent_errors": recent_errors[:10],

        "recommendations": recommendations
    }


# ==========================================================
# PRINT EVALUATION REPORT
# ==========================================================

def print_evaluation_report():

    report = evaluate_agent_performance()

    print("\n" + "=" * 55)
    print("          SMARTPLAN AI EVALUATION REPORT")
    print("=" * 55)

    print("\n1. GENERAL ACTIVITY")

    print(
        "Total log records:",
        report["total_log_records"]
    )

    print("\n2. AGENT PERFORMANCE")

    for key, value in report["agent_statistics"].items():

        print(f"{key.replace('_', ' ').title()}: {value}")

    print("\n3. TOOL PERFORMANCE")

    for key, value in report["tool_statistics"].items():

        print(f"{key.replace('_', ' ').title()}: {value}")

    print("\n4. INDIVIDUAL TOOL PERFORMANCE")

    if not report["individual_tools"]:

        print("No tool activity recorded.")

    else:

        for tool_name, stats in report["individual_tools"].items():

            print(f"\nTool: {tool_name}")

            for key, value in stats.items():

                print(f"  {key.replace('_', ' ').title()}: {value}")

    print("\n5. RECENT ERRORS")

    if not report["recent_errors"]:

        print("No errors found in the available logs.")

    else:

        for error in report["recent_errors"]:

            print("\nEvent:", error["event_type"])
            print("Tool:", error["tool_name"])
            print("Message:", error["user_message"])
            print("Error:", error["error"])
            print("Time:", error["created_at"])

    print("\n6. RECOMMENDATIONS")

    for recommendation in report["recommendations"]:

        print("-", recommendation)

    print("\n" + "=" * 55)

    return report


# ==========================================================
# RUN EVALUATION
# ==========================================================

if __name__ == "__main__":

    print_evaluation_report()
