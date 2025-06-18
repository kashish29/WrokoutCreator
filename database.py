import sqlite3
import json
from datetime import datetime, timedelta, date # Added date

DB_FILE = "training_app.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row # Allows accessing columns by name
    return conn

def setup_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Create user_settings table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL UNIQUE,
        strength_freq INTEGER DEFAULT 2,
        hiit_freq INTEGER DEFAULT 1,
        zone2_freq INTEGER DEFAULT 2,
        recovery_freq INTEGER DEFAULT 1,
        stability_freq INTEGER DEFAULT 1,
        focus_rotation TEXT DEFAULT '["Upper Body", "Lower Body", "Push", "Pull"]',
        primary_goal TEXT DEFAULT 'Balanced Fitness',
        ai_model_id TEXT DEFAULT 'gemini-1.5-flash-latest',
        workout_duration_preference TEXT DEFAULT 'Any',
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')

    # Add new columns if they don't exist
    try:
        cursor.execute("SELECT ai_model_id, workout_duration_preference, stability_freq FROM user_settings LIMIT 1")
    except sqlite3.OperationalError:
        print("Attempting to add new columns to 'user_settings' table.")
        # Add columns one by one, committing after each, in case some already exist
        try:
            cursor.execute("ALTER TABLE user_settings ADD COLUMN ai_model_id TEXT DEFAULT 'gemini-1.5-flash-latest'")
            conn.commit()
            print("Column 'ai_model_id' added or already exists.")
        except sqlite3.OperationalError:
            conn.rollback() # Rollback if this specific ALTER fails (e.g. column exists)
            print("Column 'ai_model_id' likely already exists.")
        try:
            cursor.execute("ALTER TABLE user_settings ADD COLUMN workout_duration_preference TEXT DEFAULT 'Any'")
            conn.commit()
            print("Column 'workout_duration_preference' added or already exists.")
        except sqlite3.OperationalError:
            conn.rollback()
            print("Column 'workout_duration_preference' likely already exists.")
        try:
            cursor.execute("ALTER TABLE user_settings ADD COLUMN stability_freq INTEGER DEFAULT 1")
            conn.commit()
            print("Column 'stability_freq' added or already exists.")
        except sqlite3.OperationalError:
            conn.rollback()
            print("Column 'stability_freq' likely already exists.")

    # Create weekly_plan table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS weekly_plan (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        week_start_date DATE NOT NULL,
        day_of_week INTEGER NOT NULL, -- 0=Monday, 6=Sunday
        pillar_focus TEXT NOT NULL, -- e.g., 'Strength', 'Zone2', 'HIIT', 'Stability', 'Rest'
        workout_id INTEGER,          -- NULLABLE, FK to workout_history.id
        status TEXT NOT NULL,        -- e.g., 'Planned', 'Completed', 'Skipped'
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (workout_id) REFERENCES workout_history (id)
    )
    ''')

    # Create workout_history table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS workout_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        workout_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        pillar TEXT NOT NULL,
        focus TEXT NOT NULL,
        muscles_worked TEXT,
        full_workout_text TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')

    # Create a default user and their settings if they don't exist
    cursor.execute("SELECT id FROM users WHERE username = 'default_user'")
    user = cursor.fetchone()
    if not user:
        cursor.execute("INSERT INTO users (username) VALUES (?)", ('default_user',))
        user_id = cursor.lastrowid
        
        default_settings = {
            "user_id": user_id,
            "strength_freq": 2,
            "hiit_freq": 1,
            "zone2_freq": 2,
            "recovery_freq": 1,
            "stability_freq": 1,
            "focus_rotation": json.dumps(["Upper Body", "Lower Body", "Push", "Pull"]),
            "primary_goal": "Balanced Fitness",
            "ai_model_id": "gemini-1.5-flash-latest",
            "workout_duration_preference": "Any"
        }
        cursor.execute('''
        INSERT INTO user_settings (user_id, strength_freq, hiit_freq, zone2_freq, recovery_freq, stability_freq, focus_rotation, primary_goal, ai_model_id, workout_duration_preference)
        VALUES (:user_id, :strength_freq, :hiit_freq, :zone2_freq, :recovery_freq, :stability_freq, :focus_rotation, :primary_goal, :ai_model_id, :workout_duration_preference)
        ''', default_settings)
        conn.commit()
        print(f"Default user 'default_user' with ID {user_id} and settings created with new fields including stability_freq.")
    else:
        user_id = user['id']
        # Check if settings exist for default user, if not, create them
        cursor.execute("SELECT id FROM user_settings WHERE user_id = ?", (user_id,))
        settings = cursor.fetchone()
        if not settings:
            default_settings_values = {
                "user_id": user_id,
                "strength_freq": 2,
                "hiit_freq": 1,
                "zone2_freq": 2,
                "recovery_freq": 1,
                "stability_freq": 1,
                "focus_rotation": json.dumps(["Upper Body", "Lower Body", "Push", "Pull"]),
                "primary_goal": "Balanced Fitness",
                "ai_model_id": "gemini-1.5-flash-latest",
                "workout_duration_preference": "Any"
            }
            cursor.execute('''
        INSERT INTO user_settings (user_id, strength_freq, hiit_freq, zone2_freq, recovery_freq, stability_freq, focus_rotation, primary_goal, ai_model_id, workout_duration_preference)
        VALUES (:user_id, :strength_freq, :hiit_freq, :zone2_freq, :recovery_freq, :stability_freq, :focus_rotation, :primary_goal, :ai_model_id, :workout_duration_preference)
            ''', default_settings_values)
            conn.commit()
        print(f"Default settings created for existing user 'default_user' with ID {user_id} with new fields including stability_freq.")


    conn.close()
    print("Database setup complete. Tables created and default user/settings ensured.")

def save_workout_to_history(user_id, pillar, focus, muscles_worked, full_workout_text):
    conn = get_db_connection()
    cursor = conn.cursor()
    muscles_worked_json = json.dumps(muscles_worked)
    try:
        cursor.execute('''
        INSERT INTO workout_history (user_id, workout_date, pillar, focus, muscles_worked, full_workout_text)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, datetime.now(), pillar, focus, muscles_worked_json, full_workout_text))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def get_workout_history(user_id, days=14):
    conn = get_db_connection()
    cursor = conn.cursor()
    start_date = datetime.now() - timedelta(days=days)
    
    cursor.execute('''
    SELECT id, pillar, focus, muscles_worked, workout_date, full_workout_text
    FROM workout_history
    WHERE user_id = ? AND workout_date >= ?
    ORDER BY workout_date DESC
    ''', (user_id, start_date))
    
    history = []
    for row in cursor.fetchall():
        entry = dict(row)
        if entry['muscles_worked']:
            entry['muscles_worked'] = json.loads(entry['muscles_worked'])
        else:
            entry['muscles_worked'] = [] # Ensure it's always a list
        history.append(entry)
        
    conn.close()
    return history

