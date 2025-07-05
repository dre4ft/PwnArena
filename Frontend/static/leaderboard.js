// leaderboard.js: Fetch and display leaderboard

document.addEventListener('DOMContentLoaded', async function() {
    // Pass JWT as cookie for backend access
    const token = localStorage.getItem('access_token');
    if (token) {
        document.cookie = "access_token=" + token + "; path=/";
    }
    try {
        const response = await fetch('/api/leaderboard');
        if (!response.ok) {
            document.getElementById('leaderboardTableBody').innerHTML = '<tr><td colspan="3" class="text-danger">Failed to load leaderboard.</td></tr>';
            return;
        }
        const data = await response.json();
        renderLeaderboard(data);
    } catch (err) {
        document.getElementById('leaderboardTableBody').innerHTML = '<tr><td colspan="3" class="text-danger">Failed to load leaderboard.</td></tr>';
    }
});

function renderLeaderboard(entries) {
    const tbody = document.getElementById('leaderboardTableBody');
    if (!entries.length) {
        tbody.innerHTML = '<tr><td colspan="3">No solves yet.</td></tr>';
        return;
    }
    tbody.innerHTML = '';
    entries.forEach((entry, idx) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <th scope="row">${idx + 1}</th>
            <td>${entry.username}</td>
            <td>${entry.solves}</td>
        `;
        tbody.appendChild(tr);
    });
}
