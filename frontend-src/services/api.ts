const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export async function getAvailableSources() {
  const response = await fetch(`${API_BASE_URL}/sources`);
  if (!response.ok) throw new Error('Failed to fetch sources');
  return response.json();
}

export async function getCharacterSummary() {
  const response = await fetch(`${API_BASE_URL}/character`);
  if (!response.ok) throw new Error('Failed to fetch character');
  return response.json();
}

export async function getSessionHistory(sessionId: string) {
  const response = await fetch(`${API_BASE_URL}/session-history/${sessionId}`);
  if (!response.ok) throw new Error('Failed to fetch session history');
  return response.json();
}

export async function validateSystem() {
  const response = await fetch(`${API_BASE_URL}/validate`, {
    method: 'POST',
  });
  if (!response.ok) throw new Error('Failed to validate system');
  return response.json();
}

export async function getModels() {
  const response = await fetch(`${API_BASE_URL}/models`);
  if (!response.ok) throw new Error('Failed to fetch models');
  return response.json();
}

export async function updateModel(model: string) {
  const response = await fetch(`${API_BASE_URL}/models`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ model }),
  });
  if (!response.ok) throw new Error('Failed to update model');
  return response.json();
}
