"""
Main Flask application for the MVP Workout Generator.
Handles user input for workout preferences and generates a workout plan
using the OpenAI API.
"""
import os
import json
import random
from flask import Flask, request, jsonify, render_template
import openai
from dotenv import load_dotenv

# Load environment variables from .env file for local development
load_dotenv()

app = Flask(__name__)

# Load muscle anatomy data
try:
    with open("muscle_anatomy.json", "r", encoding="utf-8") as f:
        anatomy_data = json.load(f)
except FileNotFoundError:
    anatomy_data = {}
    app.logger.error("muscle_anatomy.json not found. Contextual nudge logic will be limited.")

# API Key Configuration
USER_CONFIG_FILE = "user_config.json"

def load_api_key():
    try:
        with open(USER_CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            return config.get("OPENAI_API_KEY")
    except FileNotFoundError:
        return os.getenv("OPENAI_API_KEY")
    except json.JSONDecodeError:
        app.logger.error(f"Error decoding {USER_CONFIG_FILE}. Using environment variable for API key.")
        return os.getenv("OPENAI_API_KEY")

openai.api_key = load_api_key()
if not openai.api_key:
    app.logger.warning("OpenAI API key is not configured (checked user_config.json and environment variable). AI features will not work.")

@app.route("/")
def index():
    """Renders the main workout configuration page."""
    return render_template("index.html")

@app.route("/save_settings", methods=["POST"])
def save_settings():
    try:
        data = request.get_json()
        api_key = data.get("apiKey")
        if not api_key:
            return jsonify({"error": "API key is required."}), 400

        config_data = {}
        if os.path.exists(USER_CONFIG_FILE):
            try:
                with open(USER_CONFIG_FILE, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
            except json.JSONDecodeError:
                app.logger.warning(f"Could not decode {USER_CONFIG_FILE}, it will be overwritten.")

        config_data["OPENAI_API_KEY"] = api_key

        with open(USER_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4)

        openai.api_key = api_key
        app.logger.info(f"OpenAI API Key updated from UI and saved to {USER_CONFIG_FILE}.")
        return jsonify({"message": "API Key saved successfully!"}), 200
    except Exception as e:
        app.logger.error(f"Error saving settings: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred while saving settings."}), 500

@app.route("/generate_workout", methods=["POST"])
def generate_workout():
    if not openai.api_key:
        app.logger.error("OpenAI API key is not configured.")
        return jsonify({"error": "AI service is not configured. Please contact support or save your API key in User Settings."}), 500

    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "Invalid request: No data provided or data is not valid JSON."}), 400

        goal = data.get("goal")
        experience = data.get("experience")
        equipment = data.get("equipment")
        focus = data.get("focus")
        user_notes = data.get("userNotes")

        if not all([goal, experience, equipment, focus]):
            return jsonify({"error": "Invalid request: Missing one or more required fields (goal, experience, equipment, focus)."}), 400

        equipment_str = ", ".join(equipment) if isinstance(equipment, list) else equipment

        rules = {}
        if goal == "Build Muscle":
            rules = {
                "Methodology": "Agonist/Antagonist Supersets",
                "Methodology_Description": "Pair exercises for opposing muscle groups (e.g., chest and back) to maximize efficiency and muscle pump.",
                "Intensity_Protocol": "Aim for 8-12 reps per set, reaching a Rate of Perceived Exertion (RPE) of 8-9 (1-2 reps shy of failure).",
                "Rest_Protocol": "15-30 seconds between paired exercises; 90-120 seconds after each superset is complete."
            }
        elif goal == "Get Stronger":
            rules = {
                "Methodology": "Traditional Straight Sets with Top Set/Back-off Sets",
                "Methodology_Description": "Focus on one primary heavy lift, followed by volume work at a slightly lower intensity.",
                "Intensity_Protocol": "Main lift should be in the 3-5 rep range (RPE 9). Back-off sets in the 6-8 rep range (RPE 7-8).",
                "Rest_Protocol": "3-5 minutes after heavy sets; 2-3 minutes for back-off sets."
            }
        else:
            rules = {
                "Methodology": "Traditional Circuits",
                "Methodology_Description": "Move from one exercise to the next with minimal rest to improve general conditioning and muscular endurance.",
                "Intensity_Protocol": "Aim for 15-20 reps per set, focusing on maintaining good form under fatigue (RPE 7-8).",
                "Rest_Protocol": "30-45 seconds between exercises; 60-90 seconds after each full circuit."
            }

        emphasized_sub_muscle = f"the main muscles of the {focus}"
        de_emphasized_sub_muscle = "other muscle groups"

        focus_anatomy_details = anatomy_data.get(focus)
        if focus_anatomy_details:
            sub_muscles = []
            for part_key in focus_anatomy_details: # Iterate through keys like "Chest", "Back" under "Upper Body"
                if isinstance(focus_anatomy_details[part_key], list):
                     sub_muscles.extend(focus_anatomy_details[part_key])
                elif isinstance(focus_anatomy_details[part_key], dict): # Should not happen with current JSON, but for robustness
                    for specific_muscles in focus_anatomy_details[part_key].values():
                        sub_muscles.extend(specific_muscles)


            if len(sub_muscles) > 1:
                index1 = random.randrange(len(sub_muscles))
                index2 = random.randrange(len(sub_muscles))
                while index1 == index2:
                    index2 = random.randrange(len(sub_muscles))
                emphasized_sub_muscle = sub_muscles[index1]
                de_emphasized_sub_muscle = sub_muscles[index2]
            elif len(sub_muscles) == 1:
                emphasized_sub_muscle = sub_muscles[0]

        final_prompt = f"""
You are 'Atlas', an AI exercise physiologist and elite-level strength and conditioning coach. Your core competency is synthesizing client data into precise, safe, and hyper-effective training protocols. You have a deep, nuanced understanding of human anatomy, biomechanics, and training methodologies. Your tone is knowledgeable, encouraging, and direct. You will act as an expert system to generate a workout plan based on the following profile and a strict set of unbreakable rules.

---
### **PART 1: CLIENT PROFILE**
---
*   **Primary Goal:** {goal}
*   **Experience Level:** {experience}
*   **Available Equipment:** {equipment_str}
*   **Workout Focus for Today:** {focus}
*   **Client's Self-Reported Notes (Consider carefully):** {user_notes or "None provided."}

---
### **PART 2: EXPERT SYSTEM RULES (MANDATORY & UNBREAKABLE)**
---
*   **Governing Training Methodology:** You MUST structure the main workout using the **"{rules['Methodology']}"** principle. {rules['Methodology_Description']}
*   **Intensity and Rep Range Protocol:** All primary working sets must adhere to this protocol: {rules['Intensity_Protocol']}
*   **Rest Period Protocol:** All rest periods must be prescribed exactly as follows: {rules['Rest_Protocol']}
*   **Exercise Selection Constraints:**
    *   You MUST only select exercises that can be performed with the Available Equipment.
    *   You MUST NOT select exercises known to have a highSpinalLoad unless it is a core part of the movement (e.g., Deadlift, Barbell Squat) and appropriate for the client's level.
    *   You MUST prioritize compound movements over isolation movements for the main portion of the workout.
---
### **PART 3: SESSION STRUCTURE DIRECTIVE**
---
**Phase 1: Warm-up (Preparation & Activation)**
*   Begin with 5-7 minutes of light, general cardiovascular activity (e.g., jogging in place, jumping jacks).
*   Following cardio, you MUST select 2-3 specific Activation or Mobility exercises. These should be low-intensity and directly prepare the primary joints and muscles for today's Workout Focus. For example, for an Upper Body day, this would include exercises like Band Pull-Aparts or Scapular Push-ups. Do not select taxing compound lifts for this phase.

**Phase 2: Main Workout (Stimulus)**
*   Design the main block of the workout using 4-6 primary exercises.
*   You MUST organize these exercises according to the Governing Training Methodology defined in PART 2.
*   **CRITICAL EMPHASIS (The Nudge):** Based on recent training patterns, the client needs specific focus. You MUST choose exercises and variations that place a primary stimulus on the **{emphasized_sub_muscle}** while giving less direct volume to the **{de_emphasized_sub_muscle}**. This is the most important variable for today's session.

**Phase 3: Cool-down (Recovery)**
*   Conclude the session with a brief period of low-intensity movement (e.g., 3-5 minute walk).
*   Follow this with 2-3 static stretches, holding each for 30-45 seconds. The stretches must target the primary muscles worked during the session.
---
### **PART 4: OUTPUT FORMATTING**
---
*   Generate the entire workout plan using clean and clear markdown.
*   Use headings (##) for each phase (Warm-up, Main Workout, Cool-down).
*   Use bullet points (*) or numbered lists for exercises.
*   Clearly label any supersets or circuits (e.g., "Superset A:").
*   For each exercise, provide the sets, reps, and the exact rest period as defined in your rules.
*   For each exercise, include a single, impactful "Coach's Cue" focusing on the most critical aspect of its form or execution.
"""

        app.logger.info(f"Assembled final prompt. Length: {len(final_prompt)}")

        chat_completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are 'Atlas', an AI exercise physiologist and elite-level strength and conditioning coach."},
                {"role": "user", "content": final_prompt}
            ]
        )

        workout_plan = chat_completion.choices[0].message.content.strip()
        app.logger.info(f"Received workout plan snippet: {workout_plan[:200]}...")
        return jsonify({"workout": workout_plan})

    except openai.AuthenticationError as e:
        app.logger.error(f"OpenAI Authentication Error: {e}")
        key_source = "user_config.json" if os.path.exists(USER_CONFIG_FILE) else "environment variable"
        app.logger.error(f"Attempted to use API key from {key_source}.")
        return jsonify({"error": "AI service authentication failed. Please check your API key configuration in User Settings or environment variables."}), 500
    except openai.RateLimitError as e:
        app.logger.error(f"OpenAI Rate Limit Error: {e}")
        return jsonify({"error": "AI service rate limit exceeded. Please try again later."}), 429
    except openai.OpenAIError as e:
        app.logger.error(f"OpenAI API Error: {e}")
        return jsonify({"error": f"An error occurred with the AI service: {str(e)}"}), 500
    except Exception as e:
        app.logger.error(f"An unexpected error occurred in generate_workout: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred. Please try again."}), 500

if __name__ == "__main__":
    app.run(debug=True)
