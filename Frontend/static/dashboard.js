// dashboard.js: Handles dashboard logic for CTF Arena

document.addEventListener('DOMContentLoaded', async function() {
    // Check if user is logged in
    const token = localStorage.getItem('access_token');
    const user = JSON.parse(localStorage.getItem('user') || 'null');
    if (!token || !user) {
        window.location.href = '/';
        return;
    }
    document.getElementById('userWelcome').textContent = `Welcome, ${user.username}`;
    document.getElementById('logoutBtn').addEventListener('click', function() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
        window.location.href = '/';
    });
    // Fetch challenges
    try {
        const response = await fetch('/api/challenges', {
            headers: { 'Authorization': 'Bearer ' + token }
        });
        const data = await response.json();
        if (response.ok) {
            renderChallenges(data);
        } else {
            document.getElementById('challengesList').innerHTML = '<div class="col-12 text-danger">Failed to load challenges.</div>';
        }
    } catch (err) {
        document.getElementById('challengesList').innerHTML = '<div class="col-12 text-danger">Failed to load challenges.</div>';
    }
});

function renderChallenges(challenges) {
    const list = document.getElementById('challengesList');
    if (!challenges.length) {
        list.innerHTML = '<div class="col-12">No challenges available.</div>';
        return;
    }
    list.innerHTML = '';
    challenges.forEach(chal => {
        const card = document.createElement('div');
        card.className = 'col-md-4';
        card.innerHTML = `
            <div class="card h-100 shadow">
                <div class="card-body">
                    <h5 class="card-title">${chal.name}</h5>
                    <p class="card-text">${chal.description}</p>
                    <p class="card-text"><b>Type:</b> ${chal.type}</p>
                    <a href="${chal.file_path}" class="btn btn-outline-light mb-2" download>Download</a>
                    <form class="submit-flag-form">
                        <input type="hidden" name="challenge_id" value="${chal.id}">
                        <div class="input-group mb-2">
                            <input type="text" class="form-control" name="flag" placeholder="Submit flag" required>
                            <button class="btn btn-success" type="submit">Submit</button>
                        </div>
                        <div class="flag-result text-danger small" style="display:none;"></div>
                    </form>
                </div>
            </div>
        `;
        // Add flag submission logic
        card.querySelector('.submit-flag-form').addEventListener('submit', async function(e) {
            e.preventDefault();
            const flag = this.flag.value;
            const challenge_id = this.challenge_id.value;
            const resultDiv = this.querySelector('.flag-result');
            try {
                const response = await fetch('/api/challenges/' + challenge_id + '/submit', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + localStorage.getItem('access_token')
                    },
                    body: JSON.stringify({ flag })
                });
                const data = await response.json();
                if (response.ok) {
                    resultDiv.textContent = 'Correct!';
                    resultDiv.classList.remove('text-danger');
                    resultDiv.classList.add('text-success');
                } else {
                    resultDiv.textContent = data.detail || 'Incorrect flag.';
                    resultDiv.classList.remove('text-success');
                    resultDiv.classList.add('text-danger');
                }
                resultDiv.style.display = 'block';
            } catch (err) {
                resultDiv.textContent = 'Submission failed.';
                resultDiv.classList.remove('text-success');
                resultDiv.classList.add('text-danger');
                resultDiv.style.display = 'block';
            }
        });
        list.appendChild(card);
    });
}
