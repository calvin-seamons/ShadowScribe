import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { CharacterCreationSelection } from '../CharacterCreationSelection';

describe('CharacterCreationSelection', () => {
  const mockOnSelectPDFImport = vi.fn();
  const mockOnSelectManualWizard = vi.fn();
  const mockOnCancel = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderComponent = () => {
    return render(
      <CharacterCreationSelection
        onSelectPDFImport={mockOnSelectPDFImport}
        onSelectManualWizard={mockOnSelectManualWizard}
        onCancel={mockOnCancel}
      />
    );
  };

  describe('Rendering', () => {
    it('should render the main heading and description', () => {
      renderComponent();
      
      expect(screen.getByText('Create New Character')).toBeInTheDocument();
      expect(screen.getByText('Choose how you\'d like to create your character')).toBeInTheDocument();
    });

    it('should render PDF import option with correct content', () => {
      renderComponent();
      
      expect(screen.getByText('Import from PDF')).toBeInTheDocument();
      expect(screen.getByText(/Upload your existing character sheet PDF/)).toBeInTheDocument();
      expect(screen.getByText('Upload PDF Character Sheet')).toBeInTheDocument();
      
      // Check feature bullets
      expect(screen.getByText('Fast and automated')).toBeInTheDocument();
      expect(screen.getByText('AI-powered data extraction')).toBeInTheDocument();
      expect(screen.getByText('Review and edit before saving')).toBeInTheDocument();
      expect(screen.getByText('Requires readable PDF file')).toBeInTheDocument();
    });

    it('should render manual wizard option with correct content', () => {
      renderComponent();
      
      expect(screen.getByText('Manual Creation Wizard')).toBeInTheDocument();
      expect(screen.getByText(/Create your character step-by-step/)).toBeInTheDocument();
      expect(screen.getByText('Start Manual Wizard')).toBeInTheDocument();
      
      // Check feature bullets
      expect(screen.getByText('Step-by-step guidance')).toBeInTheDocument();
      expect(screen.getByText('Complete control over details')).toBeInTheDocument();
      expect(screen.getByText('Built-in validation and help')).toBeInTheDocument();
      expect(screen.getByText('Takes more time to complete')).toBeInTheDocument();
    });

    it('should render help section', () => {
      renderComponent();
      
      expect(screen.getByText('Need Help Choosing?')).toBeInTheDocument();
      expect(screen.getByText(/Choose PDF Import if:/)).toBeInTheDocument();
      expect(screen.getByText(/Choose Manual Wizard if:/)).toBeInTheDocument();
    });

    it('should render cancel button', () => {
      renderComponent();
      
      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      expect(cancelButton).toBeInTheDocument();
    });
  });

  describe('Interactions', () => {
    it('should call onSelectPDFImport when PDF import button is clicked', () => {
      renderComponent();
      
      const pdfImportButton = screen.getByText('Upload PDF Character Sheet');
      fireEvent.click(pdfImportButton);
      
      expect(mockOnSelectPDFImport).toHaveBeenCalledTimes(1);
    });

    it('should call onSelectManualWizard when manual wizard button is clicked', () => {
      renderComponent();
      
      const manualWizardButton = screen.getByText('Start Manual Wizard');
      fireEvent.click(manualWizardButton);
      
      expect(mockOnSelectManualWizard).toHaveBeenCalledTimes(1);
    });

    it('should call onCancel when cancel button is clicked', () => {
      renderComponent();
      
      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      fireEvent.click(cancelButton);
      
      expect(mockOnCancel).toHaveBeenCalledTimes(1);
    });
  });

  describe('Visual Design', () => {
    it('should have proper hover effects on option cards', () => {
      renderComponent();
      
      // Find the card containers (they should be the parent divs with the hover classes)
      const cards = screen.getAllByText(/Import from PDF|Manual Creation Wizard/);
      const pdfCard = cards[0].closest('.group');
      const manualCard = cards[1].closest('.group');
      
      expect(pdfCard).toHaveClass('hover:border-purple-500');
      expect(manualCard).toHaveClass('hover:border-blue-500');
    });

    it('should have proper button styling', () => {
      renderComponent();
      
      const pdfButton = screen.getByRole('button', { name: /upload pdf character sheet/i });
      const manualButton = screen.getByRole('button', { name: /start manual wizard/i });
      
      expect(pdfButton).toHaveClass('bg-purple-600', 'hover:bg-purple-700');
      expect(manualButton).toHaveClass('bg-blue-600', 'hover:bg-blue-700');
    });

    it('should display proper icons', () => {
      renderComponent();
      
      // Check that Upload and Edit icons are present (via their parent containers)
      const iconContainers = screen.getAllByRole('button').slice(1, 3); // Skip cancel button
      expect(iconContainers).toHaveLength(2);
    });
  });

  describe('Accessibility', () => {
    it('should have proper button roles and labels', () => {
      renderComponent();
      
      expect(screen.getByRole('button', { name: /upload pdf character sheet/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /start manual wizard/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
    });

    it('should have proper heading hierarchy', () => {
      renderComponent();
      
      const mainHeading = screen.getByRole('heading', { level: 1 });
      expect(mainHeading).toHaveTextContent('Create New Character');
      
      const subHeadings = screen.getAllByRole('heading', { level: 3 });
      expect(subHeadings).toHaveLength(2);
      expect(subHeadings[0]).toHaveTextContent('Import from PDF');
      expect(subHeadings[1]).toHaveTextContent('Manual Creation Wizard');
    });

    it('should support keyboard navigation', () => {
      renderComponent();
      
      const buttons = screen.getAllByRole('button');
      buttons.forEach(button => {
        expect(button).not.toHaveAttribute('tabindex', '-1');
      });
    });
  });

  describe('Responsive Design', () => {
    it('should have responsive grid classes', () => {
      renderComponent();
      
      // Find the grid container by looking for the element with grid classes
      const gridElement = document.querySelector('.grid.grid-cols-1.md\\:grid-cols-2');
      expect(gridElement).toBeInTheDocument();
      expect(gridElement).toHaveClass('grid-cols-1', 'md:grid-cols-2');
    });

    it('should have responsive spacing classes', () => {
      renderComponent();
      
      // Find the max-width container
      const maxWidthElement = document.querySelector('.max-w-4xl');
      expect(maxWidthElement).toBeInTheDocument();
      expect(maxWidthElement).toHaveClass('max-w-4xl');
    });
  });
});