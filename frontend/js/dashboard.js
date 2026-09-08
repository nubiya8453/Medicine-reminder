// Dashboard logic and Medicine Recommendation submission
document.addEventListener('DOMContentLoaded', async () => {
  const userGreeting = document.getElementById('userGreeting');
  const logoutBtn = document.getElementById('logoutBtn');
  const recommendForm = document.getElementById('recommendForm');
  const alertBox = document.getElementById('alertBox');

  const resultCard = document.getElementById('resultCard');
  const resDisease = document.getElementById('resDisease');
  const resMedicine = document.getElementById('resMedicine');
  const resDosage = document.getElementById('resDosage');
  const resTiming = document.getElementById('resTiming');

  // Verify auth session
  try {
    const user = await API.getCurrentUser();
    if (user.authenticated && userGreeting) {
      userGreeting.textContent = `Welcome, ${user.username}! 👋`;
    }
  } catch (err) {
    // If not authenticated, redirect to login
    window.location.href = 'index.html';
    return;
  }

  // Handle Logout
  if (logoutBtn) {
    logoutBtn.addEventListener('click', async (e) => {
      e.preventDefault();
      await API.logout();
      window.location.href = 'index.html';
    });
  }

  function showAlert(msg, isSuccess = false) {
    alertBox.textContent = msg;
    alertBox.className = `alert ${isSuccess ? 'alert-success' : 'alert-error'}`;
    alertBox.style.display = 'block';
  }

  function hideAlert() {
    alertBox.style.display = 'none';
  }

  // Handle Medicine Recommendation Submit
  if (recommendForm) {
    recommendForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      hideAlert();

      const patientData = {
        patient_name: document.getElementById('patientName').value.trim(),
        age: document.getElementById('patientAge').value,
        gender: document.getElementById('patientGender').value,
        email: document.getElementById('patientEmail').value.trim(),
        disease: document.getElementById('patientDisease').value.trim()
      };

      try {
        showAlert('⏳ Generating recommendation & sending email...', true);
        const res = await API.recommend(patientData);

        if (res.success) {
          showAlert('✅ Recommendation generated & sent to patient email!', true);
          resDisease.textContent = res.disease;
          resMedicine.textContent = res.medicine;
          resDosage.textContent = res.dosage;
          resTiming.textContent = res.timing;
          resultCard.style.display = 'block';
        }
      } catch (err) {
        showAlert(err.message || 'Failed to get recommendation.');
      }
    });
  }
});
