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
    // Add Challenge Modal logic
    var addChallengeBtn = document.getElementById('addChallengeBtn');
    var addChallengeModal = new bootstrap.Modal(document.getElementById('addChallengeModal'));
    addChallengeBtn.addEventListener('click', function() {
        addChallengeModal.show();
    });
    var addChallengeForm = document.getElementById('addChallengeForm');
    addChallengeForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        var errorDiv = document.getElementById('addChallengeError');
        errorDiv.style.display = 'none';
        const token = localStorage.getItem('access_token');
        const formData = new FormData(addChallengeForm);
        try {
            const response = await fetch('/api/challenges', {
                method: 'POST',
                headers: {
                    'Authorization': 'Bearer ' + token
                },
                body: formData
            });
            const data = await response.json();
            if (response.ok) {
                addChallengeModal.hide();
                addChallengeForm.reset();
                // Refresh challenges list
                location.reload();
            } else {
                errorDiv.textContent = data.detail || 'Failed to add challenge.';
                errorDiv.style.display = 'block';
            }
        } catch (err) {
            errorDiv.textContent = 'Failed to add challenge.';
            errorDiv.style.display = 'block';
        }
    });
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
                    <button class="btn btn-outline-light mb-2 download-btn" data-challenge-id="${chal.id}" data-challenge-name="${chal.name}">Download</button>
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
        // Download button logic
        card.querySelector('.download-btn').addEventListener('click', async function() {
            const challengeId = this.getAttribute('data-challenge-id');
            const challengeName = this.getAttribute('data-challenge-name');
            const token = localStorage.getItem('access_token');
            try {
                const response = await fetch(`/api/challenges/${challengeId}/download`, {
                    headers: { 'Authorization': 'Bearer ' + token }
                });
                if (!response.ok) {
                    alert('Failed to download file.');
                    return;
                }
                const disposition = response.headers.get('Content-Disposition');
                let filename = challengeName;
                if (disposition && disposition.indexOf('filename=') !== -1) {
                    filename = disposition.split('filename=')[1].replace(/"/g, '').trim();
                }
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                setTimeout(() => {
                    window.URL.revokeObjectURL(url);
                    a.remove();
                }, 100);
            } catch (err) {
                alert('Download failed.');
            }
        });
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
