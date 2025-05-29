document.addEventListener('DOMContentLoaded', () => {
    const fetchDataButton = document.getElementById('fetchDataBtn');
    const fetchProtectedDataButton = document.getElementById('fetchProtectedDataBtn');
    const dataDisplay = document.getElementById('dataDisplay');
    const messageDisplay = document.getElementById('messageDisplay');

    // Function to display messages
    function displayMessage(message, isError = false) {
        messageDisplay.textContent = message;
        messageDisplay.style.color = isError ? '#dc3545' : '#28a745';
    }

    // Function to clear data display
    function clearDisplay() {
        dataDisplay.textContent = '';
        messageDisplay.textContent = '';
    }

    // Function to simulate user login and get a token (for demonstration)
    function simulateLogin() {
        // In a real app, this would be an actual API call to your /api/login endpoint
        // and you'd store the received JWT token.
        // For now, let's use a dummy token or prompt the user.
        alert("Please log in to get a token for protected routes.\nFor this demo, imagine a token is now in localStorage.");
        localStorage.setItem('jwt_token', 'your_dummy_jwt_token_here'); // Replace with a real token in a real app
    }

    // Event listener for fetching public data
    if (fetchDataButton) {
        fetchDataButton.addEventListener('click', async () => {
            clearDisplay();
            displayMessage('Fetching public data...');
            try {
                const response = await fetch('/api/data');
                const data = await response.json();
                if (response.ok) {
                    dataDisplay.textContent = JSON.stringify(data, null, 2);
                    displayMessage('Public data fetched successfully!');
                } else {
                    displayMessage(`Error fetching public data: ${data.error || response.statusText}`, true);
                }
            } catch (error) {
                displayMessage(`Network error fetching public data: ${error.message}`, true);
            }
        });
    }

    // Event listener for fetching protected data
    if (fetchProtectedDataButton) {
        fetchProtectedDataButton.addEventListener('click', async () => {
            clearDisplay();
            const token = localStorage.getItem('jwt_token');
            if (!token) {
                displayMessage('No JWT token found. Please log in first.', true);
                simulateLogin(); // Prompt for login
                return;
            }

            displayMessage('Fetching protected data...');
            try {
                const response = await fetch('/api/protected_data', {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                const data = await response.json();
                if (response.ok) {
                    dataDisplay.textContent = JSON.stringify(data, null, 2);
                    displayMessage('Protected data fetched successfully!');
                } else {
                    displayMessage(`Error fetching protected data: ${data.error || response.statusText}`, true);
                }
            } catch (error) {
                displayMessage(`Network error fetching protected data: ${error.message}`, true);
            }
        });
    }

    // Optional: Add a simple welcome message
    console.log("Script loaded and ready!");
});