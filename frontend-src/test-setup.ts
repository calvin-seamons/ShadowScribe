import { vi } from 'vitest'
import '@testing-library/jest-dom'

// Mock environment variables
vi.mock('import.meta', () => ({
  env: {
    VITE_API_URL: 'http://localhost:8001/api'
  }
}))

// Global test setup
global.fetch = vi.fn()