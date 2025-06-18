// Script to handle form submission and display workout
document.addEventListener('DOMContentLoaded', function () {
    // --- DOM Element References ---
    const workoutForm = document.getElementById('workoutForm');
    const statusMessage = document.getElementById('statusMessage');
    const errorMessage = document.getElementById('errorMessage');
    const workoutOutput = document.getElementById('workoutOutput');
    const workoutHistory = document.getElementById('workoutHistory');
    const saveWorkoutButton = document.getElementById('saveWorkoutButton');
    const weeklyPlanDisplay = document.getElementById('weeklyPlanDisplay'); // Added

    // Elements for User Settings
    const saveSettingsButton = document.getElementById('saveSettingsButton');
    const apiKeyInput = document.getElementById('geminiApiKey');
    const settingsMessage = document.getElementById('settingsMessage');
    const strengthFreqInput = document.getElementById('strength_freq');
    const hiitFreqInput = document.getElementById('hiit_freq');
    const zone2FreqInput = document.getElementById('zone2_freq');
    const recoveryFreqInput = document.getElementById('recovery_freq');
    const stabilityFreqInput = document.getElementById('stability_freq'); // Added
    const focusRotationInput = document.getElementById('focus_rotation');
    const primaryGoalInput = document.getElementById('primary_goal');
    const aiModelIdSelect = document.getElementById('ai_model_id');
    const workoutDurationPreferenceSelect = document.getElementById('workout_duration_preference');
    const themeToggleButton = document.getElementById('themeToggle');

    // --- Global Variables / State ---
    let currentWorkoutData = null;

    // --- API Functions ---
    async function loadWorkoutHistoryRequest() {
        const response = await fetch('/get_workout_history?days=14');
        if (!response.ok) {
            throw new Error('Could not load workout history.');
        }
        return response.json();
    }

    async function loadWeeklyPlanRequest() {
        const response = await fetch('/get_current_weekly_plan');
        if (!response.ok) {
            throw new Error('Could not load weekly plan.');
        }
        return response.json();
    }

    async function loadUserSettingsRequest() {
        const response = await fetch('/get_user_settings');
        if (!response.ok) {
            throw new Error('Could not load user settings.');
        }
        return response.json();
    }

    async function generateWorkoutRequest(formData) {
        const response = await fetch('/generate_workout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData),
        });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'An unknown error occurred during workout generation.');
        }
        return response.json();
    }

    async function saveWorkoutRequest(workoutData) {
        const response = await fetch('/save_workout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(workoutData),
        });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to save workout.');
        }
        return response.json();
    }

    async function saveGeminiApiKeyRequest(apiKey) {
        const response = await fetch('/save_settings', { // Assuming this is the endpoint for API key
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ geminiApiKey: apiKey }),
        });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to save API key.');
        }
        return response.json();
    }

    async function saveUserSettingsRequest(settingsData) {
        const response = await fetch('/save_user_settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settingsData),
        });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to save user settings.');
        }
        return response.json();
    }

    async function deleteWorkoutRequest(workoutId) {
        const response = await fetch(`/delete_workout/${workoutId}`, {
            method: 'DELETE',
        });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to delete workout.');
        }
        return response.json();
    }

    // --- UI Update Functions ---
    function displayStatusMessage(message) {
        statusMessage.textContent = message;
    }

    function displayErrorMessage(message) {
        errorMessage.textContent = message;
    }

    function displaySettingsMessage(message) {
        settingsMessage.textContent = message;
    }

    function clearMessages() {
        statusMessage.textContent = '';
        errorMessage.textContent = '';
    }

    function clearSettingsMessage() {
        settingsMessage.textContent = '';
    }

    function toggleSaveWorkoutButton(show) {
        saveWorkoutButton.style.display = show ? 'block' : 'none';
    }

    function clearWorkoutOutput() {
        workoutOutput.innerHTML = ''; // Use innerHTML for markdown, textContent otherwise
    }

    function displayWorkoutOutput(data) {
        const workoutTitle = `## Today's Workout: ${data.pillar} - ${data.focus}\n\n`;
        workoutOutput.innerHTML = marked.parse(workoutTitle + data.workout_text);
    }

    function updateWorkoutHistoryDisplay(history) {
        if (history.length === 0) {
            workoutHistory.innerHTML = '<p>No recent workouts found.</p>';
        } else {
            const historyHtml = history.map(item => `
                <div class="history-item">
                    <strong>${new Date(item.workout_date).toLocaleDateString()} - ${item.pillar}: ${item.focus}</strong>
                    <p>Muscles: ${item.muscles_worked.join(', ') || 'N/A'}</p>
                    <details>
                        <summary>View Full Workout</summary>
                        <pre>${item.full_workout_text}</pre>
                    </details>
                    <button class="delete-workout-btn" data-id="${item.id}">Delete Workout</button>
                </div>
            `).join('');
            workoutHistory.innerHTML = historyHtml;

           // Add event listeners to the new delete buttons
           document.querySelectorAll('.delete-workout-btn').forEach(button => {
               button.addEventListener('click', handleDeleteWorkoutClick);
           });
        }
    }

    function populateUserSettingsForm(settings) {
        strengthFreqInput.value = settings.strength_freq;
        hiitFreqInput.value = settings.hiit_freq;
        zone2FreqInput.value = settings.zone2_freq;
        recoveryFreqInput.value = settings.recovery_freq;
        if (stabilityFreqInput) stabilityFreqInput.value = settings.stability_freq; // Added
        focusRotationInput.value = settings.focus_rotation.join(', ');
        if (settings.primary_goal) {
            primaryGoalInput.value = settings.primary_goal;
        }
        // Populate new fields, providing defaults if not present
        aiModelIdSelect.value = settings.ai_model_id || 'gemini-1.5-flash-latest';
        workoutDurationPreferenceSelect.value = settings.workout_duration_preference || 'Any';
    }

    function displayWeeklyPlan(plan) {
        if (!weeklyPlanDisplay) return;

        if (!plan || plan.length === 0) {
            weeklyPlanDisplay.innerHTML = '<p>No weekly plan found for the current week. Save your settings to generate one.</p>';
            return;
        }

        // Sort by day_of_week just in case
        plan.sort((a, b) => a.day_of_week - b.day_of_week);

        const days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
        let html = '<ul>';
        plan.forEach(item => {
            html += `<li><strong>${days[item.day_of_week] || 'Unknown Day'}:</strong> ${item.pillar_focus} (${item.status})</li>`;
        });
        html += '</ul>';
        weeklyPlanDisplay.innerHTML = html;
    }

    // --- Event Handlers & Logic ---
    async function handleWorkoutFormSubmit(event) {
        event.preventDefault();
        clearMessages();
        displayStatusMessage('Generating your adaptive workout...');
        clearWorkoutOutput();
        toggleSaveWorkoutButton(false);
        currentWorkoutData = null;

        const experience = document.getElementById('experience').value;
        const userNotes = document.getElementById('userNotes').value;
        const equipmentCheckboxes = document.querySelectorAll('input[name="equipment"]:checked');
        const equipment = Array.from(equipmentCheckboxes).map(cb => cb.value);
        const workoutPillar = document.getElementById('workout_pillar').value; // Added
        const strengthStyle = document.getElementById('goal').value; // Renamed for clarity in JS, maps to 'goal' in HTML
        const focus = document.getElementById('focus').value;


        if (equipment.length === 0) {
            displayErrorMessage('Please select at least one piece of equipment.');
            displayStatusMessage('');
            return;
        }

        const formData = {
            workout_pillar: workoutPillar, // Added
            strength_style: strengthStyle, // Renamed from goal for backend clarity
            experience: experience,
            equipment: equipment,
            focus: focus,
            userNotes: userNotes,
        };

        try {
            const data = await generateWorkoutRequest(formData);
            currentWorkoutData = {
                pillar: data.pillar,
                focus: data.focus,
                muscles_worked: data.muscles_worked,
                full_workout_text: data.workout_text
            };
            displayWorkoutOutput(data);
            toggleSaveWorkoutButton(true);
            displayStatusMessage(''); // Clear "Generating..."
        } catch (error) {
            console.error('Error during workout generation:', error);
            displayErrorMessage(error.message || 'A network error occurred. Please try again.');
            displayStatusMessage('');
        }
    }

    async function handleSaveWorkoutClick() {
        if (!currentWorkoutData) {
            displayErrorMessage('No workout data to save.');
            return;
        }
        clearMessages();
        displayStatusMessage('Saving workout...');

        try {
            console.log("Saving workout data:", currentWorkoutData);
            const result = await saveWorkoutRequest(currentWorkoutData);
            displayStatusMessage(result.message);
            await fetchAndDisplayWorkoutHistory(); // Refresh history
        } catch (error) {
            console.error('Error saving workout:', error);
            displayErrorMessage(error.message || 'A network error occurred while saving.');
        } finally {
            setTimeout(() => {
                displayStatusMessage('');
            }, 3000);
        }
    }

    async function handleSaveSettingsClick() {
        displaySettingsMessage('Saving...');

        const settingsData = {
            strength_freq: parseInt(strengthFreqInput.value, 10),
            hiit_freq: parseInt(hiitFreqInput.value, 10),
            zone2_freq: parseInt(zone2FreqInput.value, 10),
            recovery_freq: parseInt(recoveryFreqInput.value, 10),
            stability_freq: parseInt(stabilityFreqInput.value, 10), // Added
            focus_rotation: focusRotationInput.value.split(',').map(s => s.trim()).filter(Boolean),
            primary_goal: primaryGoalInput.value,
            ai_model_id: aiModelIdSelect.value,
            workout_duration_preference: workoutDurationPreferenceSelect.value,
        };

        const geminiApiKey = apiKeyInput.value;
        if (geminiApiKey.trim()) {
             try {
                await saveGeminiApiKeyRequest(geminiApiKey);
                // No specific message here, or could be part of a combined message
             } catch (error) {
                console.error('Error saving API key:', error);
                displaySettingsMessage(error.message || 'A network error occurred while saving API key.');
                return; // Stop if API key saving fails
            }
        }

        try {
            const result = await saveUserSettingsRequest(settingsData);
            displaySettingsMessage(result.message || 'Settings saved successfully!');
        } catch (error) {
            console.error('Error saving settings:', error);
            displaySettingsMessage(error.message || 'A network error occurred while saving settings.');
        }
    }

   async function handleDeleteWorkoutClick(event) {
       const workoutId = event.target.dataset.id;
       if (!confirm('Are you sure you want to delete this workout?')) {
           return;
       }

       clearMessages();
       displayStatusMessage('Deleting workout...');

       try {
           const result = await deleteWorkoutRequest(workoutId);
           displayStatusMessage(result.message);
           await fetchAndDisplayWorkoutHistory(); // Refresh history
       } catch (error) {
           console.error('Error deleting workout:', error);
           displayErrorMessage(error.message || 'A network error occurred while deleting.');
       } finally {
           setTimeout(() => {
               displayStatusMessage('');
           }, 3000);
       }
   }

    // --- Theme Management ---
    function applyTheme(theme) {
        document.body.classList.toggle('dark-mode', theme === 'dark');
        if (themeToggleButton) {
            themeToggleButton.textContent = theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode';
        }
        localStorage.setItem('appTheme', theme);
    }

    // --- Initialization Functions ---
    async function fetchAndDisplayWorkoutHistory() {
        try {
            const history = await loadWorkoutHistoryRequest();
            updateWorkoutHistoryDisplay(history);
        } catch (error) {
            console.error('Error fetching workout history:', error);
            if (workoutHistory) workoutHistory.innerHTML = `<p>${error.message}</p>`;
        }
    }

    async function fetchAndPopulateUserSettings() {
        try {
            const settings = await loadUserSettingsRequest();
            populateUserSettingsForm(settings);
        } catch (error) {
            console.error('Error fetching user settings:', error);
            // Optionally display an error message in the settings area
        }
    }

    async function fetchAndDisplayWeeklyPlan() {
        if (!weeklyPlanDisplay) return; // Don't try if the element doesn't exist
        try {
            weeklyPlanDisplay.innerHTML = '<p>Loading weekly plan...</p>'; // Initial message
            const plan = await loadWeeklyPlanRequest();
            displayWeeklyPlan(plan);
        } catch (error) {
            console.error('Error fetching weekly plan:', error);
            if (weeklyPlanDisplay) weeklyPlanDisplay.innerHTML = `<p>${error.message}</p>`;
        }
    }

    // --- Event Listeners ---
    workoutForm.addEventListener('submit', handleWorkoutFormSubmit);
    saveWorkoutButton.addEventListener('click', handleSaveWorkoutClick);
    if (saveSettingsButton) {
        saveSettingsButton.addEventListener('click', handleSaveSettingsClick);
    }
    if (themeToggleButton) {
        themeToggleButton.addEventListener('click', () => {
            const currentTheme = document.body.classList.contains('dark-mode') ? 'dark' : 'light';
            if (currentTheme === 'dark') {
                applyTheme('light');
            } else {
                applyTheme('dark');
            }
        });
    }

    // --- Initial Data Load ---
    fetchAndPopulateUserSettings();
    fetchAndDisplayWorkoutHistory();
    fetchAndDisplayWeeklyPlan(); // Added

    const savedTheme = localStorage.getItem('appTheme') || 'light'; // Default to light
    applyTheme(savedTheme);
});
