'use client';

/**
 * Error Boundary Component
 * 
 * Catches errors in React component tree and displays user-friendly error messages.
 */

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { BaseError } from '@/lib/errors';

interface Props {
  children: ReactNode;
  fallback?: (error: Error, reset: () => void) => ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Log error to console in development
    if (process.env.NODE_ENV === 'development') {
      console.error('ErrorBoundary caught an error:', error, errorInfo);
    }

    // TODO: Send error to error tracking service (Sentry) when integrated
    // if (error instanceof BaseError) {
    //   Sentry.captureException(error, {
    //     contexts: {
    //       react: {
    //         componentStack: errorInfo.componentStack,
    //       },
    //     },
    //   });
    // }
  }

  handleReset = (): void => {
    this.setState({
      hasError: false,
      error: null,
    });
  };

  render(): ReactNode {
    if (this.state.hasError && this.state.error) {
      if (this.props.fallback) {
        return this.props.fallback(this.state.error, this.handleReset);
      }

      // Default error UI
      return (
        <div className="flex min-h-screen flex-col items-center justify-center p-4">
          <div className="w-full max-w-md rounded-lg border border-neutral/20 bg-surface-light p-6 shadow-lg">
            <h2 className="mb-4 text-xl font-semibold text-text">
              Something went wrong
            </h2>
            <p className="mb-4 text-text-light">
              {this.state.error instanceof BaseError
                ? this.state.error.getUserMessage()
                : 'An unexpected error occurred. Please try again.'}
            </p>
            <button
              onClick={this.handleReset}
              className="btn-primary w-full"
              type="button"
            >
              Try again
            </button>
            {process.env.NODE_ENV === 'development' && (
              <details className="mt-4">
                <summary className="cursor-pointer text-sm text-text-light">
                  Error details (development only)
                </summary>
                <pre className="mt-2 overflow-auto rounded bg-neutral p-2 text-xs text-text">
                  {this.state.error.stack}
                </pre>
              </details>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
