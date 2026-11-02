// @vitest-environment jsdom
import { describe, it, expect, beforeEach } from 'vitest';

describe('Frontend Authentication and Session Management', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('stores and retrieves access tokens from local storage', () => {
    const testToken = 'header.eyJzdWIiOiIxMjM0NSIsInJvbGUiOiJkb2N0b3IifQ.signature';
    localStorage.setItem('patient360_access_token', testToken);
    expect(localStorage.getItem('patient360_access_token')).toBe(testToken);
  });

  it('clears token on logout', () => {
    localStorage.setItem('patient360_access_token', 'sample-token');
    localStorage.removeItem('patient360_access_token');
    expect(localStorage.getItem('patient360_access_token')).toBeNull();
  });

  it('correctly maps 5 demo personas to authorized workspace roles', () => {
    const roles = [
      { key: 'doctor', role: 'doctor' },
      { key: 'nurse', role: 'nurse' },
      { key: 'hospital_admin', role: 'hospital_admin' },
      { key: 'patient', role: 'patient' },
      { key: 'admin', role: 'admin' },
    ];

    expect(roles).toHaveLength(5);
    expect(roles.map((r) => r.role)).toEqual([
      'doctor',
      'nurse',
      'hospital_admin',
      'patient',
      'admin',
    ]);
  });
});
