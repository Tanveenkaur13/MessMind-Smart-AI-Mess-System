async function getPrediction() {
    const data = {
        day: document.getElementById('day').value,
        meal: document.getElementById('meal').value,
        pop: document.getElementById('menu').value
    };

    try {
        const response = await fetch('/predict', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        const res = await response.json();

        if (!response.ok) {
            alert(res.message || 'Forecast failed. Please check the server log.');
            return;
        }

        document.getElementById('pred-val').innerText = res.plates;
        document.getElementById('live-count').innerText = res.verified;

        const tbody = document.getElementById('history-body');
        tbody.innerHTML = res.history.map(row => `
            <tr>
                <td>${row.time}</td>
                <td>${row.meal}</td>
                <td style="color: #6366f1;">${row.predicted}</td>
                <td style="color: #10b981;">${row.verified}</td>
            </tr>
        `).join('');
    } catch (error) {
        alert('Forecast request failed: ' + error.message);
    }
}

async function mark(mealName, statusChoice) {
    const res = await fetch('/submit_attendance', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ meal: mealName, status: statusChoice })
    });
    if(res.ok) {
        document.getElementById('msg-' + mealName).style.display = 'block';
    }
}

// Menu data object (will be populated with actual menu)
const menuData = {
    0: { day: "Monday", Breakfast: "", Lunch: "", Dinner: "", Sweet: "" },
    1: { day: "Tuesday", Breakfast: "", Lunch: "", Dinner: "", Sweet: "" },
    2: { day: "Wednesday", Breakfast: "", Lunch: "", Dinner: "", Sweet: "" },
    3: { day: "Thursday", Breakfast: "", Lunch: "", Dinner: "", Sweet: "" },
    4: { day: "Friday", Breakfast: "", Lunch: "", Dinner: "", Sweet: "" },
    5: { day: "Saturday", Breakfast: "", Lunch: "", Dinner: "", Sweet: "" },
    6: { day: "Sunday", Breakfast: "", Lunch: "", Dinner: "", Sweet: "" }
};

// Initialize menu data from server response
document.addEventListener('DOMContentLoaded', function() {
    // Fetch menu data from the manager route or set it directly
    const daySelect = document.getElementById('day');
    daySelect.addEventListener('change', function() {
        showMenuParchment(this.value);
    });
});

// Show parchment letter with menu
function showMenuParchment(dayIndex) {
    const day = parseInt(dayIndex);
    const dayNames = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    
    // For now, we'll fetch the menu from the visible menu cards in the sidebar
    const menuCards = document.querySelectorAll('.menu-card');
    const selectedCard = menuCards[day];
    
    if (selectedCard) {
        const mealInfo = selectedCard.innerText;
        const lines = mealInfo.split('\n');
        
        let parchmentHTML = `<h2>${dayNames[day]} Menu</h2>`;
        
        // Extract meal information
        for (let i = 1; i < lines.length; i++) {
            const line = lines[i].trim();
            if (line) {
                parchmentHTML += `<div class="menu-item">${line}</div>`;
            }
        }
        
        document.getElementById('parchment-content').innerHTML = parchmentHTML;
        document.getElementById('menu-modal').classList.add('active');
    }
}

// Close parchment letter
function closeMenuParchment() {
    document.getElementById('menu-modal').classList.remove('active');
}

// Close modal when clicking outside
document.addEventListener('click', function(event) {
    const modal = document.getElementById('menu-modal');
    if (event.target === modal) {
        modal.classList.remove('active');
    }
});