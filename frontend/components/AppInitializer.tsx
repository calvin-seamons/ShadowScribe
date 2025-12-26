'use client'

import { useEffect, useState } from 'react'
import { LogoText } from './Logo'

interface AppInitializerProps {
  children: React.ReactNode
}

export default function AppInitializer({ children }: AppInitializerProps) {
  const [isInitialized, setIsInitialized] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState<'checking' | 'connected' | 'error'>('checking')
  const [errorMessage, setErrorMessage] = useState<string>('')

  useEffect(() => {
    const checkConnection = async () => {
      try {
        // Get API URL from environment or construct for local dev
        let apiUrl: string
        if (process.env.NEXT_PUBLIC_API_URL) {
          apiUrl = process.env.NEXT_PUBLIC_API_URL
        } else {
          // Development fallback: use localhost
          const protocol = window.location.protocol
          const host = window.location.hostname
          const port = '8000'
          apiUrl = `${protocol}//${host}:${port}`
        }

        console.log(`Checking backend connection at: ${apiUrl}`)
        
        // Test backend connection with timeout
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), 5000)

        const response = await fetch(`${apiUrl}/docs`, {
          signal: controller.signal,
          mode: 'no-cors', // Just check if endpoint responds
        })

        clearTimeout(timeoutId)

        // If we got here without error, backend is accessible
        console.log('Backend connection successful')
        setConnectionStatus('connected')
        
        // Small delay for smooth transition
        setTimeout(() => {
          setIsInitialized(true)
        }, 500)

      } catch (error) {
        console.error('Backend connection failed:', error)
        setConnectionStatus('error')
        
        if (error instanceof Error) {
          if (error.name === 'AbortError') {
            setErrorMessage('Connection timeout - backend is not responding')
          } else {
            setErrorMessage(error.message || 'Unable to connect to backend')
          }
        } else {
          setErrorMessage('Unable to connect to backend')
        }
      }
    }

    checkConnection()
  }, [])

  const retry = () => {
    setConnectionStatus('checking')
    setErrorMessage('')
    window.location.reload()
  }

  if (isInitialized) {
    return <>{children}</>
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
      <div className="text-center max-w-md px-6">
        {/* Logo */}
        <div className="mb-8 flex justify-center">
          <div className="scale-150">
            <LogoText />
          </div>
        </div>

        {/* Status indicator */}
        {connectionStatus === 'checking' && (
          <div className="space-y-6">
            <div className="flex justify-center">
              <div className="relative">
                <div className="w-20 h-20 border-4 border-purple-500/20 rounded-full"></div>
                <div className="absolute top-0 left-0 w-20 h-20 border-4 border-purple-500 border-t-transparent rounded-full animate-spin"></div>
              </div>
            </div>
            <div>
              <h2 className="text-2xl font-bold text-white mb-2">
                Initializing Application
              </h2>
              <p className="text-purple-300">
                Connecting to backend services...
              </p>
            </div>
          </div>
        )}

        {connectionStatus === 'error' && (
          <div className="space-y-6">
            <div className="flex justify-center">
              <div className="w-20 h-20 rounded-full bg-red-500/20 flex items-center justify-center">
                <span className="text-4xl">⚠️</span>
              </div>
            </div>
            <div>
              <h2 className="text-2xl font-bold text-red-400 mb-2">
                Connection Failed
              </h2>
              <p className="text-red-300 mb-4">
                {errorMessage || 'Unable to connect to the backend server'}
              </p>
              <div className="space-y-2 text-sm text-purple-300/80">
                <p>Please ensure:</p>
                <ul className="list-disc list-inside text-left space-y-1">
                  <li>Backend server is running (port 8000)</li>
                  <li>Network connection is stable</li>
                  <li>Firewall allows connections</li>
                </ul>
              </div>
            </div>
            <button
              onClick={retry}
              className="px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:from-purple-700 hover:to-pink-700 transition-all transform hover:scale-105 active:scale-95 font-medium shadow-lg"
            >
              Retry Connection
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
