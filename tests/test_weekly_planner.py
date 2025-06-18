import unittest
from unittest.mock import MagicMock, patch, call
import datetime
# Assuming weekly_planner.py is in the root directory /app
# and tests/ is a subdirectory. If running from /app, this should work.
import sys
import os
# Add the parent directory (/app) to sys.path to find weekly_planner and database
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from weekly_planner import generate_and_save_weekly_plan
# database module will be mocked, so direct import isn't strictly needed in test file
# but weekly_planner itself imports it.

class TestWeeklyPlanner(unittest.TestCase):

    def mock_db_connection(self):
        # Create a mock connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.lastrowid = 1 # Example
        return mock_conn

    @patch('weekly_planner.database') # Mock the entire database module used by weekly_planner
    def test_generate_and_save_weekly_plan_normal_distribution(self, mock_db_module):
        # mock_conn = self.mock_db_connection() # Not strictly needed if db_connection_func is also mocked
        # mock_db_module.get_db_connection.return_value = mock_conn

        # Mock the db_connection_func directly if it's passed in
        mock_db_connection_func = MagicMock()
        mock_conn_instance = self.mock_db_connection()
        mock_db_connection_func.return_value = mock_conn_instance


        user_id = 1
        user_settings = {
            "strength_freq": 2, "zone2_freq": 2, "hiit_freq": 1,
            "stability_freq": 1, "primary_goal": "Balanced Fitness"
            # Total 6 workout days, 1 rest day
        }

        # We need to control the date for consistent testing of clear_weekly_plan args
        fixed_today = datetime.date(2024, 7, 15) # A Monday
        with patch('weekly_planner.datetime.date') as mock_date:
            mock_date.today.return_value = fixed_today
            mock_date.side_effect = lambda *args, **kw: datetime.date(*args, **kw) # Allow date object creation

            generate_and_save_weekly_plan(user_id, user_settings, mock_db_connection_func)

            # Assert clear_weekly_plan was called
            # The first argument to clear_weekly_plan is user_id, second is week_start_date (which is fixed_today)
            # The third is the connection object from mock_db_connection_func
            mock_db_module.clear_weekly_plan.assert_called_once_with(user_id, fixed_today, conn=mock_conn_instance)

            # Assert save_daily_plan_entry was called 7 times (6 workouts + 1 rest)
            self.assertEqual(mock_db_module.save_daily_plan_entry.call_count, 7)

            # Example: check that pillar distribution seems plausible
            calls_to_save = mock_db_module.save_daily_plan_entry.call_args_list
            pillars_saved = [c.args[0]['pillar_focus'] for c in calls_to_save]
            self.assertEqual(pillars_saved.count("Strength"), 2)
            self.assertEqual(pillars_saved.count("Zone2"), 2)
            self.assertEqual(pillars_saved.count("HIIT"), 1)
            self.assertEqual(pillars_saved.count("Stability"), 1)
            self.assertEqual(pillars_saved.count("Rest"), 1)


    @patch('weekly_planner.database')
    def test_generate_and_save_weekly_plan_overflow_frequency(self, mock_db_module):
        mock_db_connection_func = MagicMock()
        mock_conn_instance = self.mock_db_connection()
        mock_db_connection_func.return_value = mock_conn_instance

        user_id = 1
        user_settings = { # Total 9, should be capped at 7
            "strength_freq": 3, "zone2_freq": 3, "hiit_freq": 2, "stability_freq": 1
        }
        fixed_today = datetime.date(2024, 7, 15) # A Monday
        with patch('weekly_planner.datetime.date') as mock_date:
            mock_date.today.return_value = fixed_today
            mock_date.side_effect = lambda *args, **kw: datetime.date(*args, **kw)

            generate_and_save_weekly_plan(user_id, user_settings, mock_db_connection_func)

            self.assertEqual(mock_db_module.save_daily_plan_entry.call_count, 7)
            # Check prioritization (Strength > HIIT > Zone2 > Stability)
            calls_to_save = mock_db_module.save_daily_plan_entry.call_args_list
            pillars_saved = [c.args[0]['pillar_focus'] for c in calls_to_save]
            self.assertEqual(pillars_saved.count("Strength"), 3)
            self.assertEqual(pillars_saved.count("HIIT"), 2)
            self.assertEqual(pillars_saved.count("Zone2"), 2) # 3+2+2=7
            self.assertEqual(pillars_saved.count("Stability"), 0) # Stability gets cut
            self.assertEqual(pillars_saved.count("Rest"), 0)


    @patch('weekly_planner.database')
    def test_generate_and_save_weekly_plan_zero_frequency(self, mock_db_module):
        mock_db_connection_func = MagicMock()
        mock_conn_instance = self.mock_db_connection()
        mock_db_connection_func.return_value = mock_conn_instance

        user_id = 1
        user_settings = {
            "strength_freq": 0, "zone2_freq": 0, "hiit_freq": 0, "stability_freq": 0
        }
        fixed_today = datetime.date(2024, 7, 15) # A Monday
        with patch('weekly_planner.datetime.date') as mock_date:
            mock_date.today.return_value = fixed_today
            mock_date.side_effect = lambda *args, **kw: datetime.date(*args, **kw)

            generate_and_save_weekly_plan(user_id, user_settings, mock_db_connection_func)

            self.assertEqual(mock_db_module.save_daily_plan_entry.call_count, 7)
            calls_to_save = mock_db_module.save_daily_plan_entry.call_args_list
            pillars_saved = [c.args[0]['pillar_focus'] for c in calls_to_save]
            self.assertEqual(pillars_saved.count("Rest"), 7)

if __name__ == '__main__':
    unittest.main()
