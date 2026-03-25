import axios from 'axios';

// Create axios instance with base URL
const API_BASE_URL = process.env.VITE_API_URL || 'http://localhost:5000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for JWT token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Authentication endpoints
export const authApi = {
  getToken: () => apiClient.post('/auth/token'),
  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
  },
};

// Health endpoints
export const healthApi = {
  check: () => apiClient.get('/health'),
};

// Submission endpoints
export const submissionApi = {
  upload: (formData) => {
    const config = {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    };
    return apiClient.post('/submissions/upload', formData, config);
  },
  
  getStatus: (submissionId) => apiClient.get(`/submissions/${submissionId}/status`),
  
  process: (submissionId) => apiClient.post(`/submissions/${submissionId}/process`),
  
  getResults: (submissionId) => apiClient.get(`/submissions/${submissionId}/results`),
  
  listSubmissions: (page = 1, perPage = 10) =>
    apiClient.get(`/submissions?page=${page}&per_page=${perPage}`),
};

// Utility function to handle API errors
export const handleApiError = (error) => {
  if (error.response) {
    // Server responded with error
    return error.response.data.error || 'An error occurred';
  } else if (error.request) {
    // Request made but no response
    return 'No response from server. Is the backend running?';
  } else {
    // Error in request setup
    return error.message;
  }
};

export default apiClient;
