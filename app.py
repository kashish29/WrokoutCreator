"""
Main Flask application for the MVP Workout Generator.
Handles user input for workout preferences and generates a workout plan
using the Google Gemini API.
"""
import os
import json
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import database as db
from ai_provider import SimpleGeminiProvider
from workout_generator import generate_workout_plan

# Load environment variables from .env file for local development
load_dotenv()

app = Flask(__name__)

# API Key Configuration
USER_CONFIG_FILE = "user_config.json"

def load_gemini_api_key():
    """Loads the Gemini API key from config file or environment variable."""
    try:
        with open(USER_CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            return config.get("GEMINI_API_KEY")
    except FileNotFoundError:
        return os.getenv("GEMINI_API_KEY")
    except json.JSONDecodeError:
        app.logger.error(f"Error decoding {USER_CONFIG_FILE}. Using environment variable for API key.")
        return os.getenv("GEMINI_API_KEY")

# Initialize the database
with app.app_context():
    db.setup_database()

@app.route("/")
def index():
    """Renders the main workout configuration page."""
    return render_template("index.html")

@app.route("/save_settings", methods=["POST"])
def save_settings():
    try:
        data = request.get_json()
        gemini_key = data.get("geminiApiKey")
        if not gemini_key:
            return jsonify({"error": "API key is required."}), 400

        config_data = {"GEMINI_API_KEY": gemini_key}

        with open(USER_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4)

        # Test the new key by initializing the provider
        try:
            SimpleGeminiProvider({"gemini_api_key": gemini_key})
            app.logger.info("Gemini provider validated with new key.")
        except Exception as e:
            app.logger.error(f"Failed to initialize Gemini provider with new key: {e}")
            return jsonify({"error": "Invalid Gemini API Key."}), 400

        app.logger.info(f"Gemini API Key saved to {USER_CONFIG_FILE}.")
        return jsonify({"message": "API Key saved successfully!"}), 200
    except Exception as e:
        app.logger.error(f"Error saving settings: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred while saving settings."}), 500

@app.route("/get_user_settings", methods=["GET"])
def get_user_settings():
    # For now, we'll use a hardcoded user_id. In a real app, you'd get this from the session.
    user_id = 1
    try:
        settings = db.get_user_settings(user_id)
        return jsonify(settings)
    except Exception as e:
        app.logger.error(f"Error getting user settings: {e}", exc_info=True)
        return jsonify({"error": "Could not retrieve user settings."}), 500

@app.route("/save_user_settings", methods=["POST"])
def save_user_settings():
    # For now, we'll use a hardcoded user_id.
    user_id = 1
    try:
        data = request.get_json()
        db.save_user_settings(user_id, data)
        return jsonify({"message": "Settings saved successfully!"}), 200
    except Exception as e:
        app.logger.error(f"Error saving user settings: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred while saving settings."}), 500

@app.route("/get_workout_history", methods=["GET"])
def get_workout_history():
    # For now, we'll use a hardcoded user_id.
    user_id = 1
    try:
        days = int(request.args.get('days', 14))
        history = db.get_workout_history(user_id, days)
        return jsonify(history)
    except Exception as e:
        app.logger.error(f"Error getting workout history: {e}", exc_info=True)
        return jsonify({"error": "Could not retrieve workout history."}), 500

@app.route("/generate_workout", methods=["POST"])
def generate_workout():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "Invalid request: No data provided or data is not valid JSON."}), 400

        user_id = 1  # Hardcoded for now
        settings = db.get_user_settings(user_id)
        api_key = load_gemini_api_key()

        if not api_key:
            return jsonify({"error": "AI service is not configured. Please save your Gemini API key in User Settings."}), 500

        try:
            workout_data = generate_workout_plan(data, settings, api_key)
            
            # Save the generated workout to history
            db.save_workout_to_history(
                user_id,
                workout_data["pillar"],
                workout_data["focus"],
                workout_data["muscles_worked"],
                workout_data["workout_text"]
            )
            app.logger.info(f"Workout saved to history for user {user_id}.")
            
            return jsonify(workout_data)

        except ValueError as e:
            app.logger.error(f"Workout generation failed: {e}")
            return jsonify({"error": str(e)}), 500
        except Exception as e:
            app.logger.error(f"An unexpected error occurred in generate_workout: {e}", exc_info=True)
            return jsonify({"error": "An unexpected error occurred. Please try again."}), 500

    except Exception as e:
        app.logger.error(f"An unexpected error occurred in generate_workout: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred. Please try again."}), 500

@app.route("/save_workout", methods=["POST"])
def save_workout():
    user_id = 1 # Hardcoded for now
    try:
        data = request.get_json()
        pillar = data.get("pillar")
        focus = data.get("focus")
        muscles_worked = data.get("muscles_worked")
        full_workout_text = data.get("full_workout_text")

        if not all([pillar, focus, muscles_worked, full_workout_text]):
            return jsonify({"error": "Missing required workout data."}), 400

        db.save_workout_to_history(user_id, pillar, focus, muscles_worked, full_workout_text)
        return jsonify({"message": "Workout saved successfully!"}), 200
    except Exception as e:
        app.logger.error(f"Error saving workout: {e}", exc_info=True)
        return jsonify({"error": "Could not save workout."}), 500

@app.route("/delete_workout/<int:workout_id>", methods=["DELETE"])
def delete_workout(workout_id):
    user_id = 1 # Hardcoded for now, in a real app, you'd verify ownership
    try:
        db.delete_workout_from_history(workout_id)
        app.logger.info(f"Workout with ID {workout_id} deleted for user {user_id}.")
        return jsonify({"message": "Workout deleted successfully!"}), 200
    except Exception as e:
        app.logger.error(f"Error deleting workout {workout_id}: {e}", exc_info=True)
        return jsonify({"error": "Could not delete workout."}), 500

if __name__ == "__main__":
    app.run(debug=True)
