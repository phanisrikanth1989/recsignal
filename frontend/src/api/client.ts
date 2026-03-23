import axios from 'axios';

const apiClient = axios.create({
  baseURL: '',  // Uses Vite proxy in dev
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
});

// Auto-clear auth on 401 responses (token expired / invalid)
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && !error.config?.url?.includes('/auth/login')) {
      localStorage.removeItem('recsignal_token');
      localStorage.removeItem('recsignal_user');
      delete apiClient.defaults.headers.common['Authorization'];
      window.location.reload();
    }
    return Promise.reject(error);
  }
);

export default apiClient;
