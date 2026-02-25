'use client';

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { opportunitiesApi, ingestionApi, type Opportunity } from '@/lib/api';
import { useProposalStore } from '@/lib/store';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { formatDate, formatCurrency, truncate, cn } from '@/lib/utils';
import {
    Search, Filter, RefreshCw, ChevronLeft, ChevronRight,
    Building2, Calendar, DollarSign, Shield, Tag, ArrowRight,
    Sparkles, Globe, Clock,
} from 'lucide-react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

const SET_ASIDE_OPTIONS = [
    { value: '', label: 'All Set-Asides' },
    { value: 'SBA', label: 'Small Business' },
    { value: '8A', label: '8(a)' },
    { value: 'HZC', label: 'HUBZone' },
    { value: 'SDVOSB', label: 'SDVOSB' },
    { value: 'WOSB', label: 'WOSB' },
];

export default function OpportunitiesPage() {
    const router = useRouter();
    const { setSelectedOpportunity } = useProposalStore();
    const [page, setPage] = useState(1);
    const [search, setSearch] = useState('');
    const [naicsFilter, setNaicsFilter] = useState('');
    const [setAsideFilter, setSetAsideFilter] = useState('');
    const [searchInput, setSearchInput] = useState('');

    const { data, isLoading, isFetching, refetch } = useQuery({
        queryKey: ['opportunities', page, search, naicsFilter, setAsideFilter],
        queryFn: () =>
            opportunitiesApi
                .list({
                    page,
                    page_size: 15,
                    search: search || undefined,
                    naics_code: naicsFilter || undefined,
                    set_aside_type: setAsideFilter || undefined,
                    active: true,
                })
                .then((r) => r.data),
        staleTime: 30000,
    });

    const syncMutation = useMutation({
        mutationFn: () => ingestionApi.triggerSamgov(5),
    });

    const handleSearch = () => {
        setSearch(searchInput);
        setPage(1);
    };

    const handleSelectOpportunity = (opp: Opportunity) => {
        setSelectedOpportunity(opp);
        router.push('/proposal-review');
    };

    const totalPages = data ? Math.ceil(data.total / 15) : 1;

    return (
        <div className="min-h-screen bg-background">
            {/* Top nav */}
            <header className="border-b border-border bg-card/80 backdrop-blur-sm sticky top-0 z-20">
                <div className="max-w-7xl mx-auto px-6 py-3 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <Link href="/" className="flex items-center gap-2 group">
                            <div className="w-7 h-7 rounded-lg bg-govblue-600 flex items-center justify-center group-hover:bg-govblue-700 transition-colors">
                                <Sparkles className="w-3.5 h-3.5 text-white" />
                            </div>
                            <span className="font-bold text-sm text-foreground">GovPreneurs</span>
                        </Link>
                        <span className="text-muted-foreground">/</span>
                        <span className="text-sm font-medium text-foreground">Opportunities</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <Button
                            variant="outline"
                            size="sm"
                            isLoading={syncMutation.isPending}
                            onClick={() => syncMutation.mutate()}
                            title="Sync from SAM.gov"
                        >
                            <RefreshCw className="w-3.5 h-3.5" />
                            Sync SAM.gov
                        </Button>
                        <Link href="/proposal-review">
                            <Button size="sm" className="bg-govblue-600 hover:bg-govblue-700 text-white">
                                <Sparkles className="w-3.5 h-3.5" />
                                Proposal Editor
                            </Button>
                        </Link>
                    </div>
                </div>
            </header>

            <main className="max-w-7xl mx-auto px-6 py-8">
                {/* Page header */}
                <div className="mb-8">
                    <h1 className="text-2xl font-bold text-foreground mb-1">Government Opportunities</h1>
                    <p className="text-muted-foreground text-sm">
                        Browse and filter live opportunities from SAM.gov.
                        {data && (
                            <span className="ml-2 font-medium text-foreground">{data.total.toLocaleString()} total</span>
                        )}
                    </p>
                </div>

                {/* Search + Filters */}
                <div className="flex flex-wrap gap-3 mb-6">
                    <div className="relative flex-1 min-w-[280px]">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                        <input
                            value={searchInput}
                            onChange={(e) => setSearchInput(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                            placeholder="Search by title, solicitation number, or keyword…"
                            className="w-full pl-9 pr-4 py-2.5 text-sm border border-border rounded-xl bg-background focus:outline-none focus:ring-2 focus:ring-govblue-500 transition"
                        />
                    </div>
                    <input
                        value={naicsFilter}
                        onChange={(e) => { setNaicsFilter(e.target.value); setPage(1); }}
                        placeholder="NAICS code…"
                        className="w-32 px-3 py-2.5 text-sm border border-border rounded-xl bg-background focus:outline-none focus:ring-2 focus:ring-govblue-500"
                    />
                    <select
                        value={setAsideFilter}
                        onChange={(e) => { setSetAsideFilter(e.target.value); setPage(1); }}
                        className="px-3 py-2.5 text-sm border border-border rounded-xl bg-background focus:outline-none focus:ring-2 focus:ring-govblue-500"
                    >
                        {SET_ASIDE_OPTIONS.map((o) => (
                            <option key={o.value} value={o.value}>{o.label}</option>
                        ))}
                    </select>
                    <Button onClick={handleSearch} size="sm" variant="outline">
                        <Filter className="w-3.5 h-3.5" />
                        Filter
                    </Button>
                </div>

                {/* Sync notification */}
                {syncMutation.isSuccess && (
                    <div className="mb-4 p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-sm text-emerald-700 flex items-center gap-2">
                        <RefreshCw className="w-4 h-4" />
                        SAM.gov sync triggered! New opportunities will appear shortly.
                    </div>
                )}

                {/* Opportunities list */}
                {isLoading ? (
                    <div className="space-y-3">
                        {Array.from({ length: 8 }).map((_, i) => (
                            <div key={i} className="h-32 rounded-xl shimmer-bg" />
                        ))}
                    </div>
                ) : !data?.items.length ? (
                    <EmptyOpportunities onSync={() => syncMutation.mutate()} />
                ) : (
                    <div className="space-y-3">
                        {data.items.map((opp) => (
                            <OpportunityCard
                                key={opp.id}
                                opportunity={opp}
                                onSelect={() => handleSelectOpportunity(opp)}
                            />
                        ))}
                    </div>
                )}

                {/* Pagination */}
                {data && totalPages > 1 && (
                    <div className="flex items-center justify-between mt-8 pt-6 border-t border-border">
                        <p className="text-sm text-muted-foreground">
                            Page {page} of {totalPages} · {data.total} opportunities
                        </p>
                        <div className="flex gap-2">
                            <Button
                                variant="outline" size="sm"
                                disabled={page === 1}
                                onClick={() => setPage((p) => p - 1)}
                            >
                                <ChevronLeft className="w-4 h-4" />
                                Prev
                            </Button>
                            <Button
                                variant="outline" size="sm"
                                disabled={page >= totalPages}
                                onClick={() => setPage((p) => p + 1)}
                            >
                                Next
                                <ChevronRight className="w-4 h-4" />
                            </Button>
                        </div>
                    </div>
                )}

                {isFetching && !isLoading && (
                    <div className="text-center mt-4 text-xs text-muted-foreground">Refreshing…</div>
                )}
            </main>
        </div>
    );
}

function OpportunityCard({
    opportunity: opp,
    onSelect,
}: {
    opportunity: Opportunity;
    onSelect: () => void;
}) {
    const isDeadlineSoon =
        opp.response_deadline &&
        new Date(opp.response_deadline) < new Date(Date.now() + 7 * 86400_000);

    return (
        <div className="group bg-card border border-border rounded-xl p-5 hover:border-govblue-300 hover:shadow-md transition-all duration-200 card-hover">
            <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                    {/* Title */}
                    <div className="flex items-start gap-2 mb-2">
                        <h2 className="text-sm font-semibold text-foreground leading-snug group-hover:text-govblue-700 transition-colors">
                            {opp.title}
                        </h2>
                    </div>

                    {/* Meta row */}
                    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground mb-3">
                        {opp.agency && (
                            <span className="flex items-center gap-1">
                                <Building2 className="w-3 h-3" />
                                {truncate(opp.agency, 50)}
                            </span>
                        )}
                        {opp.solicitation_number && (
                            <span className="font-mono">{opp.solicitation_number}</span>
                        )}
                        {opp.place_of_performance && (
                            <span className="flex items-center gap-1">
                                <Globe className="w-3 h-3" />
                                {opp.place_of_performance}
                            </span>
                        )}
                    </div>

                    {/* Description */}
                    {opp.description && (
                        <p className="text-xs text-muted-foreground leading-relaxed line-clamp-2 mb-3">
                            {truncate(opp.description, 220)}
                        </p>
                    )}

                    {/* Badges */}
                    <div className="flex flex-wrap gap-1.5">
                        {opp.notice_type && (
                            <Badge variant="secondary">{opp.notice_type}</Badge>
                        )}
                        {opp.naics_code && (
                            <Badge variant="outline">
                                <Tag className="w-2.5 h-2.5" />
                                {opp.naics_code}
                            </Badge>
                        )}
                        {opp.set_aside_type && (
                            <Badge variant="default">
                                <Shield className="w-2.5 h-2.5" />
                                {opp.set_aside_type}
                            </Badge>
                        )}
                        {opp.estimated_value && (
                            <Badge variant="success">
                                <DollarSign className="w-2.5 h-2.5" />
                                {formatCurrency(opp.estimated_value)}
                            </Badge>
                        )}
                        {opp.processed && (
                            <Badge variant="success">Analyzed</Badge>
                        )}
                    </div>
                </div>

                {/* Right: dates + CTA */}
                <div className="flex flex-col items-end gap-3 flex-shrink-0">
                    <div className="text-right space-y-1">
                        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                            <Calendar className="w-3 h-3" />
                            Posted {formatDate(opp.posted_date)}
                        </div>
                        {opp.response_deadline && (
                            <div className={cn(
                                'flex items-center gap-1.5 text-xs',
                                isDeadlineSoon ? 'text-amber-600 font-semibold' : 'text-muted-foreground',
                            )}>
                                <Clock className="w-3 h-3" />
                                Due {formatDate(opp.response_deadline)}
                                {isDeadlineSoon && ' ⚠️'}
                            </div>
                        )}
                    </div>

                    <Button
                        size="sm"
                        onClick={onSelect}
                        className="opacity-0 group-hover:opacity-100 transition-opacity bg-govblue-600 hover:bg-govblue-700 text-white"
                    >
                        <Sparkles className="w-3.5 h-3.5" />
                        Generate Proposal
                        <ArrowRight className="w-3 h-3" />
                    </Button>
                </div>
            </div>
        </div>
    );
}

function EmptyOpportunities({ onSync }: { onSync: () => void }) {
    return (
        <div className="text-center py-20">
            <div className="w-16 h-16 rounded-2xl bg-muted flex items-center justify-center mx-auto mb-4">
                <Building2 className="w-8 h-8 text-muted-foreground/40" />
            </div>
            <h3 className="text-lg font-semibold mb-2">No Opportunities Found</h3>
            <p className="text-sm text-muted-foreground mb-6 max-w-sm mx-auto">
                Your database is empty. Trigger a SAM.gov sync to ingest the latest federal opportunities.
            </p>
            <Button onClick={onSync} className="bg-govblue-600 hover:bg-govblue-700 text-white">
                <RefreshCw className="w-4 h-4" />
                Sync from SAM.gov Now
            </Button>
        </div>
    );
}
