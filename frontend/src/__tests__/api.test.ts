import { describe, it, expect } from 'vitest';
import { ApiError } from '../services/api';

describe('Centralized API Service and Error Handling', () => {
  it('instantiates ApiError with status code and error message', () => {
    const error = new ApiError('Patient record not found', 404, 'ENTITY_NOT_FOUND', {
      resource: 'SYNTH-99999',
    });

    expect(error.name).toBe('ApiError');
    expect(error.message).toBe('Patient record not found');
    expect(error.statusCode).toBe(404);
    expect(error.code).toBe('ENTITY_NOT_FOUND');
    expect(error.details).toEqual({ resource: 'SYNTH-99999' });
  });

  it('handles network error fallback with zero status code', () => {
    const networkError = new ApiError('Network connection lost', 0, 'NETWORK_ERROR');
    expect(networkError.statusCode).toBe(0);
    expect(networkError.code).toBe('NETWORK_ERROR');
  });
});
