'use client';

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { proposalsApi } from '@/lib/api';
import { useProposalStore } from '@/lib/store';
import { Button } from '@/components/ui/Button';
import { PROPOSAL_SECTIONS, sectionLabel, TONES, cn } from '@/lib/utils';
import type { Proposal, ProposalSection } from '@/lib/api';
import {
    RefreshCw,
    Edit3,
    ChevronDown,
    ChevronUp,
    BookOpen,
    CheckSquare,
    FileText,
    Users,
    BarChart3,
    MessageSquare,
    Wand2,
    Save,
    X,
} from 'lucide-react';

const SECTION_ICONS: Record<string, React.ElementType> = {
    executive_summary: BookOpen,
    technical_approach: BarChart3,
    past_performance: CheckSquare,
    compliance_matrix: FileText,
    company_overview: Users,
    conclusion: MessageSquare,
};

interface ProposalEditorProps {
    proposal: Proposal;
    onSourceClick: (sourceId: string | null) => void;
}

export function ProposalEditor({ proposal, onSourceClick }: ProposalEditorProps) {
    const queryClient = useQueryClient();
    const {
        activeSection,
        setActiveSection,
        isRefining,
        setIsRefining,
        selectedTone,
    } = useProposalStore();

    const [editingSection, setEditingSection] = useState<string | null>(null);
    const [editContent, setEditContent] = useState('');
    const [refineInstruction, setRefineInstruction] = useState('');
    const [showRefineInput, setShowRefineInput] = useState<string | null>(null);
    const [expandedSections, setExpandedSections] = useState<Set<string>>(
        new Set(['executive_summary']),
    );

    const refineMutation = useMutation({
        mutationFn: ({ section, instruction }: { section: string; instruction: string }) =>
            proposalsApi.refine({
                proposal_id: proposal.id,
                section,
                instruction,
                tone: selectedTone,
            }),
        onMutate: ({ section }) => setIsRefining(section, true),
        onSuccess: (res) => {
            queryClient.setQueryData(['proposal', proposal.id], res.data);
            setShowRefineInput(null);
            setRefineInstruction('');
        },
        onSettled: (_, __, { section }) => setIsRefining(section, false),
    });

    const saveEditMutation = useMutation({
        mutationFn: ({ section, content }: { section: string; content: string }) =>
            proposalsApi.updateSection(proposal.id, section, content),
        onSuccess: (_, { section, content }) => {
            queryClient.setQueryData(['proposal', proposal.id], (old: Proposal | undefined) => {
                if (!old || !old.sections) return old;
                return {
                    ...old,
                    sections: {
                        ...old.sections,
                        [section]: {
                            ...(old.sections as any)[section],
                            content,
                        },
                    },
                };
            });
            setEditingSection(null);
        },
    });

    const toggleExpand = (section: string) => {
        setExpandedSections((prev) => {
            const next = new Set(prev);
            if (next.has(section)) next.delete(section);
            else next.add(section);
            return next;
        });
    };

    if (!proposal.sections) {
        return (
            <div className="flex items-center justify-center h-full text-muted-foreground">
                <p className="text-sm">No sections generated yet.</p>
            </div>
        );
    }

    return (
        <div className="max-w-3xl mx-auto px-6 py-8 space-y-4">
            {/* Section navigation tabs */}
            <div className="flex gap-1 overflow-x-auto scrollbar-thin pb-2 sticky top-0 bg-background/95 backdrop-blur-sm z-10 pt-1">
                {PROPOSAL_SECTIONS.map((key) => {
                    const Icon = SECTION_ICONS[key] || FileText;
                    const hasContent = !!(proposal.sections as any)[key]?.content;
                    return (
                        <button
                            key={key}
                            onClick={() => {
                                setActiveSection(key);
                                document.getElementById(`section-${key}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
                            }}
                            className={cn(
                                'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-all',
                                activeSection === key
                                    ? 'bg-govblue-600 text-white shadow-sm'
                                    : 'text-muted-foreground hover:text-foreground hover:bg-muted',
                                !hasContent && 'opacity-50',
                            )}
                        >
                            <Icon className="w-3 h-3" />
                            {sectionLabel(key)}
                        </button>
                    );
                })}
            </div>

            {/* Section cards */}
            {PROPOSAL_SECTIONS.map((sectionKey) => {
                const section = (proposal.sections as any)[sectionKey] as ProposalSection | undefined;
                const Icon = SECTION_ICONS[sectionKey] || FileText;
                const isExpanded = expandedSections.has(sectionKey);
                const isEditing = editingSection === sectionKey;
                const isCurrentlyRefining = isRefining[sectionKey];

                return (
                    <div
                        key={sectionKey}
                        id={`section-${sectionKey}`}
                        className={cn(
                            'proposal-section-card section-fade-in',
                            activeSection === sectionKey && 'ring-2 ring-govblue-500/30',
                        )}
                        onClick={() => setActiveSection(sectionKey)}
                    >
                        {/* Section header */}
                        <div className="flex items-center justify-between mb-4">
                            <div className="flex items-center gap-2.5">
                                <div className="w-8 h-8 rounded-lg bg-govblue-50 flex items-center justify-center">
                                    <Icon className="w-4 h-4 text-govblue-600" />
                                </div>
                                <h2 className="text-sm font-semibold">{sectionLabel(sectionKey)}</h2>
                            </div>

                            <div className="flex items-center gap-1">
                                {/* Refine */}
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    title="Refine with AI"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        setShowRefineInput(showRefineInput === sectionKey ? null : sectionKey);
                                    }}
                                >
                                    <Wand2 className="w-3.5 h-3.5 text-govblue-600" />
                                </Button>
                                {/* Edit */}
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    title="Edit manually"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        setEditingSection(sectionKey);
                                        setEditContent(section?.content || '');
                                    }}
                                >
                                    <Edit3 className="w-3.5 h-3.5" />
                                </Button>
                                {/* Expand/Collapse */}
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        toggleExpand(sectionKey);
                                    }}
                                >
                                    {isExpanded ? (
                                        <ChevronUp className="w-3.5 h-3.5" />
                                    ) : (
                                        <ChevronDown className="w-3.5 h-3.5" />
                                    )}
                                </Button>
                            </div>
                        </div>

                        {/* Refine input */}
                        {showRefineInput === sectionKey && (
                            <div className="mb-4 p-4 bg-govblue-50 rounded-lg border border-govblue-200 animate-fade-in">
                                <p className="text-xs font-medium text-govblue-700 mb-2">
                                    Refine this section with AI
                                </p>
                                <div className="flex gap-2">
                                    <input
                                        type="text"
                                        value={refineInstruction}
                                        onChange={(e) => setRefineInstruction(e.target.value)}
                                        placeholder="e.g., Make this more concise and highlight our certifications…"
                                        className="flex-1 text-sm px-3 py-2 rounded-lg border border-govblue-300 bg-white focus:outline-none focus:ring-2 focus:ring-govblue-500"
                                        onKeyDown={(e) => {
                                            if (e.key === 'Enter' && refineInstruction.trim()) {
                                                refineMutation.mutate({ section: sectionKey, instruction: refineInstruction });
                                            }
                                        }}
                                        autoFocus
                                    />
                                    <Button
                                        size="sm"
                                        isLoading={isCurrentlyRefining}
                                        disabled={!refineInstruction.trim()}
                                        onClick={() => refineMutation.mutate({ section: sectionKey, instruction: refineInstruction })}
                                    >
                                        <RefreshCw className="w-3.5 h-3.5" />
                                        Refine
                                    </Button>
                                    <Button variant="ghost" size="icon" onClick={() => setShowRefineInput(null)}>
                                        <X className="w-3.5 h-3.5" />
                                    </Button>
                                </div>
                            </div>
                        )}

                        {/* Section content */}
                        {isExpanded && (
                            <div className="animate-fade-in">
                                {isCurrentlyRefining ? (
                                    <SectionSkeleton />
                                ) : isEditing ? (
                                    <div className="space-y-3">
                                        <textarea
                                            value={editContent}
                                            onChange={(e) => setEditContent(e.target.value)}
                                            rows={12}
                                            className="w-full text-sm px-4 py-3 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-govblue-500 resize-y font-mono"
                                        />
                                        <div className="flex gap-2 justify-end">
                                            <Button variant="ghost" size="sm" onClick={() => setEditingSection(null)}>
                                                Cancel
                                            </Button>
                                            <Button
                                                size="sm"
                                                isLoading={saveEditMutation.isPending}
                                                onClick={() => saveEditMutation.mutate({ section: sectionKey, content: editContent })}
                                            >
                                                <Save className="w-3.5 h-3.5" />
                                                Save Changes
                                            </Button>
                                        </div>
                                    </div>
                                ) : section?.content ? (
                                    <ProposalSectionContent
                                        content={section.content}
                                        sources={section.sources || []}
                                        onSourceClick={onSourceClick}
                                    />
                                ) : (
                                    <p className="text-sm text-muted-foreground italic">
                                        Information not provided in company profile.
                                    </p>
                                )}
                            </div>
                        )}
                    </div>
                );
            })}
        </div>
    );
}

function ProposalSectionContent({
    content,
    sources,
    onSourceClick,
}: {
    content: string;
    sources: any[];
    onSourceClick: (id: string | null) => void;
}) {
    // Render content with clickable citation tags
    const renderedContent = content.split(/(\[Source:[^\]]+\])/g).map((part, idx) => {
        if (part.startsWith('[Source:') && part.endsWith(']')) {
            const source = sources.find((s) => s.citation === part);
            return (
                <span
                    key={idx}
                    className="citation-tag"
                    onClick={() => onSourceClick(source?.chunk_id || null)}
                    title={source?.snippet || part}
                >
                    {part}
                </span>
            );
        }
        // Render markdown-like formatting
        return (
            <span key={idx} className="whitespace-pre-wrap">
                {part}
            </span>
        );
    });

    return (
        <div className="prose prose-sm max-w-none text-foreground leading-relaxed">
            {renderedContent}
        </div>
    );
}

function SectionSkeleton() {
    return (
        <div className="space-y-3 animate-pulse">
            {[0.9, 0.8, 1, 0.7, 0.85].map((w, i) => (
                <div
                    key={i}
                    className="h-4 rounded shimmer-bg"
                    style={{ width: `${w * 100}%` }}
                />
            ))}
        </div>
    );
}
