'use client'

import { useThemeStore } from '@/lib/stores/themeStore'
import { cn } from '@/lib/utils'

interface ThemeToggleProps {
  className?: string
}

export function ThemeToggle({ className }: ThemeToggleProps) {
  const { theme, toggleTheme } = useThemeStore()
  const isDark = theme === 'dark'

  return (
    <button
      onClick={toggleTheme}
      className={cn(
        'group relative w-14 h-8 rounded-full transition-all duration-500',
        'bg-gradient-to-br border',
        isDark
          ? 'from-slate-900 via-indigo-950 to-slate-900 border-indigo-500/30'
          : 'from-amber-100 via-yellow-50 to-amber-100 border-amber-400/40',
        'hover:shadow-lg',
        isDark
          ? 'hover:shadow-indigo-500/20'
          : 'hover:shadow-amber-400/30',
        'focus:outline-none focus:ring-2 focus:ring-primary/30',
        className
      )}
      title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
      aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
    >
      {/* Stars (visible in dark mode) */}
      <div className={cn(
        'absolute inset-0 overflow-hidden rounded-full transition-opacity duration-500',
        isDark ? 'opacity-100' : 'opacity-0'
      )}>
        <span className="absolute w-0.5 h-0.5 bg-white/80 rounded-full top-2 left-2 animate-pulse" style={{ animationDelay: '0s' }} />
        <span className="absolute w-1 h-1 bg-white/60 rounded-full top-4 left-4 animate-pulse" style={{ animationDelay: '0.5s' }} />
        <span className="absolute w-0.5 h-0.5 bg-white/70 rounded-full top-1.5 right-6 animate-pulse" style={{ animationDelay: '1s' }} />
        <span className="absolute w-0.5 h-0.5 bg-white/50 rounded-full bottom-2 left-3 animate-pulse" style={{ animationDelay: '0.3s' }} />
      </div>

      {/* Sun rays (visible in light mode) */}
      <div className={cn(
        'absolute inset-0 overflow-hidden rounded-full transition-opacity duration-500',
        isDark ? 'opacity-0' : 'opacity-100'
      )}>
        {[...Array(6)].map((_, i) => (
          <span
            key={i}
            className="absolute w-0.5 h-2 bg-gradient-to-t from-amber-400/0 to-amber-400/60 rounded-full"
            style={{
              left: '70%',
              top: '50%',
              transformOrigin: '50% 50%',
              transform: `rotate(${i * 60}deg) translateY(-10px)`,
            }}
          />
        ))}
      </div>

      {/* Celestial orb (sun/moon) */}
      <div
        className={cn(
          'absolute top-1 w-6 h-6 rounded-full transition-all duration-500 ease-out',
          'flex items-center justify-center',
          isDark
            ? 'left-1 bg-gradient-to-br from-slate-200 via-slate-100 to-slate-300 shadow-lg shadow-slate-400/30'
            : 'left-7 bg-gradient-to-br from-amber-400 via-yellow-300 to-amber-500 shadow-lg shadow-amber-500/40'
        )}
      >
        {/* Moon craters (dark mode) */}
        <div className={cn(
          'absolute inset-0 overflow-hidden rounded-full transition-opacity duration-500',
          isDark ? 'opacity-100' : 'opacity-0'
        )}>
          <span className="absolute w-1.5 h-1.5 bg-slate-300/60 rounded-full top-1 left-2" />
          <span className="absolute w-1 h-1 bg-slate-300/40 rounded-full bottom-2 left-1" />
          <span className="absolute w-0.5 h-0.5 bg-slate-300/50 rounded-full top-3 right-1.5" />
        </div>

        {/* Sun glow (light mode) */}
        <div className={cn(
          'absolute -inset-1 rounded-full transition-opacity duration-500',
          'bg-gradient-to-br from-yellow-200/50 to-amber-300/30 blur-sm',
          isDark ? 'opacity-0' : 'opacity-100'
        )} />
      </div>

      {/* Arcane ring glow on hover */}
      <div className={cn(
        'absolute inset-0 rounded-full transition-opacity duration-300',
        'opacity-0 group-hover:opacity-100',
        isDark
          ? 'ring-2 ring-indigo-400/30 ring-offset-2 ring-offset-transparent'
          : 'ring-2 ring-amber-400/30 ring-offset-2 ring-offset-transparent'
      )} />
    </button>
  )
}
