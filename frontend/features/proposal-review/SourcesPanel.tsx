'use client';

import { cn } from '@/lib/utils';
import type { Proposal, ProposalSource } from '@/lib/api';
import { PROPOSAL_SECTIONS, sectionLabel } from '@/lib/utils';
import { BookOpen, ExternalLink, FileSearch } from 'lucide-react';
import { useProposalStore } from '@/lib/store';

interface SourcesPanelProps {
    proposal: Proposal;
    highlightedSource: string | null;
    onSourceClick: (id: string | null) => void;
}

export function SourcesPanel({ proposal, highlightedSource, onSourceClick }: SourcesPanelProps) {
    const { activeSection } = useProposalStore();

    // Gather sources from the active section
    const activeSectionData = proposal.sections
        ? (proposal.sections as any)[activeSection]
        : null;
    const sources: ProposalSource[] = activeSectionData?.sources || [];

    // Also gather all unique sources
    const allSources: { section: string; sources: ProposalSource[] }[] = [];
    if (proposal.sections) {
        PROPOSAL_SECTIONS.forEach((key) => {
            const sec = (proposal.sections as any)[key];
            if (sec?.sources?.length) {
                allSources.push({ section: key, sources: sec.sources });
            }
        });
    }

    return (
        <div className="p-4 space-y-4">
            <div className="flex items-center gap-2">
                <FileSearch className="w-4 h-4 text-govblue-600" />
                <h3 className="text-sm font-semibold">Sources & Citations</h3>
            </div>

            {/* Active section sources */}
            {sources.length > 0 ? (
                <div className="space-y-2">
                    <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                        {sectionLabel(activeSection)}
                    </p>
                    {sources.map((src, i) => (
                        <SourceCard
                            key={i}
                            source={src}
                            isHighlighted={highlightedSource === src.chunk_id}
                            onClick={() =>
                                onSourceClick(highlightedSource === src.chunk_id ? null : (src.chunk_id || null))
                            }
                        />
                    ))}
                </div>
            ) : (
                <div className="text-center py-6">
                    <BookOpen className="w-8 h-8 text-muted-foreground/30 mx-auto mb-2" />
                    <p className="text-xs text-muted-foreground">No sources for this section</p>
                </div>
            )}

            {/* All sources by section */}
            {allSources.length > 0 && (
                <div className="space-y-3 pt-2 border-t border-border">
                    <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                        All References
                    </p>
                    {allSources.map(({ section, sources: sectionSources }) => (
                        <div key={section}>
                            <p className="text-xs text-muted-foreground mb-1 font-medium">
                                {sectionLabel(section)}
                            </p>
                            <div className="space-y-1">
                                {sectionSources.slice(0, 3).map((src, i) => (
                                    <div
                                        key={i}
                                        className="text-xs text-govblue-600 hover:text-govblue-800 cursor-pointer truncate"
                                        onClick={() => onSourceClick(src.chunk_id || null)}
                                        title={src.citation}
                                    >
                                        • {src.citation}
                                    </div>
                                ))}
                                {sectionSources.length > 3 && (
                                    <p className="text-xs text-muted-foreground">
                                        +{sectionSources.length - 3} more
                                    </p>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

function SourceCard({
    source,
    isHighlighted,
    onClick,
}: {
    source: ProposalSource;
    isHighlighted: boolean;
    onClick: () => void;
}) {
    return (
        <div
            onClick={onClick}
            className={cn(
                'p-3 rounded-lg border cursor-pointer transition-all duration-150',
                isHighlighted
                    ? 'border-govblue-400 bg-govblue-50 shadow-sm'
                    : 'border-border hover:border-govblue-300 hover:bg-accent/50',
            )}
        >
            <div className="flex items-start justify-between gap-2 mb-1">
                <p className="text-xs font-medium text-govblue-700 leading-tight">
                    {source.citation}
                </p>
                {isHighlighted && <div className="w-2 h-2 rounded-full bg-govblue-500 flex-shrink-0" />}
            </div>
            {source.snippet && (
                <p className="text-xs text-muted-foreground leading-relaxed line-clamp-3">
                    {source.snippet}
                </p>
            )}
            {source.source_file && source.source_file !== '[Description]' && (
                <div className="flex items-center gap-1 mt-1.5">
                    <ExternalLink className="w-2.5 h-2.5 text-muted-foreground" />
                    <span className="text-xs text-muted-foreground truncate">{source.source_file}</span>
                </div>
            )}
        </div>
    );
}
