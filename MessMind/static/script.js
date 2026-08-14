// Animate a stat number counting up from its current value to `target`
function animateCount(el, target, duration = 600) {
    const start = parseFloat(el.textContent) || 0;
    if (start === target) return;
    const startTime = performance.now();
    function tick(now) {
        const progress = Math.min((now - startTime) / duration, 1);
        el.textContent = Math.round(start + (target - start) * progress);
        if (progress < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
}

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

        animateCount(document.getElementById('pred-val'), res.plates);
        animateCount(document.getElementById('live-count'), res.verified);

        const tbody = document.getElementById('history-body');
        tbody.innerHTML = res.history.map((row, i) => `
            <tr style="animation: fadeIn 0.3s ease both; animation-delay: ${Math.min(i * 0.03, 0.3)}s;">
                <td>${row.time}</td>
                <td>${row.meal}</td>
                <td style="color: #f97316;">${row.predicted}</td>
                <td style="color: #16a34a;">${row.verified}</td>
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
    // Fetch menu data from the manager route or set it directly.
    // Not every page that includes this script has a #day select (e.g. the
    // student portal doesn't), so guard before attaching the listener.
    const daySelect = document.getElementById('day');
    if (daySelect) {
        daySelect.addEventListener('change', function() {
            showMenuParchment(this.value);
        });
    }

    // Give the manager dashboard's "Live Verified" number a count-up on load
    // instead of just appearing with its server-rendered value.
    const liveCountEl = document.getElementById('live-count');
    if (liveCountEl) {
        const target = parseInt(liveCountEl.textContent, 10) || 0;
        liveCountEl.textContent = '0';
        animateCount(liveCountEl, target, 800);
    }
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