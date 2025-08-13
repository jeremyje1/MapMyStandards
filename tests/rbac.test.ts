import { describe, it, expect } from 'vitest';
import { roleSatisfies } from '@/lib/rbac';

describe('roleSatisfies', () => {
  it('OWNER satisfies all roles', () => {
    expect(roleSatisfies('OWNER', 'VIEWER')).toBe(true);
    expect(roleSatisfies('OWNER', 'CONTRIBUTOR')).toBe(true);
    expect(roleSatisfies('OWNER', 'OWNER')).toBe(true);
  });

  it('CONTRIBUTOR satisfies viewer but not owner', () => {
    expect(roleSatisfies('CONTRIBUTOR', 'VIEWER')).toBe(true);
    expect(roleSatisfies('CONTRIBUTOR', 'CONTRIBUTOR')).toBe(true);
    expect(roleSatisfies('CONTRIBUTOR', 'OWNER')).toBe(false);
  });

  it('VIEWER only satisfies itself', () => {
    expect(roleSatisfies('VIEWER', 'VIEWER')).toBe(true);
    expect(roleSatisfies('VIEWER', 'CONTRIBUTOR')).toBe(false);
    expect(roleSatisfies('VIEWER', 'OWNER')).toBe(false);
  });
});
