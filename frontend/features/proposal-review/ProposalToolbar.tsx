'use client';

import { useProposalStore } from '@/lib/store';
import { Button } from '@/components/ui/Button';
import type { Proposal } from '@/lib/api';
import { TONES } from '@/lib/utils';
import {
    Download, FileText, Sparkles, RotateCcw,
} from 'lucide-react';
import { useState } from 'react';

interface ProposalToolbarProps {
    proposal?: Proposal | null;
    onGenerateNew: () => void;
    opportunityTitle?: string;
}

export function ProposalToolbar({
    proposal,
    onGenerateNew,
    opportunityTitle,
}: ProposalToolbarProps) {
    const { selectedTone, setSelectedTone } = useProposalStore();
    const [isExporting, setIsExporting] = useState(false);

    const handleExportPDF = async () => {
        if (!proposal) return;
        setIsExporting(true);
        try {
            // Build printable HTML content
            const content = buildExportHTML(proposal, opportunityTitle);
            const printWindow = window.open('', '_blank');
            if (printWindow) {
                printWindow.document.write(content);
                printWindow.document.close();
                printWindow.print();
            }
        } finally {
            setIsExporting(false);
        }
    };

    const handleExportWord = async () => {
        if (!proposal?.sections) return;
        setIsExporting(true);
        try {
            const content = buildExportText(proposal, opportunityTitle);
            const blob = new Blob([content], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `proposal-${proposal.id.slice(0, 8)}.txt`;
            a.click();
            URL.revokeObjectURL(url);
        } finally {
            setIsExporting(false);
        }
    };

    return (
        <div className="flex items-center gap-2">
            {/* Tone selector */}
            <select
                value={selectedTone}
                onChange={(e) => setSelectedTone(e.target.value)}
                className="text-xs border border-border rounded-lg px-2.5 py-1.5 bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-govblue-500"
                title="Proposal tone"
            >
                {TONES.map((t) => (
                    <option key={t.value} value={t.value}>{t.label}</option>
                ))}
            </select>

            {proposal?.status === 'completed' && (
                <>
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={handleExportPDF}
                        isLoading={isExporting}
                        title="Export as PDF"
                    >
                        <FileText className="w-3.5 h-3.5" />
                        PDF
                    </Button>
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={handleExportWord}
                        isLoading={isExporting}
                        title="Export as Word"
                    >
                        <Download className="w-3.5 h-3.5" />
                        Word
                    </Button>
                </>
            )}

            <Button
                size="sm"
                onClick={onGenerateNew}
                className="bg-govblue-600 hover:bg-govblue-700 text-white"
            >
                <Sparkles className="w-3.5 h-3.5" />
                New Proposal
            </Button>
        </div>
    );
}

// ── Export helpers ─────────────────────────────────────────────────────────────

const SECTION_LABELS: Record<string, string> = {
    executive_summary: 'Executive Summary',
    technical_approach: 'Technical Approach',
    past_performance: 'Past Performance',
    compliance_matrix: 'Compliance Matrix',
    company_overview: 'Company Overview',
    conclusion: 'Conclusion',
};

function buildExportHTML(proposal: Proposal, title?: string): string {
    const sections = proposal.sections || {};
    const sectionBlocks = Object.entries(sections)
        .map(([key, sec]: [string, any]) => {
            if (!sec?.content) return '';
            return `
        <div style="margin-bottom: 32px; page-break-inside: avoid;">
          <h2 style="font-size: 16px; font-weight: 700; color: #1a3e72; border-bottom: 2px solid #1a3e72; padding-bottom: 6px; margin-bottom: 12px;">
            ${SECTION_LABELS[key] || key}
          </h2>
          <p style="font-size: 13px; line-height: 1.8; white-space: pre-wrap;">${sec.content}</p>
        </div>
      `;
        })
        .join('');

    return `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Government Contract Proposal</title>
  <style>
    body { font-family: 'Georgia', serif; max-width: 800px; margin: 0 auto; padding: 40px; color: #1a1a2e; }
    h1 { font-size: 22px; font-weight: 700; color: #1a3e72; margin-bottom: 6px; }
    .meta { font-size: 12px; color: #666; margin-bottom: 32px; }
    @media print { body { padding: 20px; } }
  </style>
</head>
<body>
  <h1>${title || 'Government Contract Proposal'}</h1>
  <div class="meta">Generated by GovPreneurs Auto-Proposal · Version ${proposal.version}</div>
  ${sectionBlocks}
</body>
</html>`;
}

function buildExportText(proposal: Proposal, title?: string): string {
    const sections = proposal.sections || {};
    const header = `GOVERNMENT CONTRACT PROPOSAL\n${'='.repeat(50)}\n${title || 'Proposal'}\nGenerated by GovPreneurs Auto-Proposal | Version ${proposal.version}\n\n`;

    const sectionBlocks = Object.entries(sections)
        .map(([key, sec]: [string, any]) => {
            if (!sec?.content) return '';
            const label = SECTION_LABELS[key] || key;
            return `${label.toUpperCase()}\n${'-'.repeat(label.length)}\n\n${sec.content}\n\n`;
        })
        .join('');

    return header + sectionBlocks;
}
