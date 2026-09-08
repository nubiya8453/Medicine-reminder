// Password Recovery & Reset Handlers
document.addEventListener('DOMContentLoaded', () => {
  const forgotForm = document.getElementById('forgotForm');
  const resetForm = document.getElementById('resetForm');
  const alertBox = document.getElementById('alertBox');

  function showAlert(msg, isSuccess = false) {
    alertBox.textContent = msg;
    alertBox.className = `alert ${isSuccess ? 'alert-success' : 'alert-error'}`;
    alertBox.style.display = 'block';
  }

  function hideAlert() {
    alertBox.style.display = 'none';
  }

  if (forgotForm) {
    forgotForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      hideAlert();
      const email = document.getElementById('forgotEmail').value.trim();
      try {
        const res = await API.forgotPassword(email);
        showAlert(res.message || 'Reset link sent to your email!', true);
      } catch (err) {
        showAlert(err.message || 'Failed to request password reset.');
      }
    });
  }

  if (resetForm) {
    // Get token from URL params
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');

    if (!token) {
      showAlert('Invalid or missing password reset token.');
      resetForm.style.display = 'none';
      return;
    }

    resetForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      hideAlert();
      const password = document.getElementById('newPassword').value;
      try {
        const res = await API.resetPassword(token, password);
        showAlert('✅ Password updated successfully! Redirecting to login...', true);
        setTimeout(() => {
          window.location.href = 'index.html';
        }, 1500);
      } catch (err) {
        showAlert(err.message || 'Failed to reset password.');
      }
    });
  }
});
