# MVP AI Workout Generator

## Description
This project is a Minimum Viable Product (MVP) for an AI-powered workout generator. It allows users to input their fitness goal, experience level, available equipment, and desired workout focus for the day. Based on these inputs, it leverages the OpenAI API (specifically, gpt-3.5-turbo) to generate a personalized workout plan, which is then displayed to the user as raw markdown.

## Features
- User inputs for:
    - Primary Goal (e.g., Build Muscle, Get Stronger)
    - Experience Level (Beginner, Intermediate, Advanced)
    - Available Equipment (Dumbbells, Barbell, Kettlebell, Resistance Bands, Bodyweight only)
    - Workout Focus for Today (Upper Body, Lower Body, Full Body)
- AI-generated workout plans via OpenAI API.
- Simple web interface to input preferences and view the workout.
- Raw markdown display for the generated workout.

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
    ```

2.  **Navigate to the application directory:**
    The main application code is within the `mvp_workout_generator` subdirectory.
    ```bash
    cd mvp_workout_generator
    # If you are already in the root workspace, use `cd mvp_workout_generator`
    # If the README is in the root, and app is in mvp_workout_generator:
    # All commands below assume you are in the directory containing `app.py`
    # i.e., inside `mvp_workout_generator` unless specified.
    ```
    *Correction: The following commands should mostly be run from the project root (the directory containing `mvp_workout_generator/`), especially for venv and tests.*

3.  **Create a virtual environment:**
    It is highly recommended to use a virtual environment. From the project root directory (the one containing the `mvp_workout_generator` folder):
    ```bash
    python3 -m venv venv
    ```

4.  **Activate the virtual environment:**
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

5.  **Install dependencies:**
    From the project root directory, ensure your virtual environment is activated:
    ```bash
    pip install -r mvp_workout_generator/requirements.txt
    ```

6.  **Set up Environment Variables:**
    This application requires an OpenAI API key.
    -   **Using a `.env` file (recommended for local development):**
        The project uses `python-dotenv` to load environment variables from a `.env` file.
        Create a file named `.env` inside the `mvp_workout_generator` directory (alongside `app.py`).
        Add your API key to this file:
        ```
        OPENAI_API_KEY="your_openai_api_key_here"
        ```
    -   **Setting directly in your shell (alternative):**
        You can also set the environment variable directly in your terminal session before running the app.
        -   On macOS and Linux:
            ```bash
            export OPENAI_API_KEY="your_openai_api_key_here"
            ```
        -   On Windows (cmd.exe):
            ```bash
            set OPENAI_API_KEY=your_openai_api_key_here
            ```
        -   On Windows (PowerShell):
            ```powershell
            $env:OPENAI_API_KEY="your_openai_api_key_here"
            ```

## Running the Application

1.  **Ensure your virtual environment is activated** and the `OPENAI_API_KEY` is set (e.g., via `.env` file in `mvp_workout_generator/` or shell export).
2.  **Navigate to the application directory:**
    If you are in the project root, change to the application directory:
    ```bash
    cd mvp_workout_generator
    ```
3.  **Run the Flask development server:**
    ```bash
    flask run
    # Or, if flask run does not work directly:
    # python app.py
    ```
4.  Open your web browser and go to: `http://127.0.0.1:5000/`

## Running Tests

1.  **Ensure your virtual environment is activated.**
2.  **Navigate to the project root directory** (the directory that contains the `mvp_workout_generator` folder and the main `README.md`).
3.  **Run the unit tests:**
    ```bash
    python -m unittest discover -s mvp_workout_generator/tests -p "test_*.py"
    ```
    Alternatively, if you are inside the `mvp_workout_generator` directory:
    ```bash
    python -m unittest discover tests
    ```
