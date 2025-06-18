import datetime

def generate_and_save_weekly_plan(user_id, user_settings, db_connection_func):
    """
    Generates a weekly workout plan based on user settings and saves it to the database.
    """
    print(f"Generating weekly plan for user_id: {user_id} with settings: {user_settings}")

    strength_freq = user_settings.get('strength_freq', 0)
    zone2_freq = user_settings.get('zone2_freq', 0)
    hiit_freq = user_settings.get('hiit_freq', 0)
    stability_freq = user_settings.get('stability_freq', 0)
    # recovery_freq from settings could also be considered as 'Rest' or light activity
    # For now, we calculate rest days based on the sum of other activities.

    primary_goal = user_settings.get('primary_goal', 'Balanced Fitness')
    print(f"Primary Goal for plan generation: {primary_goal}")

    pillars = []
    pillars.extend(['Strength'] * strength_freq)
    pillars.extend(['Zone2'] * zone2_freq)
    pillars.extend(['HIIT'] * hiit_freq)
    pillars.extend(['Stability'] * stability_freq)

    total_workout_days = len(pillars)

    if total_workout_days > 7:
        # Handle error: total frequency exceeds 7 days.
        # For now, we'll just log it and cap the workouts.
        print(f"Warning: Total workout frequency ({total_workout_days}) exceeds 7 days. Capping at 7.")
        pillars = pillars[:7]
        total_workout_days = 7

    rest_days = 7 - total_workout_days
    pillars.extend(['Rest'] * rest_days)

    # Simple sequential distribution for now.
    # TODO: Implement more sophisticated distribution logic.
    # Example: Avoid HIIT/Strength back-to-back, distribute rest days.
    # For now, shuffle to get some variation if frequencies are low, or just fill sequentially.
    # import random
    # random.shuffle(pillars) # This might be too random without further logic.

    weekly_distribution = [None] * 7
    for i in range(len(pillars)):
        if i < 7: # Ensure we don't go out of bounds for weekly_distribution
            weekly_distribution[i] = pillars[i]

    # Fill remaining days with 'Rest' if any day is still None (e.g. if total workouts < 7 and shuffle made gaps)
    for i in range(7):
        if weekly_distribution[i] is None:
            weekly_distribution[i] = 'Rest'


    print(f"Generated weekly distribution: {weekly_distribution}")

import database # Assuming database.py is in the same directory or accessible via PYTHONPATH

