"""
Main Flask application for the MVP Workout Generator.
Handles user input for workout preferences and generates a workout plan
using the Google Gemini API.
"""
import os
import json
from datetime import date, timedelta # Added
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import database as db
from weekly_planner import generate_and_save_weekly_plan
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

# Helper function
def get_current_week_start_date():
    """Returns the date of the most recent Monday."""
    today = date.today()
    return today - timedelta(days=today.weekday()) # Monday is 0, Sunday is 6

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
        if not data:
            return jsonify({"error": "Invalid request: No data provided or data is not valid JSON."}), 400

        db.save_user_settings(user_id, data)
        app.logger.info(f"User settings saved for user_id {user_id}.")

        # After saving settings, generate and save the weekly plan
        try:
            # Ensure 'data' contains all necessary fields for generate_and_save_weekly_plan
            # It should, as it's coming directly from the frontend settings form
            app.logger.info(f"Attempting to generate weekly plan for user_id {user_id} with settings: {data}")
            generate_and_save_weekly_plan(user_id, data, db.get_db_connection)
            app.logger.info(f"Weekly plan generated and saved for user_id {user_id} after settings update.")
        except Exception as e_plan:
            app.logger.error(f"Error generating weekly plan after saving settings for user_id {user_id}: {e_plan}", exc_info=True)
            # Do not fail the entire settings save if plan generation fails, but log it.
            # Could return a partial success or a warning if desired.

        return jsonify({"message": "Settings saved successfully! Weekly plan updated."}), 200
    except Exception as e:
        app.logger.error(f"Error saving user settings or generating plan: {e}", exc_info=True)
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

@app.route("/get_current_weekly_plan", methods=["GET"])
def get_current_weekly_plan_route():
    user_id = 1 # Hardcoded for now
    try:
        week_start_date = get_current_week_start_date()
        plan = db.get_weekly_plan(user_id, week_start_date)
        if plan is None: # get_weekly_plan might return None or raise an exception
            plan = []
        return jsonify(plan)
    except Exception as e:
        app.logger.error(f"Error getting current weekly plan: {e}", exc_info=True)
        return jsonify({"error": "Could not retrieve weekly plan."}), 500

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
            # Prepare user_data for the generator, mapping from request data

            # Fetch recent workout history and today's planned pillar
            recent_history_list = db.get_workout_history(user_id, days=4) # Fetch last 4 days to likely get 2-3 workouts

            today_date_obj = date.today()
            week_start_obj = get_current_week_start_date()
            current_weekly_plan = db.get_weekly_plan(user_id, week_start_obj)

            todays_plan_entry_dict = None
            if current_weekly_plan:
                for day_plan in current_weekly_plan:
                    if day_plan['day_of_week'] == today_date_obj.weekday():
                        todays_plan_entry_dict = day_plan
                        break

            todays_planned_pillar_str = f"Today's Planned Pillar: {todays_plan_entry_dict['pillar_focus']}" if todays_plan_entry_dict else "Today's Planned Pillar: Not specifically planned (User selected)."

            history_summary_parts = []
            if recent_history_list:
                for entry in recent_history_list[:3]: # Max 3 entries
                    muscles = ', '.join(entry['muscles_worked']) if isinstance(entry['muscles_worked'], list) else entry['muscles_worked']
                    history_summary_parts.append(f"- {entry['workout_date'][:10]}: {entry['pillar']}, Focus: {entry['focus']}, Muscles: {muscles}")

            recent_history_str = "Recent Training History (last few sessions):\n" + "\n".join(history_summary_parts) if history_summary_parts else "Recent Training History: No recent workouts logged."

            user_data_for_generator = {
                "workout_pillar": data.get("workout_pillar"),
                "strength_style": data.get("strength_style"),
                "experience": data.get("experience"),
                "equipment": data.get("equipment"),
                "focus": data.get("focus"),
                "userNotes": data.get("userNotes"),
                "todays_planned_pillar": todays_planned_pillar_str, # Added
                "recent_history": recent_history_str # Added
            }
            app.logger.info(f"Data passed to workout generator: {user_data_for_generator}")

            workout_data = generate_workout_plan(user_data_for_generator, settings, api_key)
            
            # Save the generated workout to history
            # workout_data["pillar"] from the generator now correctly reflects the actual pillar
            # (e.g., "Strength", "Zone2 Cardio")
            db.save_workout_to_history(
                user_id,
                workout_data["pillar"], # This should be the actual pillar like "Strength", "Zone2 Cardio"
                workout_data["focus"],
                workout_data["muscles_worked"],
                workout_data["workout_text"]
            )
            app.logger.info(f"Workout saved to history for user {user_id}. Pillar: {workout_data['pillar']}, Focus: {workout_data['focus']}")
            
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
