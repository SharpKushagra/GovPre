'use client';

import { formatDate, formatCurrency, cn } from '@/lib/utils';
import type { Opportunity } from '@/lib/api';
import { Badge } from '@/components/ui/Badge';
import {
    Building2, Calendar, Clock, DollarSign, FileText,
    MapPin, Tag, Shield, Info, Paperclip,
} from 'lucide-react';

interface OpportunityPanelProps {
    opportunity?: Opportunity | null;
}

export function OpportunityPanel({ opportunity }: OpportunityPanelProps) {
    if (!opportunity) {
        return (
            <div className="p-6">
                <div className="space-y-3">
                    {[60, 80, 40, 70, 55].map((w, i) => (
                        <div
                            key={i}
                            className="h-4 rounded shimmer-bg"
                            style={{ width: `${w}%` }}
                        />
                    ))}
                </div>
            </div>
        );
    }

    const isActive = opportunity.active;
    const isDeadlineSoon =
        opportunity.response_deadline &&
        new Date(opportunity.response_deadline) < new Date(Date.now() + 7 * 86400_000);

    return (
        <div className="p-5 space-y-5">
            {/* Header */}
            <div>
                <div className="flex items-start justify-between gap-2 mb-2">
                    <Badge variant={isActive ? 'success' : 'secondary'}>
                        {isActive ? 'Active' : 'Inactive'}
                    </Badge>
                    {opportunity.notice_type && (
                        <Badge variant="outline" className="text-xs">
                            {opportunity.notice_type}
                        </Badge>
                    )}
                </div>
                <h2 className="text-sm font-semibold leading-snug text-foreground mt-2">
                    {opportunity.title}
                </h2>
                {opportunity.solicitation_number && (
                    <p className="text-xs text-muted-foreground mt-1 font-mono">
                        {opportunity.solicitation_number}
                    </p>
                )}
            </div>

            <div className="h-px bg-border" />

            {/* Key dates */}
            <Section title="Key Dates" icon={Calendar}>
                <InfoRow
                    icon={Calendar}
                    label="Posted"
                    value={formatDate(opportunity.posted_date)}
                />
                <InfoRow
                    icon={Clock}
                    label="Response Due"
                    value={formatDate(opportunity.response_deadline)}
                    className={cn(isDeadlineSoon && 'text-amber-600 font-semibold')}
                />
                {opportunity.archive_date && (
                    <InfoRow
                        icon={Clock}
                        label="Archive"
                        value={formatDate(opportunity.archive_date)}
                    />
                )}
            </Section>

            <div className="h-px bg-border" />

            {/* Agency */}
            <Section title="Agency" icon={Building2}>
                <InfoRow icon={Building2} label="Agency" value={opportunity.agency} />
                {opportunity.sub_agency && (
                    <InfoRow icon={Info} label="Sub-Agency" value={opportunity.sub_agency} />
                )}
                {opportunity.department && (
                    <InfoRow icon={Info} label="Department" value={opportunity.department} />
                )}
            </Section>

            <div className="h-px bg-border" />

            {/* Contract Details */}
            <Section title="Contract Details" icon={FileText}>
                {opportunity.naics_code && (
                    <InfoRow icon={Tag} label="NAICS" value={`${opportunity.naics_code}${opportunity.naics_description ? ` — ${opportunity.naics_description}` : ''}`} />
                )}
                {opportunity.set_aside_type && (
                    <InfoRow icon={Shield} label="Set-Aside" value={opportunity.set_aside_type} />
                )}
                {opportunity.contract_type && (
                    <InfoRow icon={FileText} label="Contract Type" value={opportunity.contract_type} />
                )}
                {opportunity.estimated_value && (
                    <InfoRow
                        icon={DollarSign}
                        label="Est. Value"
                        value={formatCurrency(opportunity.estimated_value)}
                    />
                )}
                {opportunity.place_of_performance && (
                    <InfoRow icon={MapPin} label="Location" value={opportunity.place_of_performance} />
                )}
            </Section>

            {/* Attachments */}
            {opportunity.attachments && opportunity.attachments.length > 0 && (
                <>
                    <div className="h-px bg-border" />
                    <Section title={`Attachments (${opportunity.attachments.length})`} icon={Paperclip}>
                        <div className="space-y-1.5">
                            {opportunity.attachments.map((att, i) => (
                                <a
                                    key={i}
                                    href={att.file_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="flex items-center gap-2 text-xs text-govblue-600 hover:text-govblue-800 hover:underline truncate"
                                    title={att.file_name}
                                >
                                    <Paperclip className="w-3 h-3 flex-shrink-0" />
                                    {att.file_name}
                                </a>
                            ))}
                        </div>
                    </Section>
                </>
            )}

            {/* Description */}
            {opportunity.description && (
                <>
                    <div className="h-px bg-border" />
                    <Section title="Description" icon={Info}>
                        <p className="text-xs text-muted-foreground leading-relaxed line-clamp-6">
                            {opportunity.description}
                        </p>
                    </Section>
                </>
            )}
        </div>
    );
}

function Section({
    title,
    icon: Icon,
    children,
}: {
    title: string;
    icon: React.ElementType;
    children: React.ReactNode;
}) {
    return (
        <div>
            <div className="flex items-center gap-1.5 mb-2">
                <Icon className="w-3.5 h-3.5 text-muted-foreground" />
                <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                    {title}
                </h3>
            </div>
            <div className="space-y-1.5">{children}</div>
        </div>
    );
}

function InfoRow({
    icon: Icon,
    label,
    value,
    className,
}: {
    icon: React.ElementType;
    label: string;
    value?: string | null;
    className?: string;
}) {
    if (!value) return null;
    return (
        <div className="flex gap-2">
            <span className="text-xs text-muted-foreground w-20 flex-shrink-0 pt-0.5">{label}</span>
            <span className={cn('text-xs text-foreground leading-snug', className)}>{value}</span>
        </div>
    );
}