def generate_and_save_weekly_plan(user_id, user_settings, db_connection_func):
    """
    Generates a weekly workout plan based on user settings and saves it to the database.
    Uses functions from the database module.
    """
    print(f"Generating weekly plan for user_id: {user_id} with settings: {user_settings}")

    strength_freq = user_settings.get('strength_freq', 0)
    zone2_freq = user_settings.get('zone2_freq', 0)
    hiit_freq = user_settings.get('hiit_freq', 0)
    stability_freq = user_settings.get('stability_freq', 0)
    primary_goal = user_settings.get('primary_goal', 'Balanced Fitness')
    print(f"Primary Goal for plan generation: {primary_goal}")

    pillars = []
    pillars.extend(['Strength'] * strength_freq)
    pillars.extend(['Zone2'] * zone2_freq)
    pillars.extend(['HIIT'] * hiit_freq)
    pillars.extend(['Stability'] * stability_freq)

    total_workout_days = len(pillars)

    if total_workout_days > 7:
        print(f"Warning: Total workout frequency ({total_workout_days}) exceeds 7 days. Capping at 7 and prioritizing.")
        # Basic prioritization: Strength, HIIT, Zone2, Stability. Can be more sophisticated.
        prioritized_pillars = []
        temp_pillars = {
            'Strength': strength_freq, 'HIIT': hiit_freq,
            'Zone2': zone2_freq, 'Stability': stability_freq
        }
        order = ['Strength', 'HIIT', 'Zone2', 'Stability']

        for p_type in order:
            count = temp_pillars[p_type]
            for _ in range(count):
                if len(prioritized_pillars) < 7:
                    prioritized_pillars.append(p_type)
                else:
                    break
            if len(prioritized_pillars) == 7:
                break
        pillars = prioritized_pillars
        total_workout_days = len(pillars)

    rest_days = 7 - total_workout_days
    pillars.extend(['Rest'] * rest_days)

    # Simple sequential distribution for now.
    weekly_distribution = [pillars[i] if i < len(pillars) else 'Rest' for i in range(7)]
    print(f"Generated weekly distribution: {weekly_distribution}")

    # Database interaction
    conn = None
    try:
        conn = db_connection_func() # Use the passed-in function to get a connection

        today = datetime.date.today()
        week_start_date = today - datetime.timedelta(days=today.weekday())
        print(f"Week start date: {week_start_date}")

        # Clear existing plan for that user and week using database function
        database.clear_weekly_plan(user_id, week_start_date, conn=conn)
        # The print statement is already in clear_weekly_plan

        # Save the new plan using database function
        for day_of_week, pillar_focus in enumerate(weekly_distribution):
            plan_entry_data = {
                "user_id": user_id,
                "week_start_date": week_start_date, # Pass as date object
                "day_of_week": day_of_week,
                "pillar_focus": pillar_focus,
                "status": "Planned",
                "workout_id": None
            }
            database.save_daily_plan_entry(plan_entry_data, conn=conn)
            # print(f"Saved plan entry: {plan_entry_data}") # save_daily_plan_entry can be verbose if needed

        conn.commit() # Commit once after all entries are saved successfully
        print("Weekly plan generated and saved successfully.")

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error generating or saving weekly plan: {e}")
        # Consider re-raising or specific error handling based on error type
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    # This example usage will now try to use the actual database.py
    # Ensure training_app.db can be created/accessed from where this is run.
    # And that database.py is in python path.

    # For a true standalone test, we might need to adjust PYTHONPATH or run as a module
    # For now, assuming it can import database if in the same directory.

    # Setup database if it doesn't exist (or tables are missing)
    print("Running weekly_planner.py standalone test...")
    print("Attempting to set up database for test...")
    try:
        database.setup_database() # Make sure tables exist
    except Exception as e:
        print(f"Error setting up database for test: {e}")
        print("Please ensure database.py is accessible and can connect/create training_app.db")
        exit(1)

    print("\n--- Test Case 1: Standard Frequencies ---")
    sample_user_settings_1 = {
        "strength_freq": 3, "zone2_freq": 2, "hiit_freq": 1,
        "stability_freq": 1, "primary_goal": "Balanced Fitness"
    }
    # Ensure user 1 exists or create them (simplified for test)
    try:
        conn_test = database.get_db_connection()
        cursor_test = conn_test.cursor()
        cursor_test.execute("INSERT OR IGNORE INTO users (id, username) VALUES (?, ?)", (1, 'test_user_1_planner'))
        cursor_test.execute("INSERT OR IGNORE INTO users (id, username) VALUES (?, ?)", (2, 'test_user_2_planner'))
        cursor_test.execute("INSERT OR IGNORE INTO users (id, username) VALUES (?, ?)", (3, 'test_user_3_planner'))
        conn_test.commit()
    except Exception as e_user:
        print(f"Error ensuring test users exist: {e_user}")
    finally:
        if conn_test:
            conn_test.close()

    generate_and_save_weekly_plan(1, sample_user_settings_1, database.get_db_connection)

    # Verify by fetching
    today = datetime.date.today()
    week_start_date_test = today - datetime.timedelta(days=today.weekday())
    plan_1 = database.get_weekly_plan(1, week_start_date_test)
    print(f"Fetched plan for user 1: {plan_1}")
    assert len(plan_1) == 7, f"Expected 7 days in plan, got {len(plan_1)}"
    assert [p['pillar_focus'] for p in plan_1].count('Rest') == 0 # 3+2+1+1 = 7

    print("\n--- Test Case 2: Overflow Frequencies ---")
    sample_user_settings_2 = {
        "strength_freq": 4, "zone2_freq": 2, "hiit_freq": 2,
        "stability_freq": 1, "primary_goal": "Strength Focus" # Total 9
    }
    generate_and_save_weekly_plan(2, sample_user_settings_2, database.get_db_connection)
    plan_2 = database.get_weekly_plan(2, week_start_date_test)
    print(f"Fetched plan for user 2 (overflow): {plan_2}")
    assert len(plan_2) == 7, f"Expected 7 days in plan for overflow, got {len(plan_2)}"
    # Check if it capped at 7 workout days (0 rest days)
    assert [p['pillar_focus'] for p in plan_2].count('Rest') == 0
    # Check prioritization (Strength > HIIT > Zone2 > Stability)
    # Expected: S, S, S, S, H, H, Z (or similar if stability gets cut)
    plan_pillars_2 = [p['pillar_focus'] for p in plan_2]
    assert plan_pillars_2.count('Strength') == 4
    assert plan_pillars_2.count('HIIT') == 2
    assert plan_pillars_2.count('Zone2') == 1
    assert plan_pillars_2.count('Stability') == 0 # Stability should be cut


    print("\n--- Test Case 3: Few Frequencies ---")
    sample_user_settings_3 = {
        "strength_freq": 1, "zone2_freq": 1, "hiit_freq": 0,
        "stability_freq": 1, "primary_goal": "Longevity" # Total 3
    }
    generate_and_save_weekly_plan(3, sample_user_settings_3, database.get_db_connection)
    plan_3 = database.get_weekly_plan(3, week_start_date_test)
    print(f"Fetched plan for user 3 (few): {plan_3}")
    assert len(plan_3) == 7, f"Expected 7 days in plan for few, got {len(plan_3)}"
    assert [p['pillar_focus'] for p in plan_3].count('Rest') == 4, \
        f"Expected 4 rest days, got {[p['pillar_focus'] for p in plan_3].count('Rest')}"

    print("\nWeekly planner standalone tests completed.")
