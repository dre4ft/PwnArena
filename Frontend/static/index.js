// Toggle hidden menu
document.addEventListener('DOMContentLoaded', function() {
        var authModal = new bootstrap.Modal(document.getElementById('authModal'));
        document.getElementById('showAuthModalBtn').addEventListener('click', function() {
          authModal.show();
        });
        // Registration form password match logic and API call
        var registerForm = document.getElementById('registerForm');
        registerForm.addEventListener('submit', async function(e) {
          var pw1 = document.getElementById('registerPassword').value;
          var pw2 = document.getElementById('registerPassword2').value;
          var username = document.getElementById('registerUsername').value;
          var errorDiv = document.getElementById('registerError');
          if (pw1 !== pw2) {
            e.preventDefault();
            errorDiv.textContent = "Passwords do not match.";
            errorDiv.style.display = 'block';
            return;
          } else {
            errorDiv.style.display = 'none';
          }
          e.preventDefault();
          try {
            const response = await fetch('/api/register', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ username: username, password: pw1 })
            });
            const data = await response.json();
            if (response.ok) {
              errorDiv.style.display = 'none';
              alert('Registration successful! You can now log in.');
              document.getElementById('login-tab').click();
              registerForm.reset();
            } else {
              errorDiv.textContent = data.detail || 'Registration failed.';
              errorDiv.style.display = 'block';
            }
          } catch (err) {
            errorDiv.textContent = 'Registration failed.';
            errorDiv.style.display = 'block';
          }
        });

        // Login form logic and API call
        var loginForm = document.getElementById('loginForm');
        loginForm.addEventListener('submit', async function(e) {
          e.preventDefault();
          var username = document.getElementById('loginUsername').value;
          var password = document.getElementById('loginPassword').value;
          try {
            const response = await fetch('/api/login', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ username: username, password: password })
            });
            const data = await response.json();
            if (response.ok) {
              // Store JWT and user info in localStorage
              localStorage.setItem('access_token', data.access_token);
              localStorage.setItem('user', JSON.stringify(data.user));
              alert('Login successful!');
              window.location.reload();
            } else {
              alert(data.detail || 'Login failed.');
            }
          } catch (err) {
            alert('Login failed.');
          }
        });
      });