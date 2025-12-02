'use client'

import { useEffect } from 'react'
import { useThemeStore } from '@/lib/stores/themeStore'

interface ThemeProviderProps {
  children: React.ReactNode
}

export function ThemeProvider({ children }: ThemeProviderProps) {
  const { theme } = useThemeStore()

  useEffect(() => {
    // Apply theme class to document
    const root = document.documentElement

    if (theme === 'dark') {
      root.classList.add('dark')
    } else {
      root.classList.remove('dark')
    }
  }, [theme])

  // Prevent flash of wrong theme on initial load
  useEffect(() => {
    // Check localStorage directly on mount for immediate application
    const stored = localStorage.getItem('shadowscribe-theme')
    if (stored) {
      try {
        const parsed = JSON.parse(stored)
        const savedTheme = parsed.state?.theme
        if (savedTheme === 'light') {
          document.documentElement.classList.remove('dark')
        } else {
          document.documentElement.classList.add('dark')
        }
      } catch {
        // Default to dark if parsing fails
        document.documentElement.classList.add('dark')
      }
    }
  }, [])

  return <>{children}</>
}
