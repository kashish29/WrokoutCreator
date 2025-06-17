// Script to handle form submission and display workout
document.addEventListener('DOMContentLoaded', function () {
    const workoutForm = document.getElementById('workoutForm');
    const statusMessage = document.getElementById('statusMessage');
    const errorMessage = document.getElementById('errorMessage');
    const workoutOutput = document.getElementById('workoutOutput');
    const workoutHistory = document.getElementById('workoutHistory');
    const saveWorkoutButton = document.getElementById('saveWorkoutButton');

    let currentWorkoutData = null; // Variable to store the current workout

    // Elements for User Settings
    const saveSettingsButton = document.getElementById('saveSettingsButton');
    const apiKeyInput = document.getElementById('geminiApiKey');
    const settingsMessage = document.getElementById('settingsMessage');
    const strengthFreqInput = document.getElementById('strength_freq');
    const hiitFreqInput = document.getElementById('hiit_freq');
    const zone2FreqInput = document.getElementById('zone2_freq');
    const recoveryFreqInput = document.getElementById('recovery_freq');
    const focusRotationInput = document.getElementById('focus_rotation');
    const primaryGoalInput = document.getElementById('primary_goal');

    // Function to fetch and display workout history
    async function loadWorkoutHistory() {
        try {
            const response = await fetch('/get_workout_history?days=14');
            if (!response.ok) {
                workoutHistory.innerHTML = '<p>Could not load workout history.</p>';
                return;
            }
            const history = await response.json();
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
                    </div>
                `).join('');
                workoutHistory.innerHTML = historyHtml;
            }
        } catch (error) {
            console.error('Error fetching workout history:', error);
            workoutHistory.innerHTML = '<p>Error loading history.</p>';
        }
    }

    // Function to fetch and display user settings
    async function loadUserSettings() {
        try {
            const response = await fetch('/get_user_settings');
            if (!response.ok) return; // Don't populate if we can't fetch
            const settings = await response.json();
            strengthFreqInput.value = settings.strength_freq;
            hiitFreqInput.value = settings.hiit_freq;
            zone2FreqInput.value = settings.zone2_freq;
            recoveryFreqInput.value = settings.recovery_freq;
            focusRotationInput.value = settings.focus_rotation.join(', ');
            if (settings.primary_goal) {
                primaryGoalInput.value = settings.primary_goal;
            }
        } catch (error) {
            console.error('Error fetching user settings:', error);
        }
    }


    async function generateWorkout(event) {
        event.preventDefault();
        statusMessage.textContent = 'Generating your adaptive workout...';
        errorMessage.textContent = '';
        workoutOutput.textContent = '';
        saveWorkoutButton.style.display = 'none';
        currentWorkoutData = null;

        const experience = document.getElementById('experience').value;
        const userNotes = document.getElementById('userNotes').value;
        const equipmentCheckboxes = document.querySelectorAll('input[name="equipment"]:checked');
        const equipment = Array.from(equipmentCheckboxes).map(cb => cb.value);

        if (equipment.length === 0) {
            errorMessage.textContent = 'Please select at least one piece of equipment.';
            statusMessage.textContent = '';
            return;
        }

        const goal = document.getElementById('goal').value;
        const focus = document.getElementById('focus').value;

        const formData = {
            goal: goal,
            experience: experience,
            equipment: equipment,
            focus: focus,
            userNotes: userNotes,
        };

        try {
            const response = await fetch('/generate_workout', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData),
            });

            statusMessage.textContent = '';

            if (!response.ok) {
                const errorData = await response.json();
                errorMessage.textContent = errorData.error || 'An unknown error occurred.';
                return;
            }

            const data = await response.json();
            
            // Store the received workout data
            currentWorkoutData = {
                pillar: data.pillar,
                focus: data.focus,
                muscles_worked: data.muscles_worked,
                full_workout_text: data.workout_text
            };

            // Display the workout
            const workoutTitle = `## Today's Workout: ${data.pillar} - ${data.focus}\n\n`;
            workoutOutput.textContent = workoutTitle + data.workout_text;
            saveWorkoutButton.style.display = 'block'; // Show the save button

        } catch (error) {
            console.error('Error during workout generation:', error);
            statusMessage.textContent = '';
            errorMessage.textContent = 'A network error occurred. Please try again.';
        }
    }

    async function saveWorkout() {
        if (!currentWorkoutData) {
            errorMessage.textContent = 'No workout data to save.';
            return;
        }

        statusMessage.textContent = 'Saving workout...';
        errorMessage.textContent = '';

        try {
            console.log("Saving workout data:", currentWorkoutData); // Added for debugging
            const response = await fetch('/save_workout', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(currentWorkoutData),
            });

            const result = await response.json();
            if (response.ok) {
                statusMessage.textContent = result.message;
                // Refresh history to show the newly saved workout
                loadWorkoutHistory();
            } else {
                errorMessage.textContent = result.error || 'Failed to save workout.';
            }
        } catch (error) {
            console.error('Error saving workout:', error);
            errorMessage.textContent = 'A network error occurred while saving.';
        } finally {
            // Clear the message after a few seconds
            setTimeout(() => {
                statusMessage.textContent = '';
            }, 3000);
        }
    }

    workoutForm.addEventListener('submit', generateWorkout);
    saveWorkoutButton.addEventListener('click', saveWorkout);

    // Event listener for Save Settings button
    if (saveSettingsButton) { // Ensure the button is present
        saveSettingsButton.addEventListener('click', async function() {
            settingsMessage.textContent = 'Saving...';
            
            const settingsData = {
                strength_freq: parseInt(strengthFreqInput.value, 10),
                hiit_freq: parseInt(hiitFreqInput.value, 10),
                zone2_freq: parseInt(zone2FreqInput.value, 10),
                recovery_freq: parseInt(recoveryFreqInput.value, 10),
                focus_rotation: focusRotationInput.value.split(',').map(s => s.trim()).filter(Boolean),
                primary_goal: primaryGoalInput.value,
            };

            // Save API key separately
            const geminiApiKey = apiKeyInput.value;
            if (geminiApiKey.trim()) {
                 try {
                    const response = await fetch('/save_settings', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ geminiApiKey: geminiApiKey }),
                    });
                    const data = await response.json();
                    if (!response.ok) {
                        settingsMessage.textContent = data.error || 'Failed to save API key.';
                        return; // Stop if API key saving fails
                    }
                } catch (error) {
                    console.error('Error saving API key:', error);
                    settingsMessage.textContent = 'A network error occurred while saving API key.';
                    return;
                }
            }

            try {
                const response = await fetch('/save_user_settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(settingsData),
                });

                const data = await response.json();
                if (response.ok) {
                    settingsMessage.textContent = data.message || 'Settings saved successfully!';
                } else {
                    settingsMessage.textContent = data.error || 'Failed to save settings.';
                }
            } catch (error) {
                console.error('Error saving settings:', error);
                settingsMessage.textContent = 'A network error occurred while saving settings.';
            }
        });
    }

    // Initial data load
    loadUserSettings();
    loadWorkoutHistory();
});
