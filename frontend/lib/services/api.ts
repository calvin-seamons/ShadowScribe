// API URL configuration
// - Production: Uses NEXT_PUBLIC_API_URL environment variable
// - Development (localhost): Uses localhost:8000
function getApiUrl(): string {
  // Check for explicit API URL first (production)
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL
  }

  // Development: use localhost with backend port
  if (typeof window !== 'undefined') {
    const host = window.location.hostname
    // If on localhost, use local backend
    if (host === 'localhost' || host === '127.0.0.1') {
      return `http://${host}:8000`
    }
    // For LAN access during development
    return `${window.location.protocol}//${host}:8000`
  }

  return 'http://localhost:8000'
}

const API_URL = getApiUrl()

// Get auth token from localStorage
function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem('auth_token')
}

// Build headers with optional auth
function buildHeaders(includeAuth: boolean = true): HeadersInit {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  }

  if (includeAuth) {
    const token = getAuthToken()
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
  }

  return headers
}

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
  const response = await fetchWithTimeout(`${API_URL}/api/characters`, {
    headers: buildHeaders()
  }, 3000)
  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('Authentication required')
    }
    throw new Error('Failed to fetch characters')
  }
  return response.json()
}

export async function fetchCharacter(id: string) {
  const response = await fetchWithTimeout(`${API_URL}/api/characters/${id}`, {
    headers: buildHeaders()
  })
  if (!response.ok) {
    throw new Error('Failed to fetch character')
  }
  return response.json()
}

export async function deleteCharacter(id: string) {
  const response = await fetchWithTimeout(`${API_URL}/api/characters/${id}`, {
    method: 'DELETE',
    headers: buildHeaders()
  })
  if (!response.ok) {
    throw new Error('Failed to delete character')
  }
  return response.json()
}
