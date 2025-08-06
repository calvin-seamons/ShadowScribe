import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getAvailableSources = async () => {
  const response = await api.get('/sources');
  return response.data;
};

export const validateSystem = async () => {
  const response = await api.post('/validate');
  return response.data;
};

export const getCharacterSummary = async () => {
  const response = await api.get('/character');
  return response.data;
};

export const getSessionHistory = async (sessionId: string) => {
  const response = await api.get(`/session-history/${sessionId}`);
  return response.data;
};
