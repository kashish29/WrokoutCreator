"""
Unit tests for the MVP Workout Generator Flask application.
"""
import os
import json
import unittest
from unittest.mock import patch, MagicMock

# Add the project root to sys.path to allow direct import of app
import sys
# Assuming the script is run from a directory where mvp_workout_generator is a subdirectory
# or mvp_workout_generator is in PYTHONPATH
# For subtasks, the structure is usually flat, so direct import might fail.
# Let's try to adjust sys.path relative to this script's assumed location if needed.
# However, the subtask environment might already handle this.
# The initial subtask created app.py in mvp_workout_generator.
# So, to import `from mvp_workout_generator.app import app`, the parent of mvp_workout_generator must be in path.
# This is typically the case if you run `python -m unittest discover` from the project root.

# Let's assume the execution context for the subtask handles path correctly for `mvp_workout_generator.app`
import mvp_workout_generator.app # Import the module itself to access module-level attributes like 'openai'
from mvp_workout_generator.app import app # Import the Flask app instance


class TestApp(unittest.TestCase):
    """Test suite for the Flask application."""

    def setUp(self):
        """Set up test client and other test variables."""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False # Ensure debug is off for testing some error handlers
        # If there are specific configs like WTF_CSRF_ENABLED for forms, disable them
        # app.config["WTF_CSRF_ENABLED"] = False
        self.client = app.test_client()
        # Ensure a clean environment for API key tests
        self.original_openai_api_key = os.environ.pop("OPENAI_API_KEY", None)
        # Also clear openai.api_key from the imported module for consistent testing
        # The 'openai' module is imported in 'mvp_workout_generator.app'
        self.original_module_api_key = mvp_workout_generator.app.openai.api_key
        mvp_workout_generator.app.openai.api_key = None


    def tearDown(self):
        """Clean up after each test."""
        if self.original_openai_api_key is not None:
            os.environ["OPENAI_API_KEY"] = self.original_openai_api_key
        else:
            # Ensure it is removed if it was set during a test and not originally there
            os.environ.pop("OPENAI_API_KEY", None)
        # Restore openai.api_key in the module
        mvp_workout_generator.app.openai.api_key = self.original_module_api_key


    def test_index_route(self):
        """Test the index route (/) loads correctly."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Workout Generator", response.data) # Check for a keyword in index.html

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_api_key_value"})
    @patch("mvp_workout_generator.app.openai.ChatCompletion.create")
    def test_generate_workout_success(self, mock_openai_create):
        """Test successful workout generation."""
        mvp_workout_generator.app.openai.api_key = "test_api_key_value" # Ensure module key is set for this test
        # Configure the mock to return a successful response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.content = "Your **generated** workout plan."
        mock_openai_create.return_value = mock_response

        payload = {
            "goal": "Build Muscle",
            "experience": "Intermediate",
            "equipment": ["Dumbbells", "Bodyweight only"],
            "focus": "Upper Body"
        }
        response = self.client.post("/generate_workout", json=payload)
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertIn("workout", data)
        self.assertEqual(data["workout"], "Your **generated** workout plan.")
        mock_openai_create.assert_called_once()
        # You could also assert the prompt structure if needed by inspecting mock_openai_create.call_args

    # Patch os.environ for the duration of this test method
    @patch.dict(os.environ, {}, clear=True)
    def test_generate_workout_missing_api_key(self):
        """Test workout generation when API key is missing."""
        # Ensure openai.api_key is None directly on the module for this test's context
        # This is critical because app.py sets openai.api_key at module load time from os.getenv()
        with patch("mvp_workout_generator.app.openai.api_key", None):
            payload = {
                "goal": "Build Muscle",
                "experience": "Intermediate",
                "equipment": ["Dumbbells"],
                "focus": "Upper Body"
            }
            response = self.client.post("/generate_workout", json=payload)
            data = json.loads(response.data)

            self.assertEqual(response.status_code, 500)
            self.assertIn("error", data)
            self.assertIn("AI service is not configured", data["error"])


    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_api_key_value"})
    @patch("mvp_workout_generator.app.openai.ChatCompletion.create")
    def test_generate_workout_openai_api_error(self, mock_openai_create):
        """Test workout generation with an OpenAI API error."""
        mvp_workout_generator.app.openai.api_key = "test_api_key_value" # Ensure module key is set
        # It's better to import specific exceptions where they are used or at the top of the test method
        from openai import APIError # For openai v1.x
        mock_openai_create.side_effect = APIError("Test API Error from OpenAI", request=None, body=None)


        payload = {
            "goal": "Lose Fat",
            "experience": "Beginner",
            "equipment": ["Bodyweight only"],
            "focus": "Full Body"
        }
        response = self.client.post("/generate_workout", json=payload)
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 500)
        self.assertIn("error", data)
        # The exact error message structure might depend on how openai.error.APIError stringifies.
        # Let's check for the core message.
        self.assertIn("An error occurred with the AI service", data["error"])
        self.assertIn("Test API Error from OpenAI", data["error"])


    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_api_key_value"})
    def test_generate_workout_no_json_data(self):
        """Test workout generation with no JSON data posted."""
        mvp_workout_generator.app.openai.api_key = "test_api_key_value" # Ensure module key is set
        response = self.client.post("/generate_workout", data="not json", content_type="text/plain")
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", data)
        # Based on Flask's default behavior for request.get_json(silent=False) or request.get_json(force=True)
        # if content-type is not application/json, it might return a 400 or 415.
        # If request.get_json(silent=True) is used and fails (e.g. not json, or wrong content-type), it returns None.
        # The app.py now uses `data = request.get_json(silent=True)`.
        # So the check `if not data:` in app.py catches this.
        self.assertIn("Invalid request: No data provided or data is not valid JSON.", data["error"])


    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_api_key_value"})
    def test_generate_workout_missing_fields(self):
        """Test workout generation with missing fields in JSON payload."""
        mvp_workout_generator.app.openai.api_key = "test_api_key_value" # Ensure module key is set
        payload = {
            "goal": "Build Muscle",
            # "experience": "Intermediate", # Missing experience
            "equipment": ["Dumbbells"],
            "focus": "Upper Body"
        }
        response = self.client.post("/generate_workout", json=payload)
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", data)
        self.assertIn("Missing one or more required fields", data["error"])

if __name__ == "__main__":
    unittest.main()
