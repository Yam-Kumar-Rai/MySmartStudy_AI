
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


# ==========================================================
# IMPORT CONFIGURATION
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "Models"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if str(MODELS_DIR) not in sys.path:
    sys.path.insert(0, str(MODELS_DIR))

import agent

# ==========================================================
# SMARTPLAN AI TOOL TEST CASES
# ==========================================================

class SmartPlanToolTests(unittest.TestCase):

    # ------------------------------------------------------
    # TEST 1: ADD TASK
    # ------------------------------------------------------

    @patch.object(agent, "add_task", return_value=101)
    def test_add_task_success(self, mock_add):

        result = agent.execute_tool(
            "add_task",
            {
                "title": "Study Machine Learning",
                "duration": 60,
                "importance": 5,
                "urgency": 4
            }
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["task_id"], 101)
        mock_add.assert_called_once()

    # ------------------------------------------------------
    # TEST 2: ADD TASK WITH EMPTY TITLE
    # ------------------------------------------------------

    @patch.object(agent, "add_task")
    def test_add_task_empty_title(self, mock_add):

        with self.assertRaises(ValueError):

            agent.execute_tool(
                "add_task",
                {"title": "   "}
            )

        mock_add.assert_not_called()

    # ------------------------------------------------------
    # TEST 3: LIST PENDING TASKS
    # ------------------------------------------------------

    @patch.object(agent, "get_tasks")
    def test_list_tasks(self, mock_get):

        mock_get.return_value = [
            {
                "id": 1,
                "title": "Assignment",
                "status": "Pending"
            },
            {
                "id": 2,
                "title": "Completed work",
                "status": "Completed"
            }
        ]

        result = agent.execute_tool(
            "list_tasks", {}
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], 1)

    # ------------------------------------------------------
    # TEST 4: PRIORITIZE TASKS
    # ------------------------------------------------------

    @patch.object(agent, "rank_tasks")
    @patch.object(agent, "get_tasks")
    def test_prioritize_tasks(
        self,
        mock_get,
        mock_rank
    ):

        tasks = [
            {"id": 1, "title": "Assignment"}
        ]

        expected = [
            {"id": 1, "title": "Assignment", "priority": 1}
        ]

        mock_get.return_value = tasks
        mock_rank.return_value = expected

        result = agent.execute_tool(
            "prioritize_tasks", {}
        )

        self.assertEqual(result, expected)
        mock_rank.assert_called_once_with(tasks)

    # ------------------------------------------------------
    # TEST 5: COMPLETE TASK
    # ------------------------------------------------------

    @patch.object(agent, "complete_task", return_value=True)
    def test_complete_task_success(self, mock_complete):

        result = agent.execute_tool(
            "complete_task",
            {"task_id": 101}
        )

        self.assertTrue(result["success"])
        mock_complete.assert_called_once_with(101)

    # ------------------------------------------------------
    # TEST 6: INVALID TASK ID
    # ------------------------------------------------------

    @patch.object(agent, "complete_task")
    def test_complete_task_invalid_id(self, mock_complete):

        with self.assertRaises(ValueError):

            agent.execute_tool(
                "complete_task",
                {"task_id": "invalid"}
            )

        mock_complete.assert_not_called()

    # ------------------------------------------------------
    # TEST 7: CREATE DAILY PLAN
    # ------------------------------------------------------

    @patch.object(agent, "generate_daily_plan")
    def test_create_daily_plan(
        self,
        mock_plan
    ):

        expected = [
            {
                "task": "Study Python",
                "start_time": "09:00"
            }
        ]

        mock_plan.return_value = expected

        result = agent.execute_tool(
            "create_daily_plan",
            {
                "start_time": "09:00",
                "available_minutes": 120
            }
        )

        self.assertEqual(result, expected)

        mock_plan.assert_called_once_with(
            "09:00", 120
        )

    # ------------------------------------------------------
    # TEST 8: INVALID DAILY PLAN TIME
    # ------------------------------------------------------

    @patch.object(agent, "generate_daily_plan")
    def test_daily_plan_invalid_minutes(self, mock_plan):

        with self.assertRaises(ValueError):

            agent.execute_tool(
                "create_daily_plan",
                {
                    "start_time": "09:00",
                    "available_minutes": -30
                }
            )

        mock_plan.assert_not_called()

    # ------------------------------------------------------
    # TEST 9: SAVE MEMORY
    # ------------------------------------------------------

    @patch.object(agent, "save_memory")
    def test_save_memory(self, mock_save):

        result = agent.execute_tool(
            "save_memory",
            {
                "memory_key": "study_preference",
                "memory_value": "Prefers morning study",
                "category": "preference"
            }
        )

        self.assertTrue(result["success"])

        mock_save.assert_called_once_with(
            memory_key="study_preference",
            memory_value="Prefers morning study",
            category="preference"
        )

    # ------------------------------------------------------
    # TEST 10: INVALID MEMORY
    # ------------------------------------------------------

    @patch.object(agent, "save_memory")
    def test_save_memory_empty_value(self, mock_save):

        with self.assertRaises(ValueError):

            agent.execute_tool(
                "save_memory",
                {
                    "memory_key": "study_preference",
                    "memory_value": "   "
                }
            )

        mock_save.assert_not_called()

    # ------------------------------------------------------
    # TEST 11: UNKNOWN TOOL
    # ------------------------------------------------------

    def test_unknown_tool(self):

        with self.assertRaises(ValueError):

            agent.execute_tool(
                "unknown_tool", {}
            )


# ==========================================================
# RUN TEST SUITE
# ==========================================================

if __name__ == "__main__":

    print("\n" + "=" * 55)
    print("       SMARTPLAN AI CONTROLLED TEST SUITE")
    print("=" * 55)

    unittest.main(verbosity=2)
