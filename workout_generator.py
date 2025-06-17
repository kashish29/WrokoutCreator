import random
import json
import logging
from ai_provider import SimpleGeminiProvider, GEMINI_MODELS, DEFAULT_MODEL_ID

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    with open("muscle_anatomy.json", "r", encoding="utf-8") as f:
        anatomy_data = json.load(f)
except FileNotFoundError:
    anatomy_data = {}
    logger.error("muscle_anatomy.json not found. Contextual nudge logic will be limited.")


def generate_workout_plan(user_data, settings, api_key):
    """
    Generates a workout plan using the AI provider based on user inputs and settings.
    """
    # --- User-specific Gemini Provider Initialization ---
    try:
        user_model_id = settings.get('ai_model_id', DEFAULT_MODEL_ID)
        provider_options = {
            "gemini_api_key": api_key,
            "model_id": user_model_id,
            "model_max_tokens": GEMINI_MODELS.get(user_model_id, {}).get("max_output_tokens", 8192),
            "model_temperature": 0.5
        }
        current_gemini_provider = SimpleGeminiProvider(provider_options)
        logger.info(f"Using model {user_model_id} for workout generation.")
    except Exception as e:
        logger.error(f"Failed to initialize user-specific Gemini provider: {e}")
        raise ValueError(f"Failed to initialize AI model: {e}")

    goal = user_data.get("goal") or settings.get("primary_goal")
    experience = user_data.get("experience")
    equipment = user_data.get("equipment")
    focus = user_data.get("focus")
    user_notes = user_data.get("userNotes")

    # --- Workout Duration Preference ---
    duration_preference = settings.get('workout_duration_preference', 'Any')
    duration_prompt_segment = ""
    if duration_preference and duration_preference != "Any":
        duration_prompt_segment = f"*   **Preferred Workout Duration:** Client prefers a {duration_preference} session."

    if not all([goal, experience, equipment, focus]):
        raise ValueError("Invalid request: Missing one or more required fields (goal, experience, equipment, focus).")

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

    system_instruction = "You are 'Atlas', an AI exercise physiologist... Your final output must be a single JSON object with two keys: 'workout_text' (containing the full markdown-formatted workout) and 'muscles_worked' (a JSON array of strings listing the primary muscle groups targeted, e.g., ['Chest', 'Triceps', 'Anterior Deltoids'])."
    
    user_prompt = f"""
---
### **PART 1: CLIENT PROFILE**
---
*   **Primary Goal:** {goal}
*   **Experience Level:** {experience}
*   **Available Equipment:** {equipment_str}
*   **Workout Focus for Today:** {focus}
{duration_prompt_segment}
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
    
    logger.info(f"Generating workout with prompt length: {len(user_prompt)}")
    
    # Non-streaming call for JSON response
    response = current_gemini_provider.model.generate_content(f"{system_instruction}\n\n{user_prompt}")
    
    try:
        # The response text should be a JSON string.
        response_json = json.loads(response.text)
        full_workout_text = response_json.get("workout_text", "")
        muscles_worked = response_json.get("muscles_worked", [])
        
        if not full_workout_text or not isinstance(muscles_worked, list):
            raise ValueError("Invalid JSON structure from AI.")

        return {
            "pillar": goal,
            "focus": focus,
            "muscles_worked": muscles_worked,
            "workout_text": full_workout_text
        }

    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Failed to parse JSON response from Gemini: {e}")
        logger.error(f"Raw response text: {response.text}")
        raise ValueError("AI returned an invalid response format. Please try again.")