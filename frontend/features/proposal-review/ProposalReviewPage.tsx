'use client';

import { useState, useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { proposalsApi, opportunitiesApi, type Proposal } from '@/lib/api';
import { useProposalStore } from '@/lib/store';
import { OpportunityPanel } from './OpportunityPanel';
import { ProposalEditor } from './ProposalEditor';
import { SourcesPanel } from './SourcesPanel';
import { ProposalToolbar } from './ProposalToolbar';
import { GenerateModal } from './GenerateModal';
import { cn } from '@/lib/utils';
import { AlertCircle, CheckCircle2, Loader2, Sparkles } from 'lucide-react';

interface ProposalReviewPageProps {
    proposalId?: string;
}

export function ProposalReviewPage({ proposalId }: ProposalReviewPageProps) {
    const queryClient = useQueryClient();
    const [showGenerateModal, setShowGenerateModal] = useState(!proposalId);
    const {
        activeProposal,
        setActiveProposal,
        selectedOpportunity,
        setSelectedOpportunity,
        highlightedSource,
        setHighlightedSource,
    } = useProposalStore();

    // Poll for in-progress proposals
    const { data: proposal, isLoading } = useQuery({
        queryKey: ['proposal', proposalId || activeProposal?.id],
        queryFn: () =>
            proposalsApi
                .get(proposalId || activeProposal!.id)
                .then((r) => r.data),
        enabled: !!(proposalId || activeProposal?.id),
        refetchInterval: (query) => {
            const data = query.state.data as Proposal | undefined;
            if (data?.status === 'pending' || data?.status === 'processing') return 3000;
            return false;
        },
    });

    // Sync fetched proposal into store (replaces removed onSuccess)
    useEffect(() => {
        if (proposal) {
            setActiveProposal(proposal);
            if (proposal.opportunity_id && !selectedOpportunity) {
                opportunitiesApi
                    .get(proposal.opportunity_id)
                    .then((r) => setSelectedOpportunity(r.data));
            }
        }
    }, [proposal]);

    const currentProposal = proposal || activeProposal;
    const isPolling =
        currentProposal?.status === 'pending' ||
        currentProposal?.status === 'processing';

    return (
        <div className="flex flex-col h-screen bg-background overflow-hidden">
            {/* Header */}
            <header className="border-b border-border bg-card/80 backdrop-blur-sm z-20 px-4 py-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-lg bg-govblue-600 flex items-center justify-center">
                            <Sparkles className="w-4 h-4 text-white" />
                        </div>
                        <div>
                            <h1 className="text-sm font-semibold text-foreground leading-none">GovPreneurs</h1>
                            <p className="text-xs text-muted-foreground">Auto-Proposal Generator</p>
                        </div>
                    </div>

                    {currentProposal && (
                        <StatusIndicator status={currentProposal.status} />
                    )}
                </div>

                <ProposalToolbar
                    proposal={currentProposal}
                    onGenerateNew={() => setShowGenerateModal(true)}
                    opportunityTitle={selectedOpportunity?.title}
                />
            </header>

            {/* Main 3-panel layout */}
            {!currentProposal && !isLoading ? (
                <EmptyState onGenerate={() => setShowGenerateModal(true)} />
            ) : isLoading ? (
                <LoadingState />
            ) : isPolling ? (
                <GeneratingState status={currentProposal!.status} />
            ) : currentProposal?.status === 'failed' ? (
                <ErrorState message={currentProposal.error_message} onRetry={() => setShowGenerateModal(true)} />
            ) : (
                <div className="flex flex-1 overflow-hidden">
                    {/* Left panel: Opportunity Details */}
                    <aside className="w-80 flex-shrink-0 border-r border-border overflow-y-auto scrollbar-thin bg-card/50">
                        <OpportunityPanel opportunity={selectedOpportunity} />
                    </aside>

                    {/* Center panel: Proposal Editor */}
                    <main className="flex-1 overflow-y-auto scrollbar-thin">
                        <ProposalEditor
                            proposal={currentProposal!}
                            onSourceClick={setHighlightedSource}
                        />
                    </main>

                    {/* Right panel: Sources */}
                    <aside className="w-72 flex-shrink-0 border-l border-border overflow-y-auto scrollbar-thin bg-card/50">
                        <SourcesPanel
                            proposal={currentProposal!}
                            highlightedSource={highlightedSource}
                            onSourceClick={setHighlightedSource}
                        />
                    </aside>
                </div>
            )}

            {/* Generate Modal */}
            {showGenerateModal && (
                <GenerateModal
                    onClose={() => setShowGenerateModal(false)}
                    onGenerated={(p) => {
                        setActiveProposal(p);
                        setShowGenerateModal(false);
                    }}
                />
            )}
        </div>
    );
}

function StatusIndicator({ status }: { status: string }) {
    const configs = {
        pending: { color: 'text-amber-600 bg-amber-50', label: 'Pending', icon: Loader2, spin: true },
        processing: { color: 'text-blue-600 bg-blue-50', label: 'Generating…', icon: Loader2, spin: true },
        completed: { color: 'text-emerald-600 bg-emerald-50', label: 'Complete', icon: CheckCircle2, spin: false },
        failed: { color: 'text-red-600 bg-red-50', label: 'Failed', icon: AlertCircle, spin: false },
    };
    const cfg = configs[status as keyof typeof configs] || configs.pending;
    const Icon = cfg.icon;

    return (
        <span className={cn('flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium', cfg.color)}>
            <Icon className={cn('w-3 h-3', cfg.spin && 'animate-spin')} />
            {cfg.label}
        </span>
    );
}

function EmptyState({ onGenerate }: { onGenerate: () => void }) {
    return (
        <div className="flex-1 flex items-center justify-center p-8">
            <div className="text-center max-w-md animate-fade-in">
                <div className="w-16 h-16 rounded-2xl bg-govblue-100 flex items-center justify-center mx-auto mb-4">
                    <Sparkles className="w-8 h-8 text-govblue-600" />
                </div>
                <h2 className="text-xl font-semibold mb-2">Generate Your First Proposal</h2>
                <p className="text-muted-foreground text-sm mb-6">
                    Select a government opportunity and your company profile to generate a fully compliant federal proposal in minutes.
                </p>
                <button
                    onClick={onGenerate}
                    className="inline-flex items-center gap-2 px-6 py-3 bg-govblue-600 text-white rounded-xl font-semibold text-sm hover:bg-govblue-700 transition-colors shadow-lg shadow-govblue-600/20 animate-pulse-glow"
                >
                    <Sparkles className="w-4 h-4" />
                    Generate Proposal
                </button>
            </div>
        </div>
    );
}

function LoadingState() {
    return (
        <div className="flex-1 flex items-center justify-center">
            <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
        </div>
    );
}

function GeneratingState({ status }: { status: string }) {
    return (
        <div className="flex-1 flex items-center justify-center p-8">
            <div className="text-center max-w-sm animate-fade-in">
                <div className="relative w-20 h-20 mx-auto mb-6">
                    <div className="absolute inset-0 rounded-full bg-govblue-100 animate-ping opacity-60" />
                    <div className="relative w-20 h-20 rounded-full bg-govblue-600 flex items-center justify-center">
                        <Sparkles className="w-8 h-8 text-white animate-pulse" />
                    </div>
                </div>
                <h2 className="text-xl font-semibold mb-2">AI is Writing Your Proposal</h2>
                <p className="text-muted-foreground text-sm mb-4">
                    Analyzing solicitation, matching capabilities, and drafting compliant sections…
                </p>
                <div className="flex justify-center gap-1">
                    {[0, 1, 2].map((i) => (
                        <div
                            key={i}
                            className="w-2 h-2 rounded-full bg-govblue-400"
                            style={{ animation: `bounce 1.2s ease-in-out ${i * 0.2}s infinite` }}
                        />
                    ))}
                </div>
            </div>
        </div>
    );
}

function ErrorState({ message, onRetry }: { message?: string; onRetry: () => void }) {
    return (
        <div className="flex-1 flex items-center justify-center p-8">
            <div className="text-center max-w-sm">
                <div className="w-16 h-16 rounded-2xl bg-red-100 flex items-center justify-center mx-auto mb-4">
                    <AlertCircle className="w-8 h-8 text-red-600" />
                </div>
                <h2 className="text-xl font-semibold mb-2">Generation Failed</h2>
                {message && <p className="text-sm text-muted-foreground mb-6 font-mono bg-muted p-3 rounded-lg">{message}</p>}
                <button
                    onClick={onRetry}
                    className="px-6 py-2.5 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition"
                >
                    Try Again
                </button>
            </div>
        </div>
    );
}
