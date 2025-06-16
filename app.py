"""
Main Flask application for the MVP Workout Generator.
Handles user input for workout preferences and generates a workout plan
using the Google Gemini API.
"""
import os
import json
import random
from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
from dotenv import load_dotenv
from flask import Response

# Load environment variables from .env file for local development
load_dotenv()


GEMINI_MODELS = {
    "gemini-2.0-flash-001": {
        "id": "gemini-2.0-flash-001", "name": "Gemini 2.0 Flash",
        "inputPrice": 0.1, "outputPrice": 0.4
    },
    "gemini-1.5-flash-002": {
        "id": "gemini-1.5-flash-002", "name": "Gemini 1.5 Flash (128k+)",
        "inputPrice": 0.075, "outputPrice": 0.3 # Using first tier pricing
    },
    "gemini-2.5-pro-preview-06-05": {
        "id": "gemini-2.5-pro-preview-06-05", "name": "Gemini 2.5 Pro Preview (200k+)",
        "inputPrice": 1.25, "outputPrice": 10 # Using first tier pricing
    },
    "gemini-2.5-flash-preview-05-20": {
        "id": "gemini-2.5-flash-preview-05-20", "name": "Gemini 2.5 Flash Preview",
        "inputPrice": 0.15, "outputPrice": 0.6
    },
    # Adding a few more for variety, focusing on priced models
    "gemini-1.5-pro-latest": {
		"id": "gemini-1.5-pro-latest", "name": "Gemini 1.5 Pro",
		"inputPrice": 3.5, "outputPrice": 10.5
	},
    "gemini-1.5-flash-latest": {
		"id": "gemini-1.5-flash-latest", "name": "Gemini 1.5 Flash",
		"inputPrice": 0.35, "outputPrice": 0.70
	},
}
DEFAULT_MODEL_ID = "gemini-2.0-flash-001"

class SimpleGeminiProvider:
    def __init__(self, options):
        if not options.get("gemini_api_key"):
            raise ValueError("Gemini API key is required.")
        
        self.options = options
        genai.configure(api_key=options["gemini_api_key"])
        
        self.model_id = options.get("model_id", DEFAULT_MODEL_ID)
        self.model_info = GEMINI_MODELS.get(self.model_id)
        if not self.model_info:
            raise ValueError(f"Unsupported model ID: {self.model_id}")
            
        self.model = genai.GenerativeModel(
            self.model_id,
            generation_config={
                "max_output_tokens": options.get("model_max_tokens"),
                "temperature": options.get("model_temperature", 0.5),
            }
        )

    def create_message_stream(self, system_instruction, user_prompt):
        full_prompt = f"{system_instruction}\n\n{user_prompt}"
        
        try:
            # The Python SDK doesn't have the same usage metadata stream.
            # We will calculate tokens based on the final response.
            response_stream = self.model.generate_content(full_prompt, stream=True)

            for chunk in response_stream:
                if chunk.text:
                    yield json.dumps({"type": "text", "text": chunk.text}) + "\n"
            
            yield json.dumps({"type": "usage", "inputTokens": 0, "outputTokens": 0, "totalCost": 0}) + "\n"

        except Exception as e:
            app.logger.error(f"Gemini stream generation failed: {e}")
            yield json.dumps({"type": "error", "message": str(e)}) + "\n"


    def calculate_cost(self, input_tokens, output_tokens):
        input_cost = (input_tokens / 1_000_000) * self.model_info["inputPrice"]
        output_cost = (output_tokens / 1_000_000) * self.model_info["outputPrice"]
        return input_cost + output_cost

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

gemini_api_key = load_gemini_api_key()
gemini_provider = None

if gemini_api_key:
    try:
        gemini_provider = SimpleGeminiProvider({"gemini_api_key": gemini_api_key})
        app.logger.info("Gemini provider initialized successfully.")
    except Exception as e:
        app.logger.error(f"Failed to initialize Gemini provider: {e}")
else:
    app.logger.warning("Gemini API key not found. AI features will be unavailable.")

@app.route("/")
def index():
    """Renders the main workout configuration page."""
    return render_template("index.html")

@app.route("/save_settings", methods=["POST"])
def save_settings():
    global gemini_provider
    try:
        data = request.get_json()
        gemini_key = data.get("geminiApiKey")
        if not gemini_key:
            return jsonify({"error": "API key is required."}), 400

        config_data = {"GEMINI_API_KEY": gemini_key}

        with open(USER_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4)

        try:
            gemini_provider = SimpleGeminiProvider({"gemini_api_key": gemini_key})
            app.logger.info("Gemini provider re-initialized with new key.")
        except Exception as e:
            app.logger.error(f"Failed to initialize Gemini provider with new key: {e}")
            return jsonify({"error": "Invalid Gemini API Key."}), 400

        app.logger.info(f"Gemini API Key saved to {USER_CONFIG_FILE}.")
        return jsonify({"message": "API Key saved successfully!"}), 200
    except Exception as e:
        app.logger.error(f"Error saving settings: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred while saving settings."}), 500

@app.route("/generate_workout", methods=["POST"])
def generate_workout():
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
        else: # General Fitness
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
            for part_key in focus_anatomy_details:
                if isinstance(focus_anatomy_details[part_key], list):
                     sub_muscles.extend(focus_anatomy_details[part_key])
                elif isinstance(focus_anatomy_details[part_key], dict):
                    for specific_muscles in focus_anatomy_details[part_key].values():
                        sub_muscles.extend(specific_muscles)

            if len(sub_muscles) > 1:
                index1, index2 = random.sample(range(len(sub_muscles)), 2)
                emphasized_sub_muscle = sub_muscles[index1]
                de_emphasized_sub_muscle = sub_muscles[index2]
            elif len(sub_muscles) == 1:
                emphasized_sub_muscle = sub_muscles[0]

        system_instruction = "You are 'Atlas', an AI exercise physiologist and elite-level strength and conditioning coach. Your core competency is synthesizing client data into precise, safe, and hyper-effective training protocols. You have a deep, nuanced understanding of human anatomy, biomechanics, and training methodologies. Your tone is knowledgeable, encouraging, and direct. You will act as an expert system to generate a workout plan based on the following profile and a strict set of unbreakable rules."
        
        user_prompt = f"""
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
        
        if not gemini_provider:
            return jsonify({"error": "AI service is not configured. Please save your Gemini API key in User Settings."}), 500

        app.logger.info(f"Using Gemini provider to generate workout. Prompt length: {len(user_prompt)}")
        stream = gemini_provider.create_message_stream(system_instruction, user_prompt)
        return Response(stream, mimetype='application/json')

    except Exception as e:
        app.logger.error(f"An unexpected error occurred in generate_workout: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred. Please try again."}), 500

if __name__ == "__main__":
    app.run(debug=True)
