import axios from 'axios';
import { 
  ChatRequest, 
  ChatResponse, 
  SessionRequest, 
  SessionResponse, 
  HealthResponse, 
  StatsResponse 
} from '../types/api';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for authentication
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export const chatAPI = {
  // Send a chat message
  sendMessage: async (request: ChatRequest): Promise<ChatResponse> => {
    const response = await api.post<ChatResponse>('/chat', request);
    return response.data;
  },

  // Create a new session
  createSession: async (request: SessionRequest): Promise<SessionResponse> => {
    const response = await api.post<SessionResponse>('/sessions', request);
    return response.data;
  },

  // Get session details
  getSession: async (sessionId: string): Promise<SessionResponse> => {
    const response = await api.get<SessionResponse>(`/sessions/${sessionId}`);
    return response.data;
  },

  // Close a session
  closeSession: async (sessionId: string): Promise<void> => {
    await api.delete(`/sessions/${sessionId}`);
  },
};

export const systemAPI = {
  // Get system health
  getHealth: async (): Promise<HealthResponse> => {
    const response = await api.get<HealthResponse>('/health');
    return response.data;
  },

  // Get system statistics
  getStats: async (): Promise<StatsResponse> => {
    const response = await api.get<StatsResponse>('/stats');
    return response.data;
  },

  // Get API root info
  getRoot: async (): Promise<any> => {
    const response = await api.get('/');
    return response.data;
  },
};

export default api; 