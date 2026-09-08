// Authentication Tab Switching & Form Submissions
document.addEventListener('DOMContentLoaded', () => {
  const loginTab = document.getElementById('loginTab');
  const registerTab = document.getElementById('registerTab');
  const loginForm = document.getElementById('loginForm');
  const registerForm = document.getElementById('registerForm');
  const alertBox = document.getElementById('alertBox');

  function showAlert(msg, isSuccess = false) {
    alertBox.textContent = msg;
    alertBox.className = `alert ${isSuccess ? 'alert-success' : 'alert-error'}`;
    alertBox.style.display = 'block';
  }

  function hideAlert() {
    alertBox.style.display = 'none';
  }

  if (loginTab && registerTab) {
    loginTab.addEventListener('click', () => {
      loginTab.classList.add('active');
      registerTab.classList.remove('active');
      loginForm.style.display = 'block';
      registerForm.style.display = 'none';
      hideAlert();
    });

    registerTab.addEventListener('click', () => {
      registerTab.classList.add('active');
      loginTab.classList.remove('active');
      registerForm.style.display = 'block';
      loginForm.style.display = 'none';
      hideAlert();
    });
  }

  // Handle Login Submit
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      hideAlert();

      const username = document.getElementById('loginUsername').value.trim();
      const password = document.getElementById('loginPassword').value;

      try {
        const res = await API.login(username, password);
        showAlert('✅ Login successful! Redirecting...', true);
        setTimeout(() => {
          window.location.href = 'dashboard.html';
        }, 1000);
      } catch (err) {
        showAlert(err.message || 'Login failed.');
      }
    });
  }

  // Handle Register Submit
  if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      hideAlert();

      const username = document.getElementById('regUsername').value.trim();
      const email = document.getElementById('regEmail').value.trim();
      const password = document.getElementById('regPassword').value;

      try {
        const res = await API.register(username, email, password);
        showAlert('✅ Registration successful! Please log in.', true);
        setTimeout(() => {
          if (loginTab) loginTab.click();
        }, 1500);
      } catch (err) {
        showAlert(err.message || 'Registration failed.');
      }
    });
  }
});
