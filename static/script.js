// Script to handle form submission and display workout
document.addEventListener('DOMContentLoaded', function () {
    const workoutForm = document.getElementById('workoutForm');
    const statusMessage = document.getElementById('statusMessage');
    const errorMessage = document.getElementById('errorMessage');
    const workoutOutput = document.getElementById('workoutOutput');

    // Elements for User Settings
    const saveSettingsButton = document.getElementById('saveSettingsButton');
    const apiKeyInput = document.getElementById('geminiApiKey');
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
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData),
            });

            statusMessage.textContent = ''; // Clear generating message

            if (!response.ok) {
                const errorData = await response.json();
                errorMessage.textContent = errorData.error || 'An unknown error occurred.';
                return;
            }

            // Handle the streaming response
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let workoutText = '';

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split('\n').filter(line => line.trim() !== '');

                for (const line of lines) {
                    try {
                        const parsed = JSON.parse(line);
                        if (parsed.type === 'text') {
                            workoutText += parsed.text;
                            workoutOutput.textContent = workoutText; // Update in real-time
                        } else if (parsed.type === 'error') {
                            errorMessage.textContent = parsed.message;
                        }
                        // 'usage' type is ignored on the frontend for now
                    } catch (e) {
                        console.warn('Could not parse JSON chunk:', line);
                    }
                }
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
            const geminiApiKey = apiKeyInput.value;
            settingsMessage.textContent = 'Saving...';

            if (!geminiApiKey.trim()) {
                settingsMessage.textContent = 'API Key cannot be empty.';
                return;
            }

            try {
                const response = await fetch('/save_settings', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ geminiApiKey: geminiApiKey }),
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
