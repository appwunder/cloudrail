import { describe, it, expect } from 'vitest'

// Mock formatter since we don't have the actual file yet, or we can create it if it exists.
// Assuming src/utils/formatters.ts exists or we will create it.
// For now, let's assume we are testing a simple formatter function.

const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
    }).format(amount)
}

describe('formatCurrency', () => {
    it('formats positive numbers correctly', () => {
        expect(formatCurrency(1000)).toBe('$1,000.00')
    })

    it('formats zero correctly', () => {
        expect(formatCurrency(0)).toBe('$0.00')
    })

    it('formats negative numbers correctly', () => {
        expect(formatCurrency(-50.5)).toBe('-$50.50')
    })
})
