import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { format, parseISO, isValid } from 'date-fns';

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

export function formatDate(dateStr?: string | null, fmt = 'MMM dd, yyyy'): string {
    if (!dateStr) return '—';
    try {
        const date = parseISO(dateStr);
        return isValid(date) ? format(date, fmt) : '—';
    } catch {
        return '—';
    }
}

export function formatCurrency(value?: string | null): string {
    if (!value) return 'TBD';
    const num = parseFloat(value.replace(/[^0-9.]/g, ''));
    if (isNaN(num)) return value;
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        maximumFractionDigits: 0,
    }).format(num);
}

export function truncate(str: string, maxLen: number): string {
    if (str.length <= maxLen) return str;
    return str.slice(0, maxLen).trimEnd() + '…';
}

export function sectionLabel(key: string): string {
    const labels: Record<string, string> = {
        executive_summary: 'Executive Summary',
        technical_approach: 'Technical Approach',
        past_performance: 'Past Performance',
        compliance_matrix: 'Compliance Matrix',
        company_overview: 'Company Overview',
        conclusion: 'Conclusion',
    };
    return labels[key] ?? key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

export const PROPOSAL_SECTIONS = [
    'executive_summary',
    'technical_approach',
    'past_performance',
    'compliance_matrix',
    'company_overview',
    'conclusion',
] as const;

export type ProposalSectionKey = (typeof PROPOSAL_SECTIONS)[number];

export const TONES = [
    { value: 'professional', label: 'Professional' },
    { value: 'assertive', label: 'Assertive' },
    { value: 'concise', label: 'Concise' },
    { value: 'detailed', label: 'Detailed' },
] as const;

export const SET_ASIDE_LABELS: Record<string, string> = {
    'SBA': 'Small Business',
    'SBP': 'Small Business Set-Aside (Partial)',
    '8A': '8(a) Business Development',
    'HZC': 'HUBZone',
    'SDVOSB': 'Service-Disabled Veteran-Owned',
    'WOSB': 'Women-Owned Small Business',
    'EDWOSB': 'Economically Disadvantaged WOSB',
};
