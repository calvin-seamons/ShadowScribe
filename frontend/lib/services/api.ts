// Use dynamic host for Docker/network access
// In browser: Use current hostname (works for localhost, LAN IP, etc.)
// Fallback to env var if available
function getApiUrl(): string {
  if (typeof window !== 'undefined') {
    const protocol = window.location.protocol
    const host = window.location.hostname
    const port = '8000' // Backend port
    return `${protocol}//${host}:${port}`
  }
  // Server-side fallback
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
}

const API_URL = getApiUrl()

// Fetch with timeout helper
async function fetchWithTimeout(url: string, options: RequestInit = {}, timeout = 5000) {
  const controller = new AbortController()
  const id = setTimeout(() => controller.abort(), timeout)
  
  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal
    })
    clearTimeout(id)
    return response
  } catch (error) {
    clearTimeout(id)
    throw error
  }
}

export async function fetchCharacters() {
  const response = await fetchWithTimeout(`${API_URL}/api/characters`, {}, 3000)
  if (!response.ok) {
    throw new Error('Failed to fetch characters')
  }
  return response.json()
}

export async function fetchCharacter(id: string) {
  const response = await fetchWithTimeout(`${API_URL}/api/characters/${id}`)
  if (!response.ok) {
    throw new Error('Failed to fetch character')
  }
  return response.json()
}

export async function deleteCharacter(id: string) {
  const response = await fetchWithTimeout(`${API_URL}/api/characters/${id}`, {
    method: 'DELETE'
  })
  if (!response.ok) {
    throw new Error('Failed to delete character')
  }
  return response.json()
}
