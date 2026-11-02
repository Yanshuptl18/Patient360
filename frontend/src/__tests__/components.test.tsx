// @vitest-environment jsdom
import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ErrorBoundary } from '../components/ErrorBoundary';

const FaultyComponent: React.FC<{ shouldThrow?: boolean }> = ({ shouldThrow }) => {
  if (shouldThrow) {
    throw new Error('Simulated medical component failure');
  }
  return <div>Clinical View Ready</div>;
};

describe('Frontend Component Resilience & Error Boundary', () => {
  it('renders children normally when no exception is thrown', () => {
    render(
      <ErrorBoundary>
        <FaultyComponent shouldThrow={false} />
      </ErrorBoundary>
    );

    expect(screen.getByText('Clinical View Ready')).toBeDefined();
  });

  it('renders clinical recovery UI when child throws an exception', () => {
    // Suppress console.error for expected caught error
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {});

    render(
      <ErrorBoundary>
        <FaultyComponent shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(screen.getByText('Workspace Recovery')).toBeDefined();
    expect(screen.getByText('Reload Interface')).toBeDefined();
    expect(screen.getByText('Reset to Clean Session')).toBeDefined();

    spy.mockRestore();
  });
});
