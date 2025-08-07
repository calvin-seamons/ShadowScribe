import React, { ErrorInfo, ReactNode } from 'react';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
}

export class SourceUsageErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('SourceUsageDisplay Error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="mt-4 p-3 bg-red-900/20 border border-red-600/50 rounded-lg">
          <div className="text-sm text-red-400">
            Error displaying source usage information
          </div>
          <div className="text-xs text-red-300 mt-1">
            {this.state.error?.message}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
