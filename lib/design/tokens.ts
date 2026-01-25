/**
 * Design Tokens - TypeScript helpers
 * 
 * Provides type-safe access to design tokens defined in globals.css
 * Use these helpers for programmatic access to design tokens.
 */

export const tokens = {
  colors: {
    primary: 'var(--color-primary)',
    primaryLight: 'var(--color-primary-light)',
    primaryDark: 'var(--color-primary-dark)',
    danger: 'var(--color-danger)',
    dangerLight: 'var(--color-danger-light)',
    dangerDark: 'var(--color-danger-dark)',
    success: 'var(--color-success)',
    successLight: 'var(--color-success-light)',
    successDark: 'var(--color-success-dark)',
    warning: 'var(--color-warning)',
    warningLight: 'var(--color-warning-light)',
    warningDark: 'var(--color-warning-dark)',
    info: 'var(--color-info)',
    infoLight: 'var(--color-info-light)',
    infoDark: 'var(--color-info-dark)',
    neutral: 'var(--color-neutral)',
    neutralLight: 'var(--color-neutral-light)',
    neutralDark: 'var(--color-neutral-dark)',
    neutralDarker: 'var(--color-neutral-darker)',
    text: 'var(--color-text)',
    textLight: 'var(--color-text-light)',
    textDark: 'var(--color-text-dark)',
    surface: 'var(--color-surface)',
    surfaceLight: 'var(--color-surface-light)',
    surfaceDark: 'var(--color-surface-dark)',
  },
} as const