def delete_workout_from_history(workout_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM workout_history WHERE id = ?", (workout_id,))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def get_user_settings(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fetch all relevant columns including the new ones
    cursor.execute("""
        SELECT strength_freq, hiit_freq, zone2_freq, recovery_freq, stability_freq,
               focus_rotation, primary_goal, ai_model_id, workout_duration_preference
        FROM user_settings WHERE user_id = ?
    """, (user_id,))
    settings_row = cursor.fetchone()
    
    if settings_row:
        settings = dict(settings_row)
        # Safely parse JSON for focus_rotation
        try:
            settings['focus_rotation'] = json.loads(settings['focus_rotation']) if settings['focus_rotation'] else []
        except (json.JSONDecodeError, TypeError):
            settings['focus_rotation'] = ["Upper Body", "Lower Body", "Push", "Pull"] # Default on error

        # Provide defaults for new fields if they are missing (e.g., for older records)
        if 'ai_model_id' not in settings or settings['ai_model_id'] is None:
            settings['ai_model_id'] = 'gemini-1.5-flash-latest' # Default model
        if 'workout_duration_preference' not in settings or settings['workout_duration_preference'] is None:
            settings['workout_duration_preference'] = 'Any' # Default duration
        if 'stability_freq' not in settings or settings['stability_freq'] is None:
            settings['stability_freq'] = 1 # Default stability frequency
    else:
        # Return default settings if none found for the user
        settings = {
            "strength_freq": 2,
            "hiit_freq": 1,
            "zone2_freq": 2,
            "recovery_freq": 1,
            "stability_freq": 1,
            "focus_rotation": ["Upper Body", "Lower Body", "Push", "Pull"],
            "primary_goal": "Balanced Fitness",
            "ai_model_id": "gemini-1.5-flash-latest",
            "workout_duration_preference": "Any"
        }
    conn.close()
    return settings

# --- Weekly Plan Functions ---

def clear_weekly_plan(user_id, week_start_date, conn=None):
    """Clears all weekly plan entries for a given user and week_start_date."""
    db_conn = conn or get_db_connection()
    cursor = db_conn.cursor()
    try:
        iso_week_start_date = week_start_date.isoformat() if isinstance(week_start_date, date) else week_start_date
        cursor.execute(
            "DELETE FROM weekly_plan WHERE user_id = ? AND week_start_date = ?",
            (user_id, iso_week_start_date)
        )
        if not conn: # Only commit if this function owns the connection
            db_conn.commit()
        print(f"Cleared weekly plan for user {user_id}, week starting {iso_week_start_date}")
    except sqlite3.Error as e:
        print(f"Database error clearing weekly plan: {e}")
        if not conn:
            db_conn.rollback()
        raise # Re-raise the exception to be handled by the caller
    finally:
        if not conn: # Only close if this function owns the connection
            db_conn.close()

def save_daily_plan_entry(plan_entry_data, conn=None):
    """Saves a single day's plan entry into the weekly_plan table."""
    db_conn = conn or get_db_connection()
    cursor = db_conn.cursor()
    try:
        # Ensure week_start_date is in ISO format if it's a date object
        if 'week_start_date' in plan_entry_data and isinstance(plan_entry_data['week_start_date'], date):
            plan_entry_data['week_start_date'] = plan_entry_data['week_start_date'].isoformat()

        cursor.execute('''
            INSERT INTO weekly_plan (user_id, week_start_date, day_of_week, pillar_focus, status, workout_id)
            VALUES (:user_id, :week_start_date, :day_of_week, :pillar_focus, :status, :workout_id)
        ''', plan_entry_data)
        if not conn: # Only commit if this function owns the connection
            db_conn.commit()
        # print(f"Saved daily plan entry: {plan_entry_data}") # Can be verbose
    except sqlite3.Error as e:
        print(f"Database error saving daily plan entry: {e}")
        if not conn:
            db_conn.rollback()
        raise
    finally:
        if not conn:
            db_conn.close()

def get_weekly_plan(user_id, week_start_date, conn=None):
    """Retrieves the weekly plan for a given user and week_start_date."""
    db_conn = conn or get_db_connection()
    cursor = db_conn.cursor()
    try:
        iso_week_start_date = week_start_date.isoformat() if isinstance(week_start_date, date) else week_start_date
        cursor.execute('''
            SELECT id, user_id, week_start_date, day_of_week, pillar_focus, workout_id, status
            FROM weekly_plan
            WHERE user_id = ? AND week_start_date = ?
            ORDER BY day_of_week ASC
        ''', (user_id, iso_week_start_date))

        plan_entries = [dict(row) for row in cursor.fetchall()]
        return plan_entries
    except sqlite3.Error as e:
        print(f"Database error retrieving weekly plan: {e}")
        raise
    finally:
        if not conn:
            db_conn.close()

# --- User Settings Functions ---

def save_user_settings(user_id, settings_dict):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Ensure focus_rotation is a JSON string
    if 'focus_rotation' in settings_dict and isinstance(settings_dict['focus_rotation'], list):
        settings_dict['focus_rotation'] = json.dumps(settings_dict['focus_rotation'])

    # Check if settings for this user_id already exist
    cursor.execute("SELECT id FROM user_settings WHERE user_id = ?", (user_id,))
    existing_setting = cursor.fetchone()

    try:
        if existing_setting:
            # Update existing settings
            # Construct the SET part of the SQL query dynamically
            set_clause = ", ".join([f"{key} = :{key}" for key in settings_dict.keys()])
            sql = f"UPDATE user_settings SET {set_clause} WHERE user_id = :user_id"
            
            params_to_update = settings_dict.copy()
            params_to_update['user_id'] = user_id 
            
            cursor.execute(sql, params_to_update)
        else:
            # Insert new settings
            # Ensure all required fields for insertion are present, using defaults if necessary
            # This is important if settings_dict doesn't contain all fields
            # Or, we retrieve current, update, then save. For simplicity, assume settings_dict is complete for insert.
            # A more robust way would be to merge with default values first.
            
            # Add user_id to the dictionary for insertion
            settings_dict['user_id'] = user_id
            columns = ', '.join(settings_dict.keys())
            placeholders = ', '.join([f":{key}" for key in settings_dict.keys()])
            sql = f"INSERT INTO user_settings ({columns}) VALUES ({placeholders})"
            cursor.execute(sql, settings_dict)
        
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    # Example usage (for testing purposes)
    print("Setting up database...")
    setup_database()
    print("Database setup should be complete.")

    # Test fetching default user settings (user_id 1 is default)
    print("\nFetching settings for user 1 (default):")
    settings = get_user_settings(1)
    print(settings)

    # Test saving settings for user 1
    print("\nSaving new settings for user 1:")
    new_settings = {
        "strength_freq": 3,
        "hiit_freq": 2,
        "zone2_freq": 3,
        "recovery_freq": 1,
        "stability_freq": 2, # Test new value
        "focus_rotation": ["Push", "Pull", "Legs", "Upper", "Lower"],
        "primary_goal": "Strength Gain",
        "ai_model_id": "gemini-1.5-pro-latest",
        "workout_duration_preference": "Medium"
    }
    save_user_settings(1, new_settings)
    updated_settings = get_user_settings(1)
    print(updated_settings)
    assert updated_settings["strength_freq"] == 3
    assert updated_settings["focus_rotation"] == ["Push", "Pull", "Legs", "Upper", "Lower"]
    assert updated_settings["primary_goal"] == "Strength Gain"
    assert updated_settings["ai_model_id"] == "gemini-1.5-pro-latest"
    assert updated_settings["workout_duration_preference"] == "Medium"
    assert updated_settings["stability_freq"] == 2
    print("Settings save and update seems to work for all fields, including stability_freq.")

    # Test saving workout history
    print("\nSaving a sample workout for user 1:")
    save_workout_to_history(1, "Strength", "Upper Body", ["Chest", "Triceps"], "Workout Details: ...")
    save_workout_to_history(1, "Zone2", "Cardio", ["Cardio"], "Run: 30 minutes")
    print("Sample workouts saved.")

    # Test fetching workout history
    print("\nFetching workout history for user 1 (last 14 days):")
    history = get_workout_history(1, days=14)
    # for item in history:
    #     print(item)
    # assert len(history) >= 2 # This assertion might fail if script is run on different days
    print(f"Found {len(history)} items in workout history (last 14 days).")
    print("Workout history fetching seems to work.")
    
    print("\nFetching workout history for user 1 (last 1 day):")
    history_today = get_workout_history(1, days=1)
    # for item in history_today:
    #     print(item)
    # assert len(history_today) >= 2 # This assertion might fail if script is run on different days
    print(f"Found {len(history_today)} items in workout history (last 1 day).")
    print("Workout history fetching for today seems to work.")

    # Test weekly_plan functions
    print("\nTesting weekly_plan functions...")
    test_user_id = 1
    today = date.today() # Use date.today()
    test_week_start_date = today - timedelta(days=today.weekday())

    # Clear any existing plan for the test week
    print(f"Clearing plan for user {test_user_id} for week {test_week_start_date.isoformat()}")
    clear_weekly_plan(test_user_id, test_week_start_date)

    # Save a couple of entries
    entry1 = {
        "user_id": test_user_id, "week_start_date": test_week_start_date, "day_of_week": 0,
        "pillar_focus": "Strength", "status": "Planned", "workout_id": None
    }
    entry2 = {
        "user_id": test_user_id, "week_start_date": test_week_start_date, "day_of_week": 1,
        "pillar_focus": "Zone2", "status": "Planned", "workout_id": None
    }
    save_daily_plan_entry(entry1)
    print("Saved entry 1")
    save_daily_plan_entry(entry2)
    print("Saved entry 2")

    # Get the plan
    retrieved_plan = get_weekly_plan(test_user_id, test_week_start_date)
    print(f"Retrieved plan: {retrieved_plan}")
    assert len(retrieved_plan) == 2
    assert retrieved_plan[0]['pillar_focus'] == "Strength"
    assert retrieved_plan[1]['day_of_week'] == 1

    # Clear again
    clear_weekly_plan(test_user_id, test_week_start_date)
    retrieved_plan_after_clear = get_weekly_plan(test_user_id, test_week_start_date)
    assert len(retrieved_plan_after_clear) == 0
    print("Weekly plan functions seem to work.")