"""
Main Flask application for the MVP Workout Generator.
Handles user input for workout preferences and generates a workout plan
using the OpenAI API.
"""
import os
from flask import Flask, request, jsonify, render_template
import openai
from dotenv import load_dotenv

# Load environment variables from .env file for local development
load_dotenv()

app = Flask(__name__)

# Set OpenAI API key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/")
def index():
    """Renders the main workout configuration page."""
    # This assumes index.html will be created in a later step by another subtask or exists.
    # The previous subtask for step 1 mentioned creating templates/index.html
    return render_template("index.html")

@app.route("/generate_workout", methods=["POST"])
def generate_workout():
    """
    Generates a workout plan based on user inputs using the OpenAI API.
    Expects a JSON payload with: goal, experience, equipment, focus.
    Returns a JSON response with the workout plan or an error message.
    """
    if not openai.api_key:
        app.logger.error("OpenAI API key is not configured.")
        return jsonify({"error": "AI service is not configured. Please contact support."}), 500

    try:
        data = request.get_json(silent=True) # Use silent=True to prevent raising 415/400 on content-type or parse error
        if not data:
            # This will now catch cases where content-type is wrong, or JSON is malformed
            return jsonify({"error": "Invalid request: No data provided or data is not valid JSON."}), 400

        goal = data.get("goal")
        experience = data.get("experience")
        equipment = data.get("equipment") # Expected to be a list, join to string
        focus = data.get("focus")

        if not all([goal, experience, equipment, focus]):
            return jsonify({"error": "Invalid request: Missing one or more required fields (goal, experience, equipment, focus)."}), 400

        equipment_str = ", ".join(equipment) if isinstance(equipment, list) else equipment

        prompt = (
            f"You are a fitness coach. Create a workout for an {experience} user "
            f"whose goal is to {goal}. The workout should focus on the {focus}. "
            f"The user only has {equipment_str}. The workout should include a warm-up, "
            f"4-5 main exercises with sets and reps in the 8-12 range, and a cool-down. "
            f"Format the output as markdown."
        )

        app.logger.info(f"Generated prompt: {prompt}")

        # OpenAI API call
        # Using chat completions with gpt-3.5-turbo
        chat_completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful fitness assistant that generates workout plans as markdown."},
                {"role": "user", "content": prompt}
            ]
        )

        workout_plan = chat_completion.choices[0].message.content.strip()
        app.logger.info(f"Received workout plan: {workout_plan[:200]}...") # Log a snippet
        return jsonify({"workout": workout_plan})

    except openai.AuthenticationError as e:
        app.logger.error(f"OpenAI Authentication Error: {e}")
        return jsonify({"error": "AI service authentication failed. Please check your API key configuration."}), 500
    except openai.RateLimitError as e:
        app.logger.error(f"OpenAI Rate Limit Error: {e}")
        return jsonify({"error": "AI service rate limit exceeded. Please try again later."}), 429
    except openai.OpenAIError as e: # Catch other OpenAI specific errors
        app.logger.error(f"OpenAI API Error: {e}")
        return jsonify({"error": f"An error occurred with the AI service: {e}"}), 500
    except Exception as e:
        app.logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred. Please try again."}), 500

if __name__ == "__main__":
    # Note: For production, use a proper WSGI server like Gunicorn
    app.run(debug=True)
