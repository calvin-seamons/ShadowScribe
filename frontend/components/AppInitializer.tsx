'use client'

import { useEffect, useState } from 'react'
import { LogoText } from './Logo'
import { useWarmupStore } from '@/lib/stores/warmupStore'
import { pollUntilReady } from '@/lib/services/warmupService'

interface AppInitializerProps {
  children: React.ReactNode
}

export default function AppInitializer({ children }: AppInitializerProps) {
  const [isInitialized, setIsInitialized] = useState(false)
  const { status, error } = useWarmupStore()

  useEffect(() => {
    const initialize = async () => {
      const ready = await pollUntilReady(2000, 120000) // Poll every 2s, timeout 2 min

      if (ready) {
        // Small delay for smooth transition
        setTimeout(() => {
          setIsInitialized(true)
        }, 500)
      }
    }

    initialize()
  }, [])

  const retry = () => {
    useWarmupStore.getState().reset()
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

        {/* Warming up state */}
        {(status === 'idle' || status === 'checking' || status === 'warming') && (
          <div className="space-y-6">
            <div className="flex justify-center">
              <div className="relative">
                <div className="w-20 h-20 border-4 border-purple-500/20 rounded-full"></div>
                <div className="absolute top-0 left-0 w-20 h-20 border-4 border-purple-500 border-t-transparent rounded-full animate-spin"></div>
              </div>
            </div>
            <div>
              <h2 className="text-2xl font-bold text-white mb-2">
                Preparing the System
              </h2>
              <p className="text-purple-300">
                {status === 'warming'
                  ? 'Loading knowledge bases...'
                  : 'Connecting to backend services...'}
              </p>
            </div>
          </div>
        )}

        {/* Error state */}
        {status === 'error' && (
          <div className="space-y-6">
            <div className="flex justify-center">
              <div className="w-20 h-20 rounded-full bg-red-500/20 flex items-center justify-center">
                <span className="text-4xl">!</span>
              </div>
            </div>
            <div>
              <h2 className="text-2xl font-bold text-red-400 mb-2">
                Connection Failed
              </h2>
              <p className="text-red-300 mb-4">
                {error || 'Unable to connect to the backend server'}
              </p>
              <div className="space-y-2 text-sm text-purple-300/80">
                <p>This may be due to:</p>
                <ul className="list-disc list-inside text-left space-y-1">
                  <li>Backend service is starting up (cold start)</li>
                  <li>Network connection issues</li>
                  <li>Service temporarily unavailable</li>
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
