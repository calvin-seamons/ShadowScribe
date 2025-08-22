import { render, screen, fireEvent } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { NavigationMenu } from '../NavigationMenu';
import { useNavigationStore } from '../../../stores/navigationStore';

// Mock the navigation store
vi.mock('../../../stores/navigationStore', () => ({
  useNavigationStore: vi.fn()
}));

const mockUseNavigationStore = useNavigationStore as unknown as ReturnType<typeof vi.fn>;

describe('NavigationMenu', () => {
  const mockSetCurrentView = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    
    mockUseNavigationStore.mockReturnValue({
      currentView: 'chat',
      isKnowledgeBaseEditorOpen: false,
      setCurrentView: mockSetCurrentView,
      openKnowledgeBaseEditor: vi.fn(),
      closeKnowledgeBaseEditor: vi.fn(),
      toggleKnowledgeBaseEditor: vi.fn(),
    });
  });

  const renderNavigationMenu = () => {
    return render(<NavigationMenu />);
  };

  describe('Rendering', () => {
    it('should render all navigation items', () => {
      renderNavigationMenu();
      
      expect(screen.getByText('Chat')).toBeInTheDocument();
      expect(screen.getByText('Knowledge Base')).toBeInTheDocument();
    });

    it('should render navigation section heading', () => {
      renderNavigationMenu();
      
      expect(screen.getByText('Navigation')).toBeInTheDocument();
    });

    it('should display correct descriptions in tooltips', () => {
      renderNavigationMenu();
      
      const chatButton = screen.getByRole('button', { name: /chat/i });
      const knowledgeBaseButton = screen.getByRole('button', { name: /knowledge base/i });
      
      expect(chatButton).toHaveAttribute('title', 'Chat with ShadowScribe AI');
      expect(knowledgeBaseButton).toHaveAttribute('title', 'Edit character data and files');
    });

    it('should render proper icons for each navigation item', () => {
      renderNavigationMenu();
      
      // Check that buttons contain SVG icons (Lucide icons render as SVGs)
      const buttons = screen.getAllByRole('button');
      buttons.forEach(button => {
        const svg = button.querySelector('svg');
        expect(svg).toBeInTheDocument();
      });
    });
  });

  describe('Active State Management', () => {
    it('should highlight chat as active by default', () => {
      renderNavigationMenu();
      
      const chatButton = screen.getByRole('button', { name: /chat/i });
      expect(chatButton).toHaveClass('bg-purple-600', 'text-white');
      
      // Should show active indicator
      const activeIndicator = chatButton.querySelector('.bg-white.rounded-full');
      expect(activeIndicator).toBeInTheDocument();
    });

    it('should highlight knowledge base when active', () => {
      mockUseNavigationStore.mockReturnValue({
        currentView: 'knowledge-base',
        isKnowledgeBaseEditorOpen: true,
        setCurrentView: mockSetCurrentView,
        openKnowledgeBaseEditor: vi.fn(),
        closeKnowledgeBaseEditor: vi.fn(),
        toggleKnowledgeBaseEditor: vi.fn(),
      });

      renderNavigationMenu();
      
      const knowledgeBaseButton = screen.getByRole('button', { name: /knowledge base/i });
      expect(knowledgeBaseButton).toHaveClass('bg-purple-600', 'text-white');
      
      // Should show active indicator
      const activeIndicator = knowledgeBaseButton.querySelector('.bg-white.rounded-full');
      expect(activeIndicator).toBeInTheDocument();
    });

    it('should apply inactive styles to non-active items', () => {
      renderNavigationMenu();
      
      const knowledgeBaseButton = screen.getByRole('button', { name: /knowledge base/i });
      
      expect(knowledgeBaseButton).toHaveClass('text-gray-300', 'hover:bg-gray-700');
      
      // Should not show active indicators
      expect(knowledgeBaseButton.querySelector('.bg-white.rounded-full')).not.toBeInTheDocument();
    });
  });

  describe('Navigation Interactions', () => {
    it('should call setCurrentView when chat is clicked', () => {
      mockUseNavigationStore.mockReturnValue({
        currentView: 'knowledge-base',
        isKnowledgeBaseEditorOpen: true,
        setCurrentView: mockSetCurrentView,
        openKnowledgeBaseEditor: vi.fn(),
        closeKnowledgeBaseEditor: vi.fn(),
        toggleKnowledgeBaseEditor: vi.fn(),
      });

      renderNavigationMenu();
      
      const chatButton = screen.getByRole('button', { name: /chat/i });
      fireEvent.click(chatButton);
      
      expect(mockSetCurrentView).toHaveBeenCalledWith('chat');
    });

    it('should call setCurrentView when knowledge base is clicked', () => {
      renderNavigationMenu();
      
      const knowledgeBaseButton = screen.getByRole('button', { name: /knowledge base/i });
      fireEvent.click(knowledgeBaseButton);
      
      expect(mockSetCurrentView).toHaveBeenCalledWith('knowledge-base');
    });

    it('should handle multiple rapid clicks gracefully', () => {
      renderNavigationMenu();
      
      const knowledgeBaseButton = screen.getByRole('button', { name: /knowledge base/i });
      
      // Simulate rapid clicking
      fireEvent.click(knowledgeBaseButton);
      fireEvent.click(knowledgeBaseButton);
      fireEvent.click(knowledgeBaseButton);
      
      expect(mockSetCurrentView).toHaveBeenCalledTimes(3);
      expect(mockSetCurrentView).toHaveBeenCalledWith('knowledge-base');
    });
  });



  describe('Accessibility', () => {
    it('should have proper button roles', () => {
      renderNavigationMenu();
      
      const buttons = screen.getAllByRole('button');
      expect(buttons).toHaveLength(2); // Chat, Knowledge Base
    });

    it('should have descriptive button text', () => {
      renderNavigationMenu();
      
      expect(screen.getByRole('button', { name: /chat/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /knowledge base/i })).toBeInTheDocument();
    });

    it('should support keyboard navigation', () => {
      renderNavigationMenu();
      
      const buttons = screen.getAllByRole('button');
      buttons.forEach(button => {
        expect(button).not.toHaveAttribute('tabindex', '-1');
      });
    });

    it('should have proper ARIA attributes', () => {
      renderNavigationMenu();
      
      const buttons = screen.getAllByRole('button');
      buttons.forEach(button => {
        expect(button).toHaveAttribute('title');
      });
    });
  });

  describe('Visual Design', () => {
    it('should have proper spacing and layout', () => {
      renderNavigationMenu();
      
      const nav = screen.getByRole('navigation') || screen.getByText('Navigation').parentElement;
      expect(nav).toHaveClass('space-y-1');
      
      const container = screen.getByText('Navigation').parentElement;
      expect(container).toHaveClass('p-4', 'border-b', 'border-gray-700');
    });

    it('should have proper text styling for section heading', () => {
      renderNavigationMenu();
      
      const heading = screen.getByText('Navigation');
      expect(heading).toHaveClass('text-sm', 'font-medium', 'text-gray-400', 'uppercase', 'tracking-wide');
    });

    it('should have consistent icon sizing', () => {
      renderNavigationMenu();
      
      const buttons = screen.getAllByRole('button');
      buttons.forEach(button => {
        const icon = button.querySelector('svg');
        if (icon) {
          expect(icon).toHaveClass('w-4', 'h-4');
        }
      });
    });

    it('should truncate long text properly', () => {
      renderNavigationMenu();
      
      const buttons = screen.getAllByRole('button');
      buttons.forEach(button => {
        const textSpan = button.querySelector('span');
        if (textSpan) {
          expect(textSpan).toHaveClass('truncate');
        }
      });
    });
  });
});