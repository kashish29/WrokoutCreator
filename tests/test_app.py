import os
import json
import unittest
from unittest.mock import patch, mock_open
import sys

# Add app from the parent directory to sys.path to allow import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, USER_CONFIG_FILE, load_api_key
# Assuming anatomy_data and random are accessed via app.random or app.anatomy_data if modified for testability
# For now, we will patch them directly using their original module names if they are global in app.py

class TestAppSettings(unittest.TestCase):
    def setUp(self):
        self.app_client = app.test_client()
        app.config['TESTING'] = True
        self.original_app_api_key = app.openai.api_key # Store original app's perspective of the key

        # Clean USER_CONFIG_FILE before each test
        if os.path.exists(USER_CONFIG_FILE):
            os.remove(USER_CONFIG_FILE)

        # Store original env var and set a test one for consistent fallback testing
        self.initial_env_api_key = os.environ.get("OPENAI_API_KEY")
        os.environ["OPENAI_API_KEY"] = "env_key_during_setup"

        # Reload key based on current state (no config, env var set above)
        # This ensures app.openai.api_key reflects a known state before each test.
        app.openai.api_key = load_api_key()


    def tearDown(self):
        if os.path.exists(USER_CONFIG_FILE):
            os.remove(USER_CONFIG_FILE)

        # Restore environment variable to its original state
        if self.initial_env_api_key is None:
            if "OPENAI_API_KEY" in os.environ: # if it was set during test/setup
                del os.environ["OPENAI_API_KEY"]
        else:
            os.environ["OPENAI_API_KEY"] = self.initial_env_api_key

        # Restore app's api key to what it was before this test class ran, or reload based on restored env
        app.openai.api_key = self.original_app_api_key
        # Or safer: app.openai.api_key = load_api_key() # re-evaluate based on restored environment
        app.config['TESTING'] = False

    def test_save_api_key_creates_config_and_updates_app_key(self):
        api_key_to_save = "test_api_key_12345"
        response = self.app_client.post('/save_settings',
                                        json={'apiKey': api_key_to_save},
                                        content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(os.path.exists(USER_CONFIG_FILE))
        with open(USER_CONFIG_FILE, "r") as f:
            config = json.load(f)
        self.assertEqual(config.get("OPENAI_API_KEY"), api_key_to_save)
        self.assertEqual(app.openai.api_key, api_key_to_save)

    def test_load_api_key_from_config_file(self):
        expected_key = "key_from_config_file_abc"
        with open(USER_CONFIG_FILE, "w") as f:
            json.dump({"OPENAI_API_KEY": expected_key}, f)

        app.openai.api_key = load_api_key()
        self.assertEqual(app.openai.api_key, expected_key)

    def test_load_api_key_fallback_to_env_if_config_missing(self):
        if os.path.exists(USER_CONFIG_FILE):
            os.remove(USER_CONFIG_FILE)

        expected_env_key = "env_key_for_fallback_test_xyz"
        os.environ["OPENAI_API_KEY"] = expected_env_key
        app.openai.api_key = load_api_key()
        self.assertEqual(app.openai.api_key, expected_env_key)

    def test_load_api_key_priority_config_over_env(self):
        config_key = "key_in_config_beats_env"
        env_key = "key_in_env_should_be_ignored"
        with open(USER_CONFIG_FILE, "w") as f:
            json.dump({"OPENAI_API_KEY": config_key}, f)
        os.environ["OPENAI_API_KEY"] = env_key

        app.openai.api_key = load_api_key()
        self.assertEqual(app.openai.api_key, config_key)

    def test_save_api_key_empty_returns_error(self):
        response = self.app_client.post('/save_settings',
                                        json={'apiKey': ''},
                                        content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn("API key is required", data.get("error"))

    @patch('app.open', new_callable=mock_open) # Patch open in app.py context
    @patch('app.os.path.exists', return_value=True) # Assume config may or may not exist
    def test_save_api_key_filesystem_error_on_write(self, mock_path_exists, mock_file_open_in_app):
        # Simulate that reading existing config is fine (if it exists)
        # but writing the new config fails.
        # If path doesn't exist, it tries to write directly. If it does, it tries to read then write.
        # Let's assume it exists and reading is fine, but writing fails.
        mock_path_exists.return_value = True
        mock_file_open_in_app.side_effect = [
            mock_open(read_data='{"OTHER_KEY": "some_value"}').return_value, # Successful read
            IOError("Failed to write") # Failed write
        ]

        # If path does not exist (first save attempt)
        # mock_path_exists.return_value = False
        # mock_file_open_in_app.side_effect = IOError("Failed to write")


        api_key_to_save = "test_key_io_error"
        response = self.app_client.post('/save_settings',
                                        json={'apiKey': api_key_to_save},
                                        content_type='application/json')
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertIn("An unexpected error occurred", data.get("error"))

MOCK_ANATOMY_DATA = {
    "Upper Body": {
        "Chest": ["Pectoralis Major", "Pectoralis Minor"],
        "Back": ["Latissimus Dorsi", "Trapezius"],
        "Shoulders": ["Anterior Deltoid", "Lateral Deltoid", "Posterior Deltoid"]
    },
    "Lower Body": {
        "Quads": ["Vastus Medialis", "Rectus Femoris"],
        "Hamstrings": ["Biceps Femoris", "Semitendinosus"],
        "Glutes": ["Gluteus Maximus", "Gluteus Medius"]
    },
    "Full Body": {
        "Push": ["Chest", "Shoulders", "Triceps"],
        "Pull": ["Back", "Biceps"],
        "Legs": ["Quads", "Glutes", "Hamstrings"]
    }
}

class TestWorkoutLogic(unittest.TestCase):
    def setUp(self):
        self.app_client = app.test_client()
        app.config['TESTING'] = True
        self.patcher_anatomy = patch('app.anatomy_data', MOCK_ANATOMY_DATA)
        self.mock_anatomy = self.patcher_anatomy.start()

        # Ensure API key is set for generate_workout endpoint
        self.original_app_api_key = app.openai.api_key
        app.openai.api_key = "test_mock_key_for_workout_logic"


    def tearDown(self):
        self.patcher_anatomy.stop()
        app.openai.api_key = self.original_app_api_key # Restore API key
        app.config['TESTING'] = False

    common_payload = {
        'experience': 'Intermediate',
        'equipment': ['Dumbbells', 'Barbell'],
        'userNotes': 'Feeling good today'
    }

    @patch('app.openai.ChatCompletion.create')
    def test_expert_rules_build_muscle(self, mock_openai_create):
        mock_openai_create.return_value.choices = [type('choice', (), {'message': type('msg', (), {'content': 'mocked workout'})})()]
        payload = {**self.common_payload, 'goal': 'Build Muscle', 'focus': 'Upper Body'}
        self.app_client.post('/generate_workout', json=payload)

        args, kwargs = mock_openai_create.call_args
        sent_prompt = kwargs['messages'][1]['content']
        self.assertIn("Methodology: Agonist/Antagonist Supersets", sent_prompt)
        self.assertIn("Intensity_Protocol: Aim for 8-12 reps per set", sent_prompt)

    @patch('app.openai.ChatCompletion.create')
    def test_expert_rules_get_stronger(self, mock_openai_create):
        mock_openai_create.return_value.choices = [type('choice', (), {'message': type('msg', (), {'content': 'mocked workout'})})()]
        payload = {**self.common_payload, 'goal': 'Get Stronger', 'focus': 'Lower Body'}
        self.app_client.post('/generate_workout', json=payload)
        args, kwargs = mock_openai_create.call_args
        sent_prompt = kwargs['messages'][1]['content']
        self.assertIn("Methodology: Traditional Straight Sets with Top Set/Back-off Sets", sent_prompt)
        self.assertIn("Intensity_Protocol: Main lift should be in the 3-5 rep range", sent_prompt)

    @patch('app.openai.ChatCompletion.create')
    def test_expert_rules_default_goal(self, mock_openai_create):
        mock_openai_create.return_value.choices = [type('choice', (), {'message': type('msg', (), {'content': 'mocked workout'})})()]
        payload = {**self.common_payload, 'goal': 'Lose Fat', 'focus': 'Full Body'}
        self.app_client.post('/generate_workout', json=payload)
        args, kwargs = mock_openai_create.call_args
        sent_prompt = kwargs['messages'][1]['content']
        self.assertIn("Methodology: Traditional Circuits", sent_prompt) # Default rule
        self.assertIn("Intensity_Protocol: Aim for 15-20 reps per set", sent_prompt)

    @patch('app.random.randrange') # Patch random.randrange used in app.py
    @patch('app.openai.ChatCompletion.create')
    def test_contextual_nudge_upper_body_selects_muscles(self, mock_openai_create, mock_randrange_in_app):
        # Flat list for "Upper Body" from MOCK_ANATOMY_DATA:
        # ["Pectoralis Major", "Pectoralis Minor", "Latissimus Dorsi", "Trapezius", "Anterior Deltoid", "Lateral Deltoid", "Posterior Deltoid"] (7 muscles)
        # Let randrange return indices 0 and 2: "Pectoralis Major" and "Latissimus Dorsi"
        mock_randrange_in_app.side_effect = [0, 2]
        mock_openai_create.return_value.choices = [type('choice', (), {'message': type('msg', (), {'content': 'mocked workout'})})()]

        payload = {**self.common_payload, 'goal': 'Build Muscle', 'focus': 'Upper Body'}
        self.app_client.post('/generate_workout', json=payload)

        args, kwargs = mock_openai_create.call_args
        sent_prompt = kwargs['messages'][1]['content']
        self.assertIn("primary stimulus on the **Pectoralis Major**", sent_prompt)
        self.assertIn("less direct volume to the **Latissimus Dorsi**", sent_prompt)

    @patch('app.random.randrange')
    @patch('app.openai.ChatCompletion.create')
    def test_contextual_nudge_single_sub_muscle_group(self, mock_openai_create, mock_randrange_in_app):
        custom_anatomy_for_test = {**MOCK_ANATOMY_DATA, "OnlyChest": {"Chest": ["Pectoralis Major"]}}

        # Patch app.anatomy_data specifically for this test method for clarity
        with patch('app.anatomy_data', custom_anatomy_for_test):
            mock_randrange_in_app.return_value = 0
            mock_openai_create.return_value.choices = [type('choice', (), {'message': type('msg', (), {'content': 'mocked workout'})})()]

            payload = {**self.common_payload, 'goal': 'Build Muscle', 'focus': 'OnlyChest'}
            self.app_client.post('/generate_workout', json=payload)

            args, kwargs = mock_openai_create.call_args
            sent_prompt = kwargs['messages'][1]['content']
            self.assertIn("primary stimulus on the **Pectoralis Major**", sent_prompt)
            self.assertIn("less direct volume to the **other muscle groups**", sent_prompt)

    @patch('app.openai.ChatCompletion.create')
    def test_generate_workout_missing_fields_returns_400(self, mock_openai_create):
        response = self.app_client.post('/generate_workout', json={
            'goal': 'Build Muscle',
            'equipment': ['Dumbbells'],
            'focus': 'Upper Body'
            # Missing 'experience'
        })
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn("Missing one or more required fields", data.get("error"))

    def test_generate_workout_no_api_key_returns_500(self):
        # This test needs to ensure app.openai.api_key is None *before* the request
        current_key = app.openai.api_key
        app.openai.api_key = None
        try:
            response = self.app_client.post('/generate_workout', json={**self.common_payload, 'goal': 'Build Muscle', 'focus': 'Upper Body'})
            self.assertEqual(response.status_code, 500)
            data = json.loads(response.data)
            self.assertIn("AI service is not configured", data.get("error"))
        finally:
            app.openai.api_key = current_key # Restore for other tests

if __name__ == '__main__':
    unittest.main()
