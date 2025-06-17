import sqlite3
import json
from datetime import datetime, timedelta

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
        focus_rotation TEXT DEFAULT '["Upper Body", "Lower Body", "Push", "Pull"]',
        primary_goal TEXT DEFAULT 'Balanced Fitness',
        ai_model_id TEXT DEFAULT 'gemini-1.5-flash-latest',
        workout_duration_preference TEXT DEFAULT 'Any',
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')

    # Add new columns if they don't exist (for existing tables)
    # This is a common pattern but might be complex with just one replace operation.
    # For now, we assume CREATE TABLE IF NOT EXISTS handles new setups,
    # and manual migration might be needed for existing dbs if this script is rerun.
    # A more robust script would use try-except blocks for ALTER TABLE.
    try:
        cursor.execute("SELECT ai_model_id, workout_duration_preference FROM user_settings LIMIT 1")
    except sqlite3.OperationalError:
        # Columns likely don't exist, try to add them
        print("Attempting to add 'ai_model_id' and 'workout_duration_preference' to 'user_settings' table.")
        try:
            cursor.execute("ALTER TABLE user_settings ADD COLUMN ai_model_id TEXT DEFAULT 'gemini-1.5-flash-latest'")
            cursor.execute("ALTER TABLE user_settings ADD COLUMN workout_duration_preference TEXT DEFAULT 'Any'")
            conn.commit()
            print("Columns added successfully.")
        except sqlite3.OperationalError as e:
            print(f"Error adding columns: {e}. Manual schema migration might be needed.")


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
            "focus_rotation": json.dumps(["Upper Body", "Lower Body", "Push", "Pull"]),
            "primary_goal": "Balanced Fitness",
            "ai_model_id": "gemini-1.5-flash-latest",
            "workout_duration_preference": "Any"
        }
        cursor.execute('''
        INSERT INTO user_settings (user_id, strength_freq, hiit_freq, zone2_freq, recovery_freq, focus_rotation, primary_goal, ai_model_id, workout_duration_preference)
        VALUES (:user_id, :strength_freq, :hiit_freq, :zone2_freq, :recovery_freq, :focus_rotation, :primary_goal, :ai_model_id, :workout_duration_preference)
        ''', default_settings)
        conn.commit()
        print(f"Default user 'default_user' with ID {user_id} and settings created with new fields.")
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
                "focus_rotation": json.dumps(["Upper Body", "Lower Body", "Push", "Pull"]),
            "primary_goal": "Balanced Fitness",
            "ai_model_id": "gemini-1.5-flash-latest",
            "workout_duration_preference": "Any"
            }
            cursor.execute('''
        INSERT INTO user_settings (user_id, strength_freq, hiit_freq, zone2_freq, recovery_freq, focus_rotation, primary_goal, ai_model_id, workout_duration_preference)
        VALUES (:user_id, :strength_freq, :hiit_freq, :zone2_freq, :recovery_freq, :focus_rotation, :primary_goal, :ai_model_id, :workout_duration_preference)
            ''', default_settings_values)
            conn.commit()
        print(f"Default settings created for existing user 'default_user' with ID {user_id} with new fields.")


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
    SELECT pillar, focus, muscles_worked, workout_date, full_workout_text
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

def get_user_settings(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fetch all relevant columns including the new ones
    cursor.execute("""
        SELECT strength_freq, hiit_freq, zone2_freq, recovery_freq,
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
    else:
        # Return default settings if none found for the user
        settings = {
            "strength_freq": 2,
            "hiit_freq": 1,
            "zone2_freq": 2,
            "recovery_freq": 1,
            "focus_rotation": ["Upper Body", "Lower Body", "Push", "Pull"],
            "primary_goal": "Balanced Fitness",
            "ai_model_id": "gemini-1.5-flash-latest",
            "workout_duration_preference": "Any"
        }
    conn.close()
    return settings

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
    print("Settings save and update seems to work for all fields.")

    # Test saving workout history
    print("\nSaving a sample workout for user 1:")
    save_workout_to_history(1, "Strength", "Upper Body", ["Chest", "Triceps"], "Workout Details: ...")
    save_workout_to_history(1, "Zone2", "Cardio", ["Cardio"], "Run: 30 minutes")
    print("Sample workouts saved.")

    # Test fetching workout history
    print("\nFetching workout history for user 1 (last 14 days):")
    history = get_workout_history(1, days=14)
    for item in history:
        print(item)
    assert len(history) >= 2 
    print("Workout history fetching seems to work.")
    
    print("\nFetching workout history for user 1 (last 1 day):")
    history_today = get_workout_history(1, days=1)
    for item in history_today:
        print(item)
    assert len(history_today) >= 2 # Assuming run within a day of each other for test
    print("Workout history fetching for today seems to work.")