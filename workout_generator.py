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

    # Extract new pillar-based inputs
    workout_pillar = user_data.get("workout_pillar")
    if not workout_pillar:
        raise ValueError("Invalid request: 'workout_pillar' is a required field.")

    strength_style = user_data.get("strength_style") # Previously 'goal' from workout form
    experience = user_data.get("experience")
    equipment = user_data.get("equipment")
    focus = user_data.get("focus") # e.g., Upper Body, Lower Body, Full Body, Core
    user_notes = user_data.get("userNotes")
    # New context fields
    todays_planned_pillar = user_data.get('todays_planned_pillar', 'Not available.')
    recent_history = user_data.get('recent_history', 'Not available.')

    # --- Workout Duration Preference ---
    duration_preference = settings.get('workout_duration_preference', 'Any')
    duration_prompt_segment = ""
    if duration_preference and duration_preference != "Any":
        duration_prompt_segment = f"*   **Preferred Workout Duration:** Client prefers a {duration_preference} session."

    if not all([experience, equipment]): # Focus might be optional for some pillars
        raise ValueError("Invalid request: Missing one or more required fields (experience, equipment).")

    equipment_str = ", ".join(equipment) if isinstance(equipment, list) else equipment

    system_instruction = "You are 'Atlas', an AI exercise physiologist... Your final output must be a single JSON object with two keys: 'workout_text' (containing the full markdown-formatted workout) and 'muscles_worked' (a JSON array of strings listing the primary muscle groups targeted, e.g., ['Chest', 'Triceps', 'Anterior Deltoids'])."

    user_prompt_parts = []

    # --- PART 1: CLIENT PROFILE ---
    user_prompt_parts.append("### **PART 1: CLIENT PROFILE**")
    user_prompt_parts.append("---")
    user_prompt_parts.append(f"*   **Selected Workout Pillar:** {workout_pillar}")
    if workout_pillar == "Strength" and strength_style:
        user_prompt_parts.append(f"*   **Strength Style:** {strength_style}")
    user_prompt_parts.append(f"*   **Experience Level:** {experience}")
    user_prompt_parts.append(f"*   **Available Equipment:** {equipment_str}")
    if focus: # Focus is most relevant for Strength and Stability/Mobility
         user_prompt_parts.append(f"*   **Workout Focus for Today:** {focus}")
    if duration_prompt_segment:
        user_prompt_parts.append(duration_prompt_segment)
    user_prompt_parts.append(f"*   **Client's Self-Reported Notes (Consider carefully):** {user_notes or 'None provided.'}")

    # PART 1B: TRAINING CONTEXT
    user_prompt_parts.append("\n---")
    user_prompt_parts.append("### **PART 1B: TRAINING CONTEXT**")
    user_prompt_parts.append("---")
    user_prompt_parts.append(todays_planned_pillar)
    user_prompt_parts.append(recent_history)
    user_prompt_parts.append("\n**Contextual Considerations for Today's Workout:**")
    user_prompt_parts.append("*   **Alignment:** Ensure today's generated workout aligns with the 'Selected Workout Pillar' from Part 1, taking into account the 'Today's Planned Pillar' (if any) and recent history.")
    user_prompt_parts.append("*   **Avoid Overlap (Strength):** If generating a 'Strength' workout, critically review 'Recent Training History'. If a similar muscle focus (e.g., Upper Body) was trained recently with high intensity, aim to vary exercises, emphasize different muscle sub-groups (using the Nudge if applicable), or slightly reduce volume/intensity to promote recovery, unless the client's notes explicitly request high frequency for that group.")
    user_prompt_parts.append("*   **Intensity Management:** If recent history shows multiple consecutive high-intensity days (Strength or HIIT), and today is also planned as high-intensity, ensure the warm-up is thorough and consider including slightly more recovery or mobility work in the cool-down.")
    user_prompt_parts.append("*   **Concurrent Training Note:** While you are generating for a single pillar, be aware that if a client were to combine Strength and Cardio/HIIT in the same session, Strength training should generally precede Cardio/HIIT. This is for your information as an expert.")
    user_prompt_parts.append("\n---")

    # --- PART 2: EXPERT SYSTEM RULES (MANDATORY & UNBREAKABLE) ---
    user_prompt_parts.append("### **PART 2: EXPERT SYSTEM RULES (MANDATORY & UNBREAKABLE)**")
    user_prompt_parts.append("---")
    user_prompt_parts.append("*   **Prioritize Safety:** In all exercise selections and workout structures, prioritize client safety and proper biomechanics according to their experience level.")
    user_prompt_parts.append("*   **General Spinal Safety:** Avoid excessive spinal loading. For any exercises involving significant axial load (e.g., squats, deadlifts, overhead presses), ensure they are appropriate for the client's experience level and pillar focus. Do not program multiple high spinal load exercises consecutively without adequate recovery or deloading exercises in between for Strength workouts.")
    # Add a newline after global rules before pillar-specific rules start
    user_prompt_parts.append("")

    rules = {} # To be populated based on pillar

    if workout_pillar == "Strength":
        chosen_methodology_name = ""
        methodology_description_for_ai = ""
        intensity_protocol_for_ai = ""
        rest_protocol_for_ai = ""
        structure_directive_for_ai = ""

        if strength_style == "Build Muscle":
            if experience == "Advanced" and random.choice([True, False]): # 50% chance for pre-exhaustion for advanced
                chosen_methodology_name = "Pre-exhaustion Sets"
                methodology_description_for_ai = "For a target muscle group, perform an isolation exercise (10-15 reps, RPE 7-8) immediately followed by a compound exercise (6-10 reps, RPE 8-9) that also involves that muscle. Minimal rest (10-20s) between the pre-exhaust and compound exercise."
                intensity_protocol_for_ai = "Isolation: 10-15 reps (RPE 7-8); Compound: 6-10 reps (RPE 8-9)."
                rest_protocol_for_ai = "Minimal rest (10-20s) between pre-exhaust P1 and compound P2. Rest 90-120 seconds after completing the pair (P2)."
                structure_directive_for_ai = "Label pairs as 'Pre-exhaustion Pair: P1: [Isolation Exercise], P2: [Compound Exercise]'. Ensure P1 truly isolates a muscle group effectively worked in P2."
            else: # Default to Antagonist/Agonist Supersets
                chosen_methodology_name = "Antagonist/Agonist Supersets"
                methodology_description_for_ai = "Pair exercises for opposing muscle groups (e.g., chest and back, or biceps and triceps) to maximize efficiency and muscle pump. Complete both exercises back-to-back."
                intensity_protocol_for_ai = "Aim for 8-12 reps per set for each exercise, reaching an RPE of 8-9 (1-2 reps shy of failure)."
                rest_protocol_for_ai = "Minimal rest (15-30s) between A1 and A2 exercises within the superset. Rest 90-120 seconds after completing the pair (A2)."
                structure_directive_for_ai = "Clearly label these pairs (e.g., A1: Exercise, A2: Exercise). Ensure A1 and A2 work opposing muscle groups."

        elif strength_style == "Get Stronger":
            if experience == "Advanced" and random.choice([True, False]): # 50% chance for contrast training for advanced
                chosen_methodology_name = "Contrast Training"
                methodology_description_for_ai = "Perform a heavy compound lift (3-5 reps, RPE 9) followed by a short rest, then an explosive power exercise (5-8 reps, RPE 7-8) targeting similar muscle groups."
                intensity_protocol_for_ai = "Heavy Lift (C1): 3-5 reps (RPE 9); Explosive Exercise (C2): 5-8 reps (RPE 7-8, focus on speed)."
                rest_protocol_for_ai = "Rest 30-60 seconds between C1 and C2. Rest 2-3 minutes after completing the pair (C2)."
                structure_directive_for_ai = "Label pairs as 'Contrast Pair: C1: [Heavy Exercise], C2: [Explosive Exercise]'. C2 should be biomechanically similar to C1 or target the same prime movers explosively."
            else: # Default to Top Set/Back-off Sets
                chosen_methodology_name = "Top Set / Back-off Sets"
                methodology_description_for_ai = "Focus on one primary heavy lift for a 'top set', then reduce the weight for 'back-off sets' to accumulate more volume."
                intensity_protocol_for_ai = "Top Set: 1 set of 3-5 reps (RPE 9). Back-off Sets: 2-3 sets of 6-8 reps (RPE 7-8)."
                rest_protocol_for_ai = "Rest 3-5 minutes after the top set. Rest 2-3 minutes after back-off sets. Other accessory exercises follow standard rest (60-90s)."
                structure_directive_for_ai = "Clearly distinguish the Top Set from Back-off Sets for the main lift(s). Subsequent exercises can be straight sets."

        else: # General Fitness (Strength)
            chosen_methodology_name = "Full-Body Circuit Training"
            methodology_description_for_ai = "Perform a series of 3-5 exercises targeting different muscle groups with minimal rest in between. Repeat the circuit 2-3 times."
            intensity_protocol_for_ai = "Aim for 10-15 reps per exercise (RPE 7-8)."
            rest_protocol_for_ai = "15-30 seconds of rest/transition between exercises in the circuit. Rest 90-120 seconds between full circuits."
            structure_directive_for_ai = "Clearly list the exercises in the circuit. Specify number of rounds for the circuit."

        rules = { # This 'rules' dict is now mostly for internal use if needed, AI gets direct strings
            "Methodology": chosen_methodology_name,
            "Methodology_Description": methodology_description_for_ai,
            "Intensity_Protocol": intensity_protocol_for_ai,
            "Rest_Protocol": rest_protocol_for_ai,
            "Structure_Directive": structure_directive_for_ai
        }

        user_prompt_parts.append(f"*   **Governing Training Methodology:** {chosen_methodology_name}. {methodology_description_for_ai}")
        user_prompt_parts.append(f"*   **Intensity and Rep Range Protocol:** {intensity_protocol_for_ai}")
        user_prompt_parts.append(f"*   **Rest Period Protocol:** {rest_protocol_for_ai}")
        user_prompt_parts.append(f"*   **Structural Guidance:** {structure_directive_for_ai}")
        user_prompt_parts.append("*   **Brief Explanation:** If the chosen methodology is complex (e.g., Contrast Training, Pre-exhaustion), include a brief one-sentence explanation of its purpose in the introductory part of the workout text.")

        # Strength Pillar Specific Safety Constraints
        user_prompt_parts.append("*   **Core Pre-Fatigue Avoidance:** Do not program intense, direct core exercises (e.g., weighted planks, leg raises, dragon flags) immediately *before* heavy compound lifts that require significant core stabilization (such as Squats, Deadlifts, Overhead Presses, or heavy Barbell Rows). Core accessory work should typically come after main lifts or on separate days.")

        # Push/Pull Balance - apply if not a specific pairing methodology like Antagonist Supersets or Pre-exhaustion for a single group
        if chosen_methodology_name not in ["Antagonist/Agonist Supersets", "Pre-exhaustion Sets"]:
            user_prompt_parts.append("*   **Push/Pull Balance (General Strength):** For general strength routines focusing on 'Upper Body' or 'Full Body', strive for a balance between pushing movements (e.g., bench press, overhead press, push-ups) and pulling movements (e.g., rows, pull-ups, lat pulldowns) within the session. Avoid sequencing multiple primary pushing exercises back-to-back without an intervening pulling exercise, and vice-versa, to maintain joint balance.")

        user_prompt_parts.append("*   **Exercise Selection Constraints (Continued):**") # Keep existing constraints
        user_prompt_parts.append("    *   You MUST only select exercises that can be performed with the Available Equipment.")
        # General Spinal Safety rule above covers the highSpinalLoad point more broadly now.
        # user_prompt_parts.append("    *   You MUST NOT select exercises known to have a highSpinalLoad unless it is a core part of the movement (e.g., Deadlift, Barbell Squat) and appropriate for the client's level.")
        user_prompt_parts.append("    *   You MUST prioritize compound movements over isolation movements for the main portion of the workout.")

        # Bodyweight specific enhancements for Strength
        is_bodyweight_only = equipment_str == "Bodyweight only" or (isinstance(equipment, list) and equipment == ["Bodyweight only"])
        if is_bodyweight_only:
            user_prompt_parts.append("*   **Bodyweight Training Principles:** Since this is a bodyweight-only session, you MUST incorporate principles to drive adaptation. This includes:")
            user_prompt_parts.append("    *   **Mechanical Difficulty:** Prescribe specific exercise progressions or regressions to adjust difficulty (e.g., incline push-ups to regular push-ups to decline push-ups; squat variations like shrimp squats or pistol squats for advanced). Clearly state the progression if offering options.")
            user_prompt_parts.append("    *   **Tempo Variations:** For at least 1-2 exercises, suggest specific tempo variations (e.g., slow eccentrics like '3-1-1-0 count: 3s down, 1s pause, 1s up, 0s pause at top') to increase time under tension. Explain the tempo briefly.")
            user_prompt_parts.append("    *   **Reps to Failure/AMRAP:** For strength/hypertrophy goals with bodyweight, consider prescribing some sets as 'Reps to Failure' (RTF) or 'As Many Reps As Possible' (AMRAP) with good form, especially for the final set of an exercise. Clearly indicate this.")

    elif workout_pillar == "Zone2 Cardio":
        user_prompt_parts.append("*   **Methodology:** Sustained, low-to-moderate intensity cardiovascular exercise.")
        user_prompt_parts.append("*   **Intensity:** Target Heart Rate Zone 2 (e.g., 60-70% Max Heart Rate) or RPE 3-4 (light to moderate). Maintain this intensity consistently.")

        cardio_machine_options = ["Treadmill", "Stationary Bike", "Rower", "Elliptical", "Stair Climber", "Assault Bike"]
        available_cardio_machines = [e for e in equipment if e in cardio_machine_options]

        if available_cardio_machines:
            machines_str = ", ".join(available_cardio_machines)
            user_prompt_parts.append(f"*   **Cardio Equipment Priority:** The client has access to: {machines_str}. You MUST prioritize using one or more of these machines as the primary tools for this Zone2 Cardio session. Clearly state which machine(s) the workout is designed for.")
            user_prompt_parts.append(f"*   **Machine-Specific Parameters:** For the selected machine(s), prescribe specific settings, intensities, or targets where applicable (e.g., for Treadmill: suggest speed ranges, incline settings; for Bike/Rower: suggest resistance levels, RPM, or pace targets; for Elliptical: resistance, stride rate). These should align with Zone 2 RPE.")
            user_prompt_parts.append("*   **Bodyweight Exercise Use:** If bodyweight exercises are included (e.g., for warm-up), they should be secondary to machine use for the main work phase.")
        else:
            user_prompt_parts.append("*   **Exercise Selection:** Choose 1-2 suitable bodyweight cardio options for steady-state work (e.g., brisk walking, jogging, light calisthenics circuit if sustainable in Zone 2).")

        user_prompt_parts.append("*   **Output - Muscles Worked:** For this pillar, 'muscles_worked' should primarily be 'Cardiovascular System'. Secondary general groups like 'Lower Body (general)' or 'Full Body (general)' can be listed if applicable to the chosen exercise(s).")
        # Duration is handled in PART 3

    elif workout_pillar == "HIIT":
        hiit_protocols = [
            {
                "name": "Norwegian 4x4 (Classic VO2 Max)",
                "description": "4 repetitions of: 4 minutes at high intensity (RPE 9-10, or ~90-95% HRmax), then 3 minutes of active recovery (RPE 5-6, or ~70% HRmax).",
                "work_intensity": "RPE 9-10 (or ~90-95% HRmax)",
                "rest_intensity": "Active Recovery (RPE 5-6, or ~70% HRmax)",
                "structure_detail": "Perform 4 sets of (4 minutes work / 3 minutes active recovery).",
                "total_high_intensity_time_minutes": 16,
                "notes": "Excellent for VO2 max development. Requires ability to sustain intensity for 4-minute blocks.",
                "difficulty": "advanced"
            },
            {
                "name": "Billat 30/30s (vVO2 Max Focus)",
                "description": "Repeated intervals of 30 seconds at or near vVO2max pace (RPE 9-10), followed by 30 seconds of active recovery.",
                "work_intensity": "RPE 9-10 (target vVO2max pace/effort)",
                "rest_intensity": "Active Recovery (e.g., light jog/cycle)",
                "structure_detail": "Perform 10-20 repetitions of (30 seconds work / 30 seconds active recovery). Adjust repetitions based on client experience and total desired HIIT phase duration.",
                "total_high_intensity_time_minutes": "5-10 (depending on reps)",
                "notes": "Targets speed at VO2 max. Good for experienced individuals.",
                "difficulty": "intermediate"
            },
            {
                "name": "Micro-intervals (e.g., 40s/20s)",
                "description": "Short, very high intensity bursts with brief recovery periods, often performed in blocks.",
                "work_intensity": "RPE 9-10",
                "rest_intensity": "Passive or very light active recovery",
                "structure_detail": "Example: 2 blocks of (8 repetitions of 40 seconds work / 20 seconds rest). Rest 2-3 minutes between blocks.",
                "total_high_intensity_time_minutes": "Approx 5-6 minutes per block",
                "notes": "Can be very demanding. Good for building anaerobic capacity and tolerating high intensity.",
                "difficulty": "intermediate"
            },
            {
                "name": "Generic HIIT (Flexible Ratio)",
                "description": "A general HIIT structure with a work-to-rest ratio like 1:1 or 2:1. This protocol is adaptable for beginners.",
                "work_intensity": "RPE 8-9 (can be RPE 7-8 for beginners)",
                "rest_intensity": "Active or passive recovery",
                "structure_detail": "Example: 8-12 rounds of (30-60 seconds work / 30-90 seconds rest). Adjust total rounds and work/rest ratio for desired HIIT phase duration and experience level.",
                "total_high_intensity_time_minutes": "Varies with rounds and ratios",
                "notes": "Good for general conditioning and can be adapted easily for all levels.",
                "difficulty": "beginner"
            }
        ]

        if experience == "Beginner":
            beginner_protocols = [p for p in hiit_protocols if p.get('difficulty') == 'beginner']
            chosen_protocol = random.choice(beginner_protocols) if beginner_protocols else random.choice([p for p in hiit_protocols if p['name'].startswith("Generic HIIT")]) # Fallback to generic
        elif experience == "Intermediate":
            intermediate_protocols = [p for p in hiit_protocols if p.get('difficulty') in ['beginner', 'intermediate']]
            chosen_protocol = random.choice(intermediate_protocols) if intermediate_protocols else random.choice(hiit_protocols)
        else: # Advanced
            chosen_protocol = random.choice(hiit_protocols) # Can choose any, or prioritize advanced ones

        logger.info(f"Client Experience: {experience}, Chosen HIIT Protocol: {chosen_protocol['name']}")

        user_prompt_parts.append(f"*   **Governing HIIT Protocol:** You MUST use the **{chosen_protocol['name']}** protocol.")
        if chosen_protocol['name'].startswith("Generic HIIT") and experience == "Beginner":
            user_prompt_parts.append("*   **Beginner Adaptation Note:** Since the client is a beginner and 'Generic HIIT' is selected, prioritize shorter work intervals (e.g., 20-30 seconds), longer relative rest periods (e.g., 1:2 or 1:3 work:rest ratio like 30s work / 60-90s rest), and a lower total number of intervals (e.g., 6-8 rounds) to ensure safety and a positive experience. Total HIIT work phase should be kept short (e.g., 8-10 minutes).")
        user_prompt_parts.append(f"*   **Protocol Description & Structure:** {chosen_protocol['description']}")
        user_prompt_parts.append(f"*   **Work Interval Intensity:** {chosen_protocol['work_intensity']}.")
        user_prompt_parts.append(f"*   **Rest Interval Details:** {chosen_protocol['rest_intensity']}.")
        user_prompt_parts.append(f"*   **Detailed Session Structure (Main Workout Phase):** {chosen_protocol['structure_detail']}")

        cardio_machine_options = ["Treadmill", "Stationary Bike", "Rower", "Elliptical", "Stair Climber", "Assault Bike"]
        available_cardio_machines = [e for e in equipment if e in cardio_machine_options]

        if available_cardio_machines:
            machines_str = ", ".join(available_cardio_machines)
            user_prompt_parts.append(f"*   **Cardio Equipment Priority for HIIT:** The client has access to: {machines_str}. You should prioritize one of these for the HIIT intervals if suitable for the chosen protocol (e.g., bike sprints for Billat 30/30s). Clearly state the machine.")
            user_prompt_parts.append(f"*   **Machine-Specific Parameters for HIIT:** If a machine is used, suggest settings appropriate for maximal effort intervals (e.g., high resistance on a bike, fast speed on a treadmill).")
            user_prompt_parts.append("*   **Bodyweight Exercise Use for HIIT:** Bodyweight exercises (burpees, high knees, jumping jacks, mountain climbers) are also excellent for HIIT and can be primary choices or mixed with machine work if the protocol allows (e.g., machine for work interval, bodyweight for active recovery or vice-versa).")
        else:
            user_prompt_parts.append("*   **Exercise Selection (Bodyweight HIIT):** Focus on bodyweight exercises suitable for high-intensity bursts (e.g., burpees, high knees, jumping jacks, mountain climbers, plyometric lunges).")

        user_prompt_parts.append("*   **Output - Muscles Worked:** For this pillar, 'muscles_worked' should include 'Cardiovascular System' and typically 'Full Body (general)' or specific major muscle groups if a single exercise modality dominates (e.g., 'Legs' for bike sprints).")
        user_prompt_parts.append("*   **Important:** Clearly state the chosen protocol name and its parameters in the generated workout text for the client.")

    elif workout_pillar == "Stability/Mobility":
        user_prompt_parts.append("*   **Methodology:** Focus on enhancing core stabilization, balance, joint mobility, and flexibility through controlled movements.")
        user_prompt_parts.append("*   **Intensity:** Controlled movements, emphasizing proper form, muscle activation, and mindful execution. Target RPE 4-7.")

        is_bodyweight_only = equipment_str == "Bodyweight only" or (isinstance(equipment, list) and equipment == ["Bodyweight only"])
        exercise_selection_parts = []
        exercise_selection_parts.append(f"*   **Exercise Selection:** Primarily bodyweight exercises. Resistance bands can be incorporated if available. Exercises should be chosen based on the client's focus for the day ('{focus if focus else 'Full Body'}'). Examples include: ")
        exercise_selection_parts.append("    *   Core: Planks (various), bird-dogs, dead bugs, glute bridges.")
        exercise_selection_parts.append("    *   Mobility: Cat-cow, thoracic spine rotations, hip circles, ankle mobility drills.")
        exercise_selection_parts.append("    *   Balance: Single-leg stands, tandem stance exercises, controlled lunges.")
        exercise_selection_parts.append("    *   Flexibility: Dynamic stretches like leg swings during warm-up/main work, static stretches during cool-down.")
        user_prompt_parts.extend(exercise_selection_parts)

        if is_bodyweight_only:
            user_prompt_parts.append("*   **Bodyweight Training Principles (Stability/Mobility):** Since this is a bodyweight-only session, enhance adaptation by:")
            user_prompt_parts.append("    *   **Mechanical Difficulty:** Suggest progressions for exercises to increase challenge where appropriate (e.g., plank variations, single-leg deadlift variations for balance).")
            user_prompt_parts.append("    *   **Tempo and Holds:** For some exercises, especially core or balance, emphasize controlled tempos or isometric holds (e.g., 'hold plank for 30-60s', 'perform bird-dog with a 2s pause at full extension').")

        user_prompt_parts.append(f"*   **Output - Muscles Worked:** For this pillar, 'muscles_worked' should reflect the targeted areas, e.g., ['Core', 'Hips', 'Shoulders'] or more specific stabilizers if applicable. If focus is '{focus if focus else 'Full Body'}', list the primary areas addressed.")

    else:
        raise ValueError(f"Unknown workout_pillar: {workout_pillar}")
    
    user_prompt_parts.append("\n---")

    # --- PART 3: SESSION STRUCTURE DIRECTIVE ---
    user_prompt_parts.append("### **PART 3: SESSION STRUCTURE DIRECTIVE**")
    user_prompt_parts.append("---")
    # TODO: Pillar-specific session structure
    if workout_pillar == "Strength":
        emphasized_sub_muscle = f"the main muscles of the {focus}" if focus else "the primary target muscles"
        de_emphasized_sub_muscle = "other muscle groups"
        if focus and anatomy_data.get(focus): # Re-integrate contextual nudge for strength
            focus_anatomy_details = anatomy_data.get(focus)
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

        user_prompt_parts.append("**Phase 1: Warm-up (Preparation & Activation)**")
        user_prompt_parts.append("*   Begin with 5-7 minutes of light, general cardiovascular activity (e.g., jogging in place, jumping jacks).")
        user_prompt_parts.append(f"*   Following cardio, you MUST select 2-3 specific Activation or Mobility exercises. These should be low-intensity and directly prepare the primary joints and muscles for today's Workout Focus ({focus}). For example, for an Upper Body day, this would include exercises like Band Pull-Aparts or Scapular Push-ups. Do not select taxing compound lifts for this phase.")
        user_prompt_parts.append("\n**Phase 2: Main Workout (Stimulus)**")
        user_prompt_parts.append("*   Design the main block of the workout using 4-6 primary exercises.")
        user_prompt_parts.append(f"*   You MUST organize these exercises according to the **{chosen_methodology_name}** methodology and its specific **Structural Guidance** provided above.")
        user_prompt_parts.append(f"*   **CRITICAL EMPHASIS (The Nudge):** Based on recent training patterns, the client needs specific focus. You MUST choose exercises and variations that place a primary stimulus on the **{emphasized_sub_muscle}** while giving less direct volume to the **{de_emphasized_sub_muscle}**. This is the most important variable for today's session. This nudge should be skillfully integrated within the chosen training methodology.")
        user_prompt_parts.append("\n**Phase 3: Cool-down (Recovery)**")
        user_prompt_parts.append("*   Conclude the session with a brief period of low-intensity movement (e.g., 3-5 minute walk).")
        user_prompt_parts.append("*   Follow this with 2-3 static stretches, holding each for 30-45 seconds. The stretches must target the primary muscles worked during the session.")

    elif workout_pillar == "Zone2 Cardio":
        user_prompt_parts.append("**Phase 1: Warm-up (Preparation & Activation)**")
        user_prompt_parts.append("*   Perform 5-7 minutes of light dynamic movements. Examples: leg swings (forward and lateral), arm circles, torso twists, walking lunges. Focus on preparing for continuous movement.")
        user_prompt_parts.append("\n**Phase 2: Main Workout (Zone 2 Activity)**")
        duration_text = "a default of 45 minutes"
        if duration_preference == "Short":
            duration_text = "approximately 30 minutes"
        elif duration_preference == "Medium":
            duration_text = "approximately 45-60 minutes"
        elif duration_preference == "Long":
            duration_text = "approximately 60-75 minutes"
        elif duration_preference != "Any": # Handles custom values if ever introduced
             duration_text = f"around {duration_preference}"

        user_prompt_parts.append(f"*   Engage in the selected Zone 2 cardiovascular exercise for {duration_text}.")
        user_prompt_parts.append("*   Maintain the target intensity (Zone 2 / RPE 3-4) consistently throughout this period.")
        user_prompt_parts.append("\n**Phase 3: Cool-down (Recovery)**")
        user_prompt_parts.append("*   Gradual decrease in intensity for 3-5 minutes.")
        user_prompt_parts.append("*   Light static stretching for major muscle groups used.")

    elif workout_pillar == "HIIT":
        user_prompt_parts.append("**Phase 1: Warm-up (Preparation & Activation)**")
        user_prompt_parts.append("*   Perform a thorough warm-up for 7-10 minutes. This is CRITICAL for HIIT. Include: general cardio (light jogging, cycling), dynamic stretches (leg swings, arm circles, torso twists), and 2-3 drills that gradually build intensity and mimic movements in the main HIIT session (e.g., practice burpees at 50% intensity, do some faster cadence cycling/running bursts).")
        user_prompt_parts.append("\n**Phase 2: Main Workout (HIIT Intervals)**")
        # The chosen_protocol from PART 2 will dictate the structure.
        # The AI should use chosen_protocol['structure_detail'] to build this part.
        # Duration preference can hint at total number of intervals or blocks for some protocols.
        user_prompt_parts.append(f"*   Execute the **{chosen_protocol['name']}** protocol as defined in PART 2. Ensure total HIIT work phase (excluding warm-up/cool-down) aligns with client preference if possible (Short: ~8-10 min, Medium: ~10-15 min, Long: ~15-20 min of intervals). Adjust number of reps/sets/blocks of the chosen protocol if necessary.")
        user_prompt_parts.append("*   Ensure exercise selection is appropriate for the protocol's demands.")
        user_prompt_parts.append("\n**Phase 3: Cool-down (Recovery)**")
        user_prompt_parts.append("*   Active recovery (e.g., light walking) for 5-7 minutes.")
        user_prompt_parts.append("*   Static stretching for major muscle groups used.")

    elif workout_pillar == "Stability/Mobility":
        user_prompt_parts.append("**Phase 1: Warm-up (Preparation & Activation)**")
        user_prompt_parts.append("*   Perform 5-7 minutes of light, dynamic movements that gently take joints through their range of motion. Examples: neck tilts/rotations, shoulder rolls, cat-cow, bird-dog, hip circles, ankle circles. Match to client's daily focus if specified.")
        user_prompt_parts.append("\n**Phase 2: Main Workout (Stability/Mobility Circuit)**")
        user_prompt_parts.append(f"*   Design a circuit of 4-6 exercises. The circuit should target the client's specified focus: **{focus if focus else 'Full Body'}**.")
        user_prompt_parts.append("*   Exercises should be selected to improve core strength, balance, joint mobility, and/or flexibility based on the chosen focus and pillar methodology.")
        user_prompt_parts.append("*   Prescribe 2-3 sets per exercise. Repetitions should be in the 10-15 range for dynamic movements, or holds for 20-60 seconds for isometric exercises (like planks or balance poses).")
        user_prompt_parts.append("*   Rest between exercises should be minimal (15-30s), with slightly longer rest (45-60s) between circuits if multiple circuits are performed.")
        user_prompt_parts.append("\n**Phase 3: Cool-down (Recovery)**")
        user_prompt_parts.append("*   Static stretching for 5-7 minutes, focusing on areas worked or known to be tight.")

    user_prompt_parts.append("\n---")
    
    # --- PART 4: OUTPUT FORMATTING ---
    user_prompt_parts.append("### **PART 4: OUTPUT FORMATTING**")
    user_prompt_parts.append("---")
    user_prompt_parts.append("*   Generate the entire workout plan using clean and clear markdown.")
    user_prompt_parts.append("*   Use headings (##) for each phase (Warm-up, Main Workout, Cool-down).")
    user_prompt_parts.append("*   Use bullet points (*) or numbered lists for exercises.")
    user_prompt_parts.append("*   Clearly label any supersets or circuits (e.g., \"Superset A:\").")
    user_prompt_parts.append("*   For each exercise, provide the sets, reps, and the exact rest period as defined in your rules (if applicable to the pillar).")
    user_prompt_parts.append("*   For each exercise, include a single, impactful \"Coach's Cue\" focusing on the most critical aspect of its form or execution.")

    user_prompt = "\n".join(user_prompt_parts)
    logger.info(f"Generating workout with prompt length: {len(user_prompt)}")
    
    # Non-streaming call for JSON response
    response = current_gemini_provider.model.generate_content(f"{system_instruction}\n\n{user_prompt}")
    
    try:
        # The response text should be a JSON string.
        response_json = json.loads(response.text)
        full_workout_text = response_json.get("workout_text", "")
        muscles_worked = response_json.get("muscles_worked", []) # AI should provide this based on new prompts
        
        if not full_workout_text or not isinstance(muscles_worked, list):
            raise ValueError("Invalid JSON structure from AI.")

        # Determine the 'focus' to return based on pillar
        returned_focus = focus
        if workout_pillar == "Zone2 Cardio":
            returned_focus = "Cardio"
        elif workout_pillar == "HIIT":
            returned_focus = "Full Body / Cardio"
        elif workout_pillar == "Stability/Mobility" and not focus: # If no specific focus given for S/M
            returned_focus = "Full Body"


        return {
            "pillar": workout_pillar, # Use the input pillar
            "focus": returned_focus,  # Use the potentially modified focus
            "muscles_worked": muscles_worked,
            "workout_text": full_workout_text
        }

    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Failed to parse JSON response from Gemini: {e}")
        logger.error(f"Raw response text: {response.text}")
        raise ValueError("AI returned an invalid response format. Please try again.")