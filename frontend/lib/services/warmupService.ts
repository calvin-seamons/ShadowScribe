import { useWarmupStore } from '@/lib/stores/warmupStore'

// API URL configuration (matches api.ts pattern)
function getApiUrl(): string {
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL
  }

  if (typeof window !== 'undefined') {
    const host = window.location.hostname
    if (host === 'localhost' || host === '127.0.0.1') {
      return `http://${host}:8000`
    }
    return `${window.location.protocol}//${host}:8000`
  }

  return 'http://localhost:8000'
}

/**
 * Trigger backend warmup by calling POST /warmup.
 * This causes Cloud Run to spin up an instance if needed.
 */
export async function triggerWarmup(): Promise<void> {
  const apiUrl = getApiUrl()

  try {
    await fetch(`${apiUrl}/warmup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    })
  } catch (error) {
    // Ignore errors - this is just a trigger, we'll poll /ready for actual status
    console.log('[Warmup] Trigger sent (may fail on cold start, will poll /ready)')
  }
}

/**
 * Check if backend is ready by calling GET /ready.
 * Returns true if ready, false if still warming up.
 */
export async function checkReadiness(): Promise<boolean> {
  const apiUrl = getApiUrl()
  const store = useWarmupStore.getState()

  try {
    const response = await fetch(`${apiUrl}/ready`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    })

    if (response.ok) {
      const data = await response.json()
      if (data.ready) {
        store.setReady()
        return true
      }
    }

    // 503 or other non-200 means still warming up
    store.setStatus('warming')
    return false
  } catch (error) {
    // Network error - backend not reachable yet
    store.setStatus('warming')
    return false
  }
}

/**
 * Poll /ready endpoint until backend is ready or timeout is reached.
 *
 * @param intervalMs - How often to check (default: 2000ms)
 * @param timeoutMs - Max time to wait (default: 120000ms = 2 minutes)
 * @returns true if ready, false if timed out
 */
export async function pollUntilReady(
  intervalMs: number = 2000,
  timeoutMs: number = 120000
): Promise<boolean> {
  const store = useWarmupStore.getState()
  store.setStatus('checking')

  const startTime = Date.now()

  // Trigger warmup first to wake up Cloud Run
  await triggerWarmup()

  // Small delay before first check (give instance time to start)
  await new Promise((resolve) => setTimeout(resolve, 1000))

  while (Date.now() - startTime < timeoutMs) {
    const ready = await checkReadiness()
    if (ready) {
      return true
    }
    await new Promise((resolve) => setTimeout(resolve, intervalMs))
  }

  // Timeout reached
  store.setError('Backend took too long to initialize. Please try again.')
  return false
}
