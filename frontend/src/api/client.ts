import axios from 'axios';

const apiClient = axios.create({
  baseURL: '',  // Uses Vite proxy in dev
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
});

export default apiClient;
