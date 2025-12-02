import type { Metadata } from 'next'
import './globals.css'
import AppInitializer from '@/components/AppInitializer'
import { ThemeProvider } from '@/components/ThemeProvider'

export const metadata: Metadata = {
  title: 'ShadowScribe 2.0',
  description: 'D&D Character Management & AI Assistant',
  icons: {
    icon: '/favicon.ico',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        {/* Inline script to prevent flash of wrong theme */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  var stored = localStorage.getItem('shadowscribe-theme');
                  if (stored) {
                    var parsed = JSON.parse(stored);
                    var theme = parsed.state && parsed.state.theme;
                    if (theme === 'light') {
                      document.documentElement.classList.remove('dark');
                    } else {
                      document.documentElement.classList.add('dark');
                    }
                  } else {
                    document.documentElement.classList.add('dark');
                  }
                } catch (e) {
                  document.documentElement.classList.add('dark');
                }
              })();
            `,
          }}
        />
      </head>
      <body className="font-sans antialiased">
        <ThemeProvider>
          <AppInitializer>
            {children}
          </AppInitializer>
        </ThemeProvider>
      </body>
    </html>
  )
}
