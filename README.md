# MVP AI Workout Generator

## Description
This project is an AI-powered workout generator that creates personalized training plans. It allows users to input their fitness goal, experience level, available equipment, desired workout focus, and any specific notes for the day. The application then leverages advanced prompting techniques with the OpenAI API (gpt-3.5-turbo or similar) to generate a detailed workout plan. It features an "Expert System" persona for more nuanced advice and "Contextual Nudges" to subtly guide muscle emphasis based on a predefined anatomy model.

## Features
- User inputs for:
    - Primary Goal (e.g., Build Muscle, Get Stronger, Lose Fat, Improve Endurance)
    - Experience Level (Beginner, Intermediate, Advanced)
    - Available Equipment (Dumbbells, Barbell, Kettlebell, Resistance Bands, Bodyweight only)
    - Workout Focus for Today (Upper Body, Lower Body, Full Body, Push, Pull, Legs)
    - Optional User Notes (e.g., 'My left shoulder feels a bit pinchy', 'Focus on arms')
- Advanced AI-generated workout plans using an "Expert System" persona for nuanced advice.
- "Contextual Nudges" to intelligently emphasize specific muscle sub-groups based on `muscle_anatomy.json`.
- OpenAI API Key configuration via the User Settings in the UI (recommended) or environment variables.
- Simple web interface to input preferences, save settings, and view the workout.
- Workout plans displayed in clean markdown format.

## Technology Stack
- **Backend**: Python, Flask
- **AI Service**: OpenAI API (gpt-3.5-turbo)
- **Frontend**: HTML, CSS (basic), JavaScript
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
    This application requires an OpenAI API key. You have a few options:

    *   **Using the UI (Recommended):**
        1.  Run the application (see "Running the Application" below).
        2.  Open the web interface.
        3.  Scroll down to "User Settings".
        4.  Enter your OpenAI API Key and click "Save Settings".
        5.  The key will be saved to a `user_config.json` file in the project root. This file is automatically added to `.gitignore` and should not be committed to version control.

    *   **Using a `.env` file (Fallback):**
        If `user_config.json` does not exist or does not contain an API key, the application will fall back to using an environment variable.
        The project uses `python-dotenv` to load environment variables from a `.env` file.
        Create a file named `.env` in the project root directory (alongside `app.py`).
        Add your API key to this file:
        ```env
        OPENAI_API_KEY="your_openai_api_key_here"
        ```
        Ensure `.env` is listed in your `.gitignore` file.

    *   **Setting directly in your shell (Fallback):**
        As another fallback, you can set the environment variable directly in your terminal session before running the app.
        -   On macOS and Linux: `export OPENAI_API_KEY="your_openai_api_key_here"`
        -   On Windows (cmd.exe): `set OPENAI_API_KEY=your_openai_api_key_here`
        -   On Windows (PowerShell): `$env:OPENAI_API_KEY="your_openai_api_key_here"`

## How to Use (Interface)
1.  Launch the application.
2.  Fill in your:
    *   **Primary Goal**
    *   **Experience Level**
    *   **Available Equipment** (select one or more)
    *   **Workout Focus for Today**
    *   **Any specific focus or muscles to avoid today? (Optional):** Use this field for any notes, like minor aches or specific short-term goals (e.g., "Left knee is a bit sore, avoid direct squats" or "Really want to hit biceps hard today").
3.  Click "Generate Workout".
4.  Your personalized workout plan will appear below.
5.  If you need to set or update your OpenAI API key, use the "User Settings" section.

## Running the Application

1.  **Ensure your virtual environment is activated** and your OpenAI API key is configured (see "API Key Configuration" above).
2.  **Navigate to the project root directory** (where `app.py` is located).
3.  **Run the Flask development server:**
    ```bash
    flask run
    # Or, if 'flask run' does not work directly (e.g., if flask is not in PATH or app not auto-detected):
    # python app.py
    ```
4.  Open your web browser and go to: `http://127.0.0.1:5000/`

## Backend Details
*   **`muscle_anatomy.json`**: This file contains a basic model of muscle groups and sub-groups. It's used by the "Contextual Nudge" feature to help the AI select specific muscles to emphasize or de-emphasize within the broader `focus` selected by the user.
*   **`/save_settings` route**: This POST endpoint (`app.py`) handles saving the OpenAI API key entered in the UI to the `user_config.json` file.
*   **`user_config.json`**: Stores user-specific configurations, primarily the OpenAI API key. This file is created in the project root and is included in `.gitignore`.

## Running Tests

1.  **Ensure your virtual environment is activated.**
2.  **Navigate to the project root directory.**
3.  **Run the unit tests:**
    ```bash
    python -m unittest discover -s tests -p "test_*.py"
    # Or simply, from the project root:
    # python -m unittest discover tests
    ```
