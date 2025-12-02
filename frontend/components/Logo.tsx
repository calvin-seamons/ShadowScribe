/**
 * ShadowScribe Logo - Arcane quill with mystical glow
 */
'use client';

interface LogoProps {
  size?: number;
  className?: string;
  animated?: boolean;
}

export function Logo({ size = 40, className = '', animated = true }: LogoProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={`${className} ${animated ? 'transition-transform duration-300 hover:scale-110' : ''}`}
    >
      {/* Outer glow effect */}
      <defs>
        <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
          <feMerge>
            <feMergeNode in="coloredBlur"/>
            <feMergeNode in="SourceGraphic"/>
          </feMerge>
        </filter>
        <linearGradient id="goldGradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#F59E0B"/>
          <stop offset="50%" stopColor="#FBBF24"/>
          <stop offset="100%" stopColor="#D97706"/>
        </linearGradient>
        <linearGradient id="shadowGradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#1E1B4B" stopOpacity="0.6"/>
          <stop offset="100%" stopColor="#312E81" stopOpacity="0.3"/>
        </linearGradient>
        <radialGradient id="innerGlow" cx="50%" cy="30%" r="70%">
          <stop offset="0%" stopColor="#FEF3C7"/>
          <stop offset="100%" stopColor="#F59E0B"/>
        </radialGradient>
      </defs>

      {/* Mystical circle background */}
      <circle
        cx="50"
        cy="50"
        r="46"
        fill="none"
        stroke="url(#goldGradient)"
        strokeWidth="1.5"
        strokeDasharray="4 6"
        opacity="0.4"
      />

      {/* Shadow/depth effect */}
      <g opacity="0.25" transform="translate(3, 4)">
        <path
          d="M55 78 L50 92 L45 78 L38 45 L50 12 L62 45 Z"
          fill="#1E1B4B"
        />
      </g>

      {/* Main quill feather */}
      <g filter="url(#glow)">
        <path
          d="M55 78 L50 92 L45 78 L38 45 L50 12 L62 45 Z"
          fill="url(#innerGlow)"
          stroke="url(#goldGradient)"
          strokeWidth="2"
        />
      </g>

      {/* Feather spine (rachis) */}
      <line
        x1="50"
        y1="18"
        x2="50"
        y2="85"
        stroke="#92400E"
        strokeWidth="1.5"
        strokeLinecap="round"
      />

      {/* Left barbs */}
      <g stroke="#78350F" strokeWidth="1" strokeLinecap="round" opacity="0.7">
        <path d="M50 25 Q40 30 36 38"/>
        <path d="M50 35 Q42 40 38 48"/>
        <path d="M50 45 Q43 50 40 58"/>
        <path d="M50 55 Q44 60 42 68"/>
        <path d="M50 65 Q45 70 44 76"/>
      </g>

      {/* Right barbs */}
      <g stroke="#78350F" strokeWidth="1" strokeLinecap="round" opacity="0.7">
        <path d="M50 25 Q60 30 64 38"/>
        <path d="M50 35 Q58 40 62 48"/>
        <path d="M50 45 Q57 50 60 58"/>
        <path d="M50 55 Q56 60 58 68"/>
        <path d="M50 65 Q55 70 56 76"/>
      </g>

      {/* Quill tip (nib) */}
      <path
        d="M47 85 L50 95 L53 85"
        fill="#1E1B4B"
        stroke="#D97706"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />

      {/* Ink drop */}
      <ellipse
        cx="50"
        cy="96"
        rx="2"
        ry="1"
        fill="#312E81"
        opacity="0.5"
      />

      {/* Sparkle accents */}
      <g fill="#FEF3C7" opacity="0.9">
        <circle cx="42" cy="28" r="1.5"/>
        <circle cx="58" cy="32" r="1"/>
        <circle cx="44" cy="50" r="1"/>
      </g>
    </svg>
  );
}

interface LogoTextProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

export function LogoText({ className = '', size = 'md' }: LogoTextProps) {
  const sizes = {
    sm: { logo: 36, title: 'text-lg', subtitle: 'text-[10px]' },
    md: { logo: 48, title: 'text-2xl', subtitle: 'text-xs' },
    lg: { logo: 64, title: 'text-4xl', subtitle: 'text-sm' },
  };

  const s = sizes[size];

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <Logo size={s.logo} />
      <div className="flex flex-col">
        <span className={`${s.title} font-bold tracking-wide text-gradient-gold text-shadow-sm`}>
          ShadowScribe
        </span>
        <span className={`${s.subtitle} text-muted-foreground tracking-[0.2em] uppercase font-medium`}>
          Arcane Companion
        </span>
      </div>
    </div>
  );
}

// Mini version for tight spaces
export function LogoMini({ className = '' }: { className?: string }) {
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <Logo size={32} animated={false} />
      <span className="text-lg font-bold tracking-wide text-gradient-gold">
        SS
      </span>
    </div>
  );
}
