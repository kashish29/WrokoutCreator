import unittest
from unittest.mock import patch, MagicMock
import sys
import os
# Add the parent directory (/app) to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from workout_generator import generate_workout_plan

class TestWorkoutGeneratorPrompts(unittest.TestCase):

    def common_user_data(self, pillar, strength_style=None, equipment=None, experience="Intermediate", focus="Full Body", notes="Feeling good."):
        data = {
            "workout_pillar": pillar,
            "strength_style": strength_style if strength_style else ("Build Muscle" if pillar == "Strength" else None),
            "experience": experience,
            "equipment": equipment if equipment else ["Bodyweight only"],
            "focus": focus,
            "userNotes": notes,
            "todays_planned_pillar": f"Today's Planned Pillar: {pillar or 'User selected'}.", # Simulate basic context
            "recent_history": "Recent Training History: - 2024-07-14: Strength, Focus: Upper Body, Muscles: Chest, Triceps" # Simulate some history
        }
        return data

    def common_settings(self):
        return {"ai_model_id": "gemini-1.5-flash-latest", "workout_duration_preference": "Medium"}

    def_ai_response_json = '{"workout_text": "Sample workout text", "muscles_worked": ["Sample"]}'

    def setUp(self):
        # This setup will mock SimpleGeminiProvider for all tests in this class
        self.patcher = patch('workout_generator.SimpleGeminiProvider')
        self.MockGeminiProvider = self.patcher.start()

        self.mock_provider_instance = MagicMock()
        self.mock_model = MagicMock()
        self.mock_ai_response = MagicMock()
        self.mock_ai_response.text = self.def_ai_response_json # Default response
        self.mock_model.generate_content.return_value = self.mock_ai_response
        self.mock_provider_instance.model = self.mock_model
        self.MockGeminiProvider.return_value = self.mock_provider_instance

    def tearDown(self):
        self.patcher.stop()

    def get_generated_prompt(self):
        # Helper to get the prompt passed to the AI model
        self.assertTrue(self.mock_model.generate_content.called, "AI model's generate_content was not called.")
        return self.mock_model.generate_content.call_args[0][0]

    def test_missing_pillar_raises_error(self):
        user_data = self.common_user_data(None) # No pillar
        with self.assertRaisesRegex(ValueError, "'workout_pillar' is a required field"):
            generate_workout_plan(user_data, self.common_settings(), "fake_api_key")

    def test_strength_prompt_bodyweight_build_muscle(self):
        user_data = self.common_user_data("Strength", strength_style="Build Muscle", equipment=["Bodyweight only"])
        generate_workout_plan(user_data, self.common_settings(), "fake_api_key")
        prompt = self.get_generated_prompt()
        self.assertIn("### **PART 1B: TRAINING CONTEXT**", prompt)
        self.assertIn("Recent Training History:", prompt)
        self.assertIn("Governing Training Methodology:", prompt)
        self.assertIn("Antagonist/Agonist Supersets", prompt) # Default for Build Muscle
        self.assertIn("Bodyweight Training Principles", prompt)
        self.assertIn("Core Pre-Fatigue Avoidance", prompt)
        # Antagonist supersets handles push/pull, so the explicit rule might not be there.

    def test_strength_prompt_advanced_build_muscle_pre_exhaustion(self):
        # To make this test deterministic, we might need to patch random.choice if it's used
        # For now, assume it might pick pre-exhaustion or might not.
        # A more robust test would mock random.choice to force Pre-exhaustion.
        with patch('workout_generator.random.choice', return_value=True): # Force Pre-exhaustion
            user_data = self.common_user_data("Strength", strength_style="Build Muscle", experience="Advanced")
            generate_workout_plan(user_data, self.common_settings(), "fake_api_key")
            prompt = self.get_generated_prompt()
            self.assertIn("Pre-exhaustion Sets", prompt)
            self.assertIn("Bodyweight Training Principles", prompt) # Default equipment

    def test_strength_prompt_advanced_get_stronger_contrast(self):
        with patch('workout_generator.random.choice', return_value=True): # Force Contrast Training
            user_data = self.common_user_data("Strength", strength_style="Get Stronger", experience="Advanced", equipment=["Barbell", "Box"])
            generate_workout_plan(user_data, self.common_settings(), "fake_api_key")
            prompt = self.get_generated_prompt()
            self.assertIn("Contrast Training", prompt)
            self.assertNotIn("Bodyweight Training Principles", prompt)
            self.assertIn("Push/Pull Balance (General Strength)", prompt) # Contrast training might not be push/pull pair based

    def test_strength_prompt_general_fitness_no_bodyweight_principles(self):
        user_data = self.common_user_data("Strength", strength_style="General Fitness (Strength)", equipment=["Dumbbells", "Bench"])
        generate_workout_plan(user_data, self.common_settings(), "fake_api_key")
        prompt = self.get_generated_prompt()
        self.assertIn("Full-Body Circuit Training", prompt)
        self.assertNotIn("Bodyweight Training Principles", prompt)
        self.assertIn("Push/Pull Balance (General Strength)", prompt)


    def test_zone2_prompt_with_cardio_equipment(self):
        user_data = self.common_user_data("Zone2 Cardio", equipment=["Stationary Bike", "Treadmill"])
        generate_workout_plan(user_data, self.common_settings(), "fake_api_key")
        prompt = self.get_generated_prompt()
        self.assertIn("Selected Workout Pillar: Zone2 Cardio", prompt)
        self.assertIn("Cardio Equipment Priority:", prompt)
        self.assertIn("Stationary Bike, Treadmill", prompt)
        self.assertIn("Machine-Specific Parameters:", prompt)
        self.assertNotIn("Bodyweight Training Principles", prompt)

    def test_zone2_prompt_bodyweight_only(self):
        user_data = self.common_user_data("Zone2 Cardio", equipment=["Bodyweight only"])
        generate_workout_plan(user_data, self.common_settings(), "fake_api_key")
        prompt = self.get_generated_prompt()
        self.assertIn("Selected Workout Pillar: Zone2 Cardio", prompt)
        self.assertIn("Exercise Selection: Choose 1-2 suitable bodyweight cardio options", prompt) # Check for bodyweight specific instruction
        self.assertNotIn("Cardio Equipment Priority:", prompt)

    def test_hiit_prompt_selects_protocol_and_cardio_equip(self):
        user_data = self.common_user_data("HIIT", equipment=["Stationary Bike", "Dumbbells"])
        # Mock random.choice to select a specific protocol for predictability
        # Example: Force selection of "Norwegian 4x4"
        mock_norwegian_protocol = {
            "name": "Norwegian 4x4 (Classic VO2 Max)",
            "description": "4 reps of 4 min high intensity / 3 min active recovery.",
            "work_intensity": "RPE 9-10", "rest_intensity": "RPE 5-6",
            "structure_detail": "4x(4min/3min)",
        }
        with patch('workout_generator.random.choice', return_value=mock_norwegian_protocol):
            generate_workout_plan(user_data, self.common_settings(), "fake_api_key")
            prompt = self.get_generated_prompt()

        self.assertIn("Governing HIIT Protocol:", prompt)
        self.assertIn("Norwegian 4x4", prompt)
        self.assertIn("Cardio Equipment Priority for HIIT:", prompt)
        self.assertIn("Stationary Bike", prompt) # Dumbbells are not cardio machines
        self.assertNotIn("Bodyweight Training Principles", prompt)

    def test_stability_mobility_prompt_bodyweight(self):
        user_data = self.common_user_data("Stability/Mobility", equipment=["Bodyweight only"], focus="Core")
        generate_workout_plan(user_data, self.common_settings(), "fake_api_key")
        prompt = self.get_generated_prompt()
        self.assertIn("Selected Workout Pillar: Stability/Mobility", prompt)
        self.assertIn("Workout Focus for Today: Core", prompt)
        self.assertIn("Bodyweight Training Principles (Stability/Mobility)", prompt)
        self.assertIn("Tempo and Holds", prompt)

if __name__ == '__main__':
    unittest.main()
