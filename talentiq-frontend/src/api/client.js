import axios from 'axios';

// Get backend URL from environment or fallback to localhost
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const askQuestion = async (question) => {
  try {
    const response = await apiClient.post('/ask', { question });
    return response.data;
  } catch (error) {
    console.error('API Error:', error);
    throw new Error(error.response?.data?.detail || 'Failed to reach TalentIQ Intelligence Backend');
  }
};

export default apiClient;
