# MVP AI Workout Generator & Coaching Engine

## Description
This project has evolved from a simple workout generator into a sophisticated, evidence-based AI coaching engine. It leverages the Google Gemini API to create highly personalized and context-aware training plans. The system is built upon a pillar-based training philosophy, designing weekly microcycles and daily workouts around **Strength, Zone 2 Cardio, High-Intensity Interval Training (HIIT) for VO2 Max, and Stability/Mobility**.

It incorporates advanced training methodologies, intelligent safety constraints, modality-specific program design (for bodyweight-only users or those with cardio equipment), and weekly context awareness (considering recent training history and planned workouts) to deliver tailored and effective fitness guidance.

## Features
- **Pillar-Based Training:** Programs daily workouts based on four core pillars: Strength, Zone 2 Cardio, HIIT (VO2 Max), and Stability/Mobility.
- **Evidence-Based Weekly Structuring:** User's primary goal (e.g., Longevity, Fat Loss, Balanced Fitness) and pillar frequency settings (days per week for each pillar) guide the generation of a dynamic weekly microcycle plan.
- **Advanced Strength Methodologies:** Incorporates techniques like Antagonist/Agonist Supersets, Pre-exhaustion Sets, Top Set/Back-off Sets, and Contrast Training, intelligently selected based on the user's chosen strength style (e.g., Build Muscle, Get Stronger) and experience level.
- **Specific HIIT Protocols:** Utilizes proven HIIT structures such as Norwegian 4x4 (for VO2 Max), Billat 30/30s (for vVO2 Max), various micro-interval formats, and adaptable generic HIIT. Protocol selection is influenced by user experience.
- **Intelligent Safety Constraints:** Guided by negative constraints to avoid common programming errors like excessive spinal over-compression, core pre-fatigue before heavy lifts, and improper push/pull sequencing in strength training.
- **Modality-Specific Program Design:**
    - Adapts logic for **bodyweight-only training** by incorporating principles like mechanical difficulty progressions, tempo variations, and reps-to-failure/AMRAP prescriptions for Strength and Stability/Mobility pillars.
    - Integrates **cardio equipment** (Treadmill, Bike, Rower, etc.) as primary tools for Zone 2 Cardio and HIIT workouts, including machine-specific parameter guidance.
- **Context-Aware Daily Workouts:** Considers recent training history (last few sessions) and today's planned pillar from the weekly schedule to generate more relevant and effective daily sessions, including advice on managing intensity and recovery.
- **User-Friendly Web Interface:** Allows users to configure overall goals, weekly training frequencies, save their Gemini API Key, select a daily workout pillar, and generate detailed workout plans.
- **Database for Settings & History:** Stores user preferences (training frequencies, primary goal, API key), generated weekly plans, and workout history using SQLite.

## Technology Stack
- **Backend**: Python, Flask
- **AI Service**: Google Gemini API (e.g., Gemini 1.5 Flash, Gemini 1.5 Pro)
- **Frontend**: HTML, CSS (basic), JavaScript
- **Database**: SQLite
- **Dependency Management**: pip, requirements.txt
- **Testing**: unittest (Python standard library)

## Setup and Installation

1.  **Clone the repository (if applicable):**
    ```bash
    # If you have this project in a git repository:
    # git clone <repository_url>
    # cd <repository_directory>
    # For the current context, you likely already have the files.
    # Ensure you are in the project's root directory for the following steps.
    ```

2.  **Create a virtual environment:**
    It is highly recommended to use a virtual environment. From the project root directory:
    ```bash
    python3 -m venv venv
    ```

3.  **Activate the virtual environment:**
    -   On macOS and Linux:
        ```bash
        source venv/bin/activate
        ```
    -   On Windows (cmd.exe):
        ```bash
        .\venv\Scripts\activate.bat
        ```
    -   On Windows (PowerShell):
        ```bash
        .\venv\Scripts\Activate.ps1
        ```

4.  **Install dependencies:**
    From the project root directory, ensure your virtual environment is activated:
    ```bash
    pip install -r requirements.txt
    ```

5.  **API Key Configuration:**
    This application requires a Google Gemini API key.

    *   **Using the UI (Recommended):**
        1.  Run the application (see "Running the Application" below).
        2.  Open the web interface.
        3.  Scroll down to "User Settings".
        4.  Enter your **Gemini API Key** and click "Save Settings".
        5.  The key will be saved to a `user_config.json` file in the project root. This file is automatically added to `.gitignore` and should not be committed to version control.

    *   **Using a `.env` file (Fallback):**
        If `user_config.json` does not exist or does not contain an API key, the application will fall back to using an environment variable.
        The project uses `python-dotenv` to load environment variables from a `.env` file.
        Create a file named `.env` in the project root directory (alongside `app.py`).
        Add your API key to this file:
        ```env
        GEMINI_API_KEY="your_gemini_api_key_here"
        ```
        Ensure `.env` is listed in your `.gitignore` file.

    *   **Setting directly in your shell (Fallback):**
        As another fallback, you can set the environment variable directly in your terminal session before running the app.
        -   On macOS and Linux: `export GEMINI_API_KEY="your_gemini_api_key_here"`
        -   On Windows (cmd.exe): `set GEMINI_API_KEY=your_gemini_api_key_here`
        -   On Windows (PowerShell): `$env:GEMINI_API_KEY="your_gemini_api_key_here"`

## How to Use (Interface)

1.  **Initial Setup (User Settings):**
    *   Navigate to the "User Settings" section.
    *   **Primary Goal:** Select your main fitness objective (e.g., Balanced Fitness, Longevity, Fat Loss, VO2 Max Improvement, Strength Focus, Muscle Hypertrophy). This helps guide weekly planning.
    *   **Pillar Frequencies:** Set how many days per week you want to train for each pillar:
        *   Strength Frequency (days/week)
        *   HIIT Frequency (days/week)
        *   Zone 2 Frequency (days/week)
        *   Stability Frequency (days/week)
    *   **Gemini API Key:** Enter your Google Gemini API key.
    *   **Strength Focus Rotation:** (Optional) Define a comma-separated list of strength focuses (e.g., Upper Body, Lower Body, Push, Pull) if you want the system to rotate through them (future feature, currently influences nudge).
    *   **AI Model & Preferred Workout Duration:** Select your preferred AI model and workout length.
    *   Click "Save Settings". This will also generate your initial weekly plan based on these settings.

2.  **View Your Weekly Plan:**
    *   The "Your Current Weekly Plan" section will display the generated plan, showing which pillar is scheduled for each day of the current week.

3.  **Generate a Daily Workout:**
    *   Go to the "Generate Your Workout" form.
    *   **Select Workout Pillar:** Choose the type of workout you want for today (e.g., Strength, Zone2 Cardio). This should ideally align with your weekly plan but allows for flexibility.
    *   **Experience Level:** Select your current fitness experience.
    *   **Strength Style (if applicable):** If you selected "Strength" as the pillar, choose a style (e.g., Build Muscle, Get Stronger). This is less relevant for other pillars.
    *   **Workout Focus for Today:** For Strength or Stability/Mobility, specify a body part focus (e.g., Upper Body, Core). Less critical for Zone2/HIIT.
    *   **Available Equipment:** Check all equipment you have access to for this session.
    *   **User Notes:** Add any specific notes for the AI coach (e.g., injuries, preferences).
    *   Click "Generate Workout".

4.  **View and Save Workout:**
    *   Your personalized workout plan will appear in the "Your Workout Plan" area.
    *   You can click "Save Workout" to add it to your history.
    *   Workout history is displayed in the "Workout History" section.

## Backend Details
*   **`app.py`**: Main Flask application, handles routing, request processing, and orchestrates calls to other modules.
*   **`workout_generator.py`**: Contains the core logic for generating detailed daily workout prompts for the Gemini API, including pillar-specific rules, methodology selection, safety constraints, and modality adaptations.
*   **`weekly_planner.py`**: Responsible for generating a 7-day weekly plan based on user-defined pillar frequencies and primary goal. Stores this plan in the database.
*   **`database.py`**: Manages the SQLite database, including schema setup and functions for saving/retrieving user settings, weekly plans, and workout history.
    *   Tables include: `users`, `user_settings`, `weekly_plan`, `workout_history`.
*   **`ai_provider.py`**: A simple wrapper for interacting with the Google Gemini API.
*   **`muscle_anatomy.json`**: This file contains a basic model of muscle groups and sub-groups. It's used by the "Contextual Nudge" feature within Strength workouts to help the AI select specific muscles to emphasize or de-emphasize.
*   **`user_config.json`**: Stores user-specific configurations, primarily the Gemini API key, if saved via the UI. This file is created in the project root and is included in `.gitignore`.

## Running the Application

1.  **Ensure your virtual environment is activated** and your Gemini API key is configured (see "API Key Configuration" above).
2.  **Navigate to the project root directory** (where `app.py` is located).
3.  **Run the Flask development server:**
    ```bash
    flask run
    # Or, if 'flask run' does not work directly:
    # python app.py
    ```
4.  Open your web browser and go to: `http://127.0.0.1:5000/`

## Running Tests

1.  **Ensure your virtual environment is activated.**
2.  **Navigate to the project root directory.**
3.  **Run the unit tests:**
    ```bash
    python -m unittest discover -s tests -p "test_*.py"
    # Or simply, from the project root:
    # python -m unittest discover tests
    ```

[end of README.md]
