// API Helper for Backend REST API
const API_BASE_URL = 'http://127.0.0.1:5000/api';

const API = {
  async request(endpoint, method = 'GET', data = null) {
    const options = {
      method,
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include', // Send cookies for Flask session
    };

    if (data) {
      options.body = JSON.stringify(data);
    }

    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
      const resData = await response.json();

      if (!response.ok) {
        throw new Error(resData.error || resData.message || 'Request failed');
      }

      return resData;
    } catch (err) {
      console.error(`API Error [${endpoint}]:`, err.message);
      throw err;
    }
  },

  register(username, email, password) {
    return this.request('/register', 'POST', { username, email, password });
  },

  login(username, password) {
    return this.request('/login', 'POST', { username, password });
  },

  getCurrentUser() {
    return this.request('/me', 'GET');
  },

  logout() {
    return this.request('/logout', 'POST');
  },

  recommend(patientData) {
    return this.request('/recommend', 'POST', patientData);
  },

  forgotPassword(email) {
    return this.request('/forgot-password', 'POST', { email });
  },

  resetPassword(token, password) {
    return this.request('/reset-password', 'POST', { token, password });
  }
};
