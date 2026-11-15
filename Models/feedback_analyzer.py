
from feedback_manager import get_recent_feedback, get_feedback_statistics


def analyze_feedback():
    """
    Analyse recent user feedback and generate
    recommendations for improving the agent.
    """

    feedback = get_recent_feedback(50)
    statistics = get_feedback_statistics()

    total = statistics["total"]
    positive = statistics["positive"]
    negative = statistics["negative"]

    result = {
        "total_feedback": total,
        "positive_feedback": positive,
        "negative_feedback": negative,
        "positive_rate": 0,
        "recommendations": []
    }

    if total == 0:
        result["recommendations"].append(
            "No feedback available yet. Collect user feedback first."
        )
        return result

    result["positive_rate"] = round(
        (positive / total) * 100, 2
    )

    if negative > positive:
        result["recommendations"].append(
            "Improve response quality because negative feedback is higher."
        )

    elif positive == total:
        result["recommendations"].append(
            "Users are satisfied with the agent's recent responses."
        )

    else:
        result["recommendations"].append(
            "Continue monitoring feedback and improve weak responses."
        )

    comments = [
        item["feedback_comment"].strip()
        for item in feedback
        if item["rating"] == -1
        and item["feedback_comment"]
        and item["feedback_comment"].strip()
    ]

    if comments:
        result["recommendations"].append(
            "Review negative feedback comments to identify recurring problems."
        )

    result["negative_comments"] = comments

    return result


def get_adaptation_guidance():
    """
    Convert feedback analysis into guidance
    that can be used by the AI agent.
    """

    analysis = analyze_feedback()

    guidance = [
        "Use previous user feedback to improve response quality."
    ]

    for recommendation in analysis["recommendations"]:
        guidance.append(recommendation)

    if analysis.get("negative_comments"):
        guidance.append(
            "Pay attention to these previous user complaints: "
            + "; ".join(analysis["negative_comments"][:5])
        )

    return "\n".join(guidance)
