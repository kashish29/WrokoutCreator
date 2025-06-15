// Script to handle form submission and display workout
document.addEventListener('DOMContentLoaded', function () {
    const workoutForm = document.getElementById('workoutForm');
    const statusMessage = document.getElementById('statusMessage');
    const errorMessage = document.getElementById('errorMessage');
    const workoutOutput = document.getElementById('workoutOutput');

    // Elements for User Settings
    const saveSettingsButton = document.getElementById('saveSettingsButton');
    const apiKeyInput = document.getElementById('apiKey');
    const settingsMessage = document.getElementById('settingsMessage');

    workoutForm.addEventListener('submit', async function (event) {
        event.preventDefault(); // Prevent default page reload

        // Clear previous messages and output
        statusMessage.textContent = 'Generating your workout...';
        errorMessage.textContent = '';
        workoutOutput.textContent = '';

        // Get form data
        const goal = document.getElementById('goal').value;
        const experience = document.getElementById('experience').value;
        const focus = document.getElementById('focus').value;
        const userNotes = document.getElementById('userNotes').value; // Get userNotes

        const equipmentCheckboxes = document.querySelectorAll('input[name="equipment"]:checked');
        const equipment = Array.from(equipmentCheckboxes).map(cb => cb.value);

        if (equipment.length === 0) {
            errorMessage.textContent = 'Please select at least one piece of equipment.';
            statusMessage.textContent = '';
            return;
        }

        const formData = {
            goal: goal,
            experience: experience,
            equipment: equipment,
            focus: focus,
            userNotes: userNotes // Add userNotes to formData
        };

        try {
            const response = await fetch('/generate_workout', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData),
            });

            statusMessage.textContent = ''; // Clear generating message
            const data = await response.json();

            if (response.ok) {
                workoutOutput.textContent = data.workout;
            } else {
                errorMessage.textContent = data.error || 'An unknown error occurred.';
            }
        } catch (error) {
            console.error('Error during fetch:', error);
            statusMessage.textContent = '';
            errorMessage.textContent = 'A network error occurred. Please try again.';
        }
    });

    // Event listener for Save Settings button
    if (saveSettingsButton) { // Ensure the button is present
        saveSettingsButton.addEventListener('click', async function() {
            const apiKey = apiKeyInput.value;
            settingsMessage.textContent = 'Saving...';

            if (!apiKey.trim()) {
                settingsMessage.textContent = 'API Key cannot be empty.';
                return;
            }

            try {
                const response = await fetch('/save_settings', { // New endpoint
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ apiKey: apiKey }),
                });

                const data = await response.json();
                if (response.ok) {
                    settingsMessage.textContent = data.message || 'Settings saved successfully!';
                    apiKeyInput.value = ''; // Optionally clear the input
                } else {
                    settingsMessage.textContent = data.error || 'Failed to save settings.';
                }
            } catch (error) {
                console.error('Error saving settings:', error);
                settingsMessage.textContent = 'A network error occurred while saving settings.';
            }
        });
    }
});
