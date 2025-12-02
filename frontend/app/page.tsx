'use client'

import { useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import ChatContainer from '@/components/chat/ChatContainer'
import { LogoText, Logo } from '@/components/Logo'
import { ConversationHistorySidebar } from '@/components/sidebar/ConversationHistorySidebar'
import { MetadataSidebar } from '@/components/sidebar/MetadataSidebar'
import { useMetadataStore } from '@/lib/stores/metadataStore'
import { useCharacterStore } from '@/lib/stores/characterStore'
import { fetchCharacters } from '@/lib/services/api'
import { Eye, EyeOff, Plus, Sparkles, BookOpen, Scroll, MessageSquare, Users, ArrowLeft, Loader2, ChevronRight } from 'lucide-react'
import { ThemeToggle } from '@/components/ThemeToggle'
import Link from 'next/link'
import { cn } from '@/lib/utils'

export default function Home() {
  const searchParams = useSearchParams()
  const [selectedCharacter, setSelectedCharacter] = useState<string | null>(null)
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null)
  const { sidebarVisible, toggleSidebar } = useMetadataStore()

  // Check for character query param on mount
  useEffect(() => {
    const characterParam = searchParams.get('character')
    if (characterParam) {
      setSelectedCharacter(decodeURIComponent(characterParam))
    }
  }, [searchParams])

  const handleNewConversation = () => {
    setSelectedConversationId(null)
  }

  const handleConversationSelect = (conversationId: string) => {
    setSelectedConversationId(conversationId)
  }

  const handleConversationCreated = (conversationId: string) => {
    setSelectedConversationId(conversationId)
  }

  const handleBackToWelcome = () => {
    setSelectedCharacter(null)
    setSelectedConversationId(null)
  }

  return (
    <main className="flex h-screen flex-col overflow-hidden bg-background">
      {/* Ambient background effects */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary/5 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-[500px] h-[500px] bg-accent/5 rounded-full blur-3xl" />
      </div>

      {/* Header */}
      <header className="relative z-10 flex-shrink-0 border-b border-border/50 bg-card/80 backdrop-blur-md">
        <div className="mx-auto flex items-center justify-between px-6 py-4">
          <div className="flex items-center gap-4">
            {selectedCharacter && (
              <button
                onClick={handleBackToWelcome}
                className="btn-ghost flex items-center gap-2 text-sm"
              >
                <ArrowLeft className="w-4 h-4" />
                <span className="hidden sm:inline">Back</span>
              </button>
            )}
            <LogoText size="md" />
          </div>

          <div className="flex items-center gap-3">
            {selectedCharacter && (
              <button
                onClick={toggleSidebar}
                className="btn-ghost flex items-center gap-2 text-sm"
                title={sidebarVisible ? 'Hide analysis' : 'Show analysis'}
              >
                {sidebarVisible ? (
                  <>
                    <EyeOff className="w-4 h-4" />
                    <span className="hidden sm:inline">Hide Analysis</span>
                  </>
                ) : (
                  <>
                    <Eye className="w-4 h-4" />
                    <span className="hidden sm:inline">Show Analysis</span>
                  </>
                )}
              </button>
            )}
            <ThemeToggle />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="relative z-0 flex-1 flex min-h-0">
        {selectedCharacter ? (
          <>
            {/* Left sidebar - Conversation history */}
            <ConversationHistorySidebar
              characterName={selectedCharacter}
              onConversationSelect={handleConversationSelect}
              onNewConversation={handleNewConversation}
            />

            {/* Center - Chat */}
            <div className="flex-1 flex flex-col min-h-0 min-w-0">
              <ChatContainer
                characterName={selectedCharacter}
                conversationId={selectedConversationId}
                onConversationCreated={handleConversationCreated}
              />
            </div>

            {/* Right sidebar - Metadata */}
            {sidebarVisible && <MetadataSidebar />}
          </>
        ) : (
          <WelcomeScreen onSelectCharacter={setSelectedCharacter} />
        )}
      </div>
    </main>
  )
}

interface WelcomeScreenProps {
  onSelectCharacter: (name: string) => void
}

function WelcomeScreen({ onSelectCharacter }: WelcomeScreenProps) {
  const [view, setView] = useState<'main' | 'select-character'>('main')

  if (view === 'select-character') {
    return <CharacterSelectView onSelect={onSelectCharacter} onBack={() => setView('main')} />
  }

  return (
    <div className="flex-1 flex items-center justify-center p-8">
      <div className="max-w-3xl text-center animate-fade-in-up">
        {/* Decorative top element */}
        <div className="flex justify-center mb-8">
          <div className="relative">
            <Logo size={100} />
            <div className="absolute inset-0 animate-pulse-glow rounded-full" />
          </div>
        </div>

        {/* Main title */}
        <h1 className="text-5xl md:text-6xl font-bold mb-4 text-gradient-gold text-shadow-glow">
          ShadowScribe
        </h1>

        <p className="text-xl text-muted-foreground mb-2 tracking-wide">
          Your Arcane D&D Companion
        </p>

        {/* Ornate divider */}
        <div className="divider-ornate my-8">
          <Sparkles className="w-5 h-5 text-primary" />
        </div>

        <p className="text-lg text-foreground/80 mb-10 leading-relaxed max-w-lg mx-auto">
          Consult the ancient tomes of your character's knowledge. Ask about abilities,
          spells, backstory, and the rules that govern your adventures.
        </p>

        {/* Feature cards */}
        <div className="grid md:grid-cols-3 gap-4 mb-10">
          <FeatureCard
            icon={<BookOpen className="w-6 h-6" />}
            title="Character Lore"
            description="Deep knowledge of your character's stats, abilities, and history"
          />
          <FeatureCard
            icon={<Scroll className="w-6 h-6" />}
            title="Rulebook Wisdom"
            description="Instant access to D&D 5e rules and mechanics"
          />
          <FeatureCard
            icon={<Sparkles className="w-6 h-6" />}
            title="Session Memory"
            description="Remembers your campaign notes and past adventures"
          />
        </div>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <button
            onClick={() => setView('select-character')}
            className="btn-primary inline-flex items-center gap-3 text-lg px-8 py-4 w-full sm:w-auto"
          >
            <MessageSquare className="w-5 h-5" />
            Chat with Character
          </button>

          <Link
            href="/characters/create"
            className="btn-secondary inline-flex items-center gap-3 text-lg px-8 py-4 w-full sm:w-auto justify-center"
          >
            <Plus className="w-5 h-5" />
            Create New Character
          </Link>
        </div>

        <p className="mt-8 text-sm text-muted-foreground">
          Choose to chat with an existing character or import a new one from D&D Beyond
        </p>
      </div>
    </div>
  )
}

interface CharacterSelectViewProps {
  onSelect: (name: string) => void
  onBack: () => void
}

function CharacterSelectView({ onSelect, onBack }: CharacterSelectViewProps) {
  const { characters, setCharacters, isLoading: loading, setLoading, error, setError } = useCharacterStore()
  const [loadAttempted, setLoadAttempted] = useState(false)

  useEffect(() => {
    if (!loadAttempted) {
      loadCharacters()
    }
  }, [loadAttempted])

  const loadCharacters = async () => {
    setLoading(true)
    setError(null)
    setLoadAttempted(true)

    try {
      const response = await fetchCharacters()
      setCharacters(response.characters)
    } catch (err) {
      console.error('Error loading characters:', err)
      setError('Failed to load characters. Please check if the API server is running.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex-1 flex items-center justify-center p-8">
      <div className="max-w-2xl w-full animate-fade-in-up">
        {/* Back button */}
        <button
          onClick={onBack}
          className="btn-ghost flex items-center gap-2 mb-8"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Home
        </button>

        {/* Header */}
        <div className="text-center mb-10">
          <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto mb-5">
            <Users className="w-8 h-8 text-primary" />
          </div>
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-2">
            Select Your Character
          </h2>
          <p className="text-muted-foreground">
            Choose a character to begin your conversation
          </p>
        </div>

        {/* Character list */}
        <div className="card-elevated p-6">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-primary mb-4" />
              <p className="text-muted-foreground">Loading characters...</p>
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <div className="w-16 h-16 rounded-full bg-destructive/10 flex items-center justify-center mx-auto mb-4">
                <Users className="w-8 h-8 text-destructive" />
              </div>
              <p className="text-destructive font-medium mb-2">Connection Error</p>
              <p className="text-sm text-muted-foreground mb-4">{error}</p>
              <button onClick={loadCharacters} className="btn-secondary text-sm">
                Retry
              </button>
            </div>
          ) : characters.length === 0 ? (
            <div className="text-center py-12">
              <div className="w-16 h-16 rounded-full bg-muted/50 flex items-center justify-center mx-auto mb-4">
                <Users className="w-8 h-8 text-muted-foreground/50" />
              </div>
              <p className="text-foreground font-medium mb-2">No Characters Found</p>
              <p className="text-sm text-muted-foreground mb-6">
                You haven't created any characters yet. Import one from D&D Beyond to get started.
              </p>
              <Link href="/characters/create" className="btn-primary inline-flex items-center gap-2">
                <Plus className="w-4 h-4" />
                Create Character
              </Link>
            </div>
          ) : (
            <div className="space-y-2">
              {characters.map((character, index) => (
                <button
                  key={character.id}
                  onClick={() => onSelect(character.name)}
                  className={cn(
                    'w-full flex items-center gap-4 p-4 rounded-xl transition-all',
                    'bg-card/50 border border-border/50 hover:border-primary/30 hover:bg-card',
                    'group'
                  )}
                  style={{ animationDelay: `${index * 50}ms` }}
                >
                  <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center text-xl font-bold text-primary group-hover:scale-105 transition-transform">
                    {character.name.charAt(0).toUpperCase()}
                  </div>
                  <div className="flex-1 text-left">
                    <p className="font-semibold text-foreground text-lg">{character.name}</p>
                    <p className="text-sm text-muted-foreground">
                      Level {character.level} {character.race} {character.character_class}
                    </p>
                  </div>
                  <ChevronRight className="w-5 h-5 text-muted-foreground group-hover:text-primary group-hover:translate-x-1 transition-all" />
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Create new character link */}
        {characters.length > 0 && (
          <div className="text-center mt-6">
            <p className="text-sm text-muted-foreground mb-3">
              Don't see your character?
            </p>
            <Link
              href="/characters/create"
              className="inline-flex items-center gap-2 text-primary hover:underline"
            >
              <Plus className="w-4 h-4" />
              Import from D&D Beyond
            </Link>
          </div>
        )}
      </div>
    </div>
  )
}

interface FeatureCardProps {
  icon: React.ReactNode
  title: string
  description: string
}

function FeatureCard({ icon, title, description }: FeatureCardProps) {
  return (
    <div className="group p-5 rounded-xl bg-card/50 border border-border/50 hover:border-primary/30 hover:bg-card transition-all duration-300">
      <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center text-primary mb-4 mx-auto group-hover:scale-110 transition-transform">
        {icon}
      </div>
      <h3 className="font-semibold text-foreground mb-2">{title}</h3>
      <p className="text-sm text-muted-foreground leading-relaxed">{description}</p>
    </div>
  )
}
