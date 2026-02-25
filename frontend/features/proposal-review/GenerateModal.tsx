'use client';

import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { opportunitiesApi, profilesApi, proposalsApi, ingestionApi, type Proposal } from '@/lib/api';
import { useProposalStore } from '@/lib/store';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { TONES, formatDate, truncate } from '@/lib/utils';
import {
    X, Sparkles, Search, Building2, Plus, ChevronRight, CheckCircle,
} from 'lucide-react';

interface GenerateModalProps {
    onClose: () => void;
    onGenerated: (proposal: Proposal) => void;
}

type Step = 'select-opportunity' | 'select-profile' | 'confirm';

export function GenerateModal({ onClose, onGenerated }: GenerateModalProps) {
    const [step, setStep] = useState<Step>('select-opportunity');
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedOpportunityId, setSelectedOpportunityId] = useState<string | null>(null);
    const [selectedProfileId, setSelectedProfileId] = useState<string | null>(null);
    const [profileForm, setProfileForm] = useState({
        company_name: '',
        capabilities_statement: '',
        past_performance: '',
        certifications: '',
        naics_codes: '',
        set_asides: '',
        location: '',
        years_experience: '',
    });
    const [showProfileForm, setShowProfileForm] = useState(false);
    const { selectedTone, setSelectedTone, setSelectedOpportunity } = useProposalStore();

    const { data: opportunities, isLoading: oppsLoading } = useQuery({
        queryKey: ['opportunities', searchQuery],
        queryFn: () => opportunitiesApi.list({ search: searchQuery || undefined, page_size: 20 }).then((r) => r.data),
        staleTime: 30000,
    });

    // Create profile mutation
    const createProfileMutation = useMutation({
        mutationFn: (data: typeof profileForm) =>
            profilesApi.create({
                ...data,
                naics_codes: data.naics_codes ? data.naics_codes.split(',').map((s) => s.trim()) : [],
                set_asides: data.set_asides ? data.set_asides.split(',').map((s) => s.trim()) : [],
                years_experience: data.years_experience ? parseInt(data.years_experience) : undefined,
            }),
        onSuccess: (res) => {
            setSelectedProfileId(res.data.id);
            setShowProfileForm(false);
            setStep('confirm');
        },
    });

    const generateMutation = useMutation({
        mutationFn: () =>
            proposalsApi.generate({
                opportunity_id: selectedOpportunityId!,
                user_profile_id: selectedProfileId!,
                tone: selectedTone,
            }),
        onSuccess: async (res) => {
            // Fetch full proposal to pass back
            const proposalRes = await proposalsApi.get(res.data.proposal_id);
            if (selectedOpportunityId) {
                const oppRes = await opportunitiesApi.get(selectedOpportunityId);
                setSelectedOpportunity(oppRes.data);
            }
            onGenerated(proposalRes.data);
        },
    });

    const selectedOpp = opportunities?.items.find((o) => o.id === selectedOpportunityId);

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />
            <div className="relative bg-card border border-border rounded-2xl shadow-2xl w-full max-w-2xl overflow-hidden animate-fade-in">
                {/* Modal header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-gradient-to-r from-govblue-600 to-govblue-500">
                    <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-white/20 flex items-center justify-center">
                            <Sparkles className="w-4 h-4 text-white" />
                        </div>
                        <div>
                            <h2 className="text-sm font-semibold text-white">Generate Proposal</h2>
                            <p className="text-xs text-white/70">AI-powered federal proposal drafting</p>
                        </div>
                    </div>
                    <button onClick={onClose} className="text-white/70 hover:text-white transition-colors">
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Step indicator */}
                <div className="flex gap-0 border-b border-border">
                    {(['select-opportunity', 'select-profile', 'confirm'] as Step[]).map((s, i) => (
                        <div
                            key={s}
                            className={`flex-1 py-2.5 text-center text-xs font-medium transition-colors ${step === s
                                    ? 'text-govblue-600 border-b-2 border-govblue-600 bg-govblue-50/50'
                                    : 'text-muted-foreground'
                                }`}
                        >
                            {i + 1}. {s === 'select-opportunity' ? 'Opportunity' : s === 'select-profile' ? 'Profile' : 'Generate'}
                        </div>
                    ))}
                </div>

                {/* Step content */}
                <div className="p-6 max-h-[60vh] overflow-y-auto scrollbar-thin">
                    {step === 'select-opportunity' && (
                        <div className="space-y-4 animate-fade-in">
                            <div className="relative">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                                <input
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    placeholder="Search opportunities by title, NAICS, or solicitation number…"
                                    className="w-full pl-9 pr-4 py-2.5 text-sm border border-border rounded-xl bg-background focus:outline-none focus:ring-2 focus:ring-govblue-500"
                                />
                            </div>

                            {oppsLoading ? (
                                <div className="space-y-2">
                                    {[1, 2, 3].map((i) => (
                                        <div key={i} className="h-16 rounded-xl shimmer-bg" />
                                    ))}
                                </div>
                            ) : opportunities?.items.length === 0 ? (
                                <div className="text-center py-8 text-muted-foreground">
                                    <Building2 className="w-10 h-10 mx-auto mb-2 opacity-30" />
                                    <p className="text-sm">No opportunities found.</p>
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        className="mt-2"
                                        onClick={() => ingestionApi.triggerSamgov()}
                                    >
                                        Trigger SAM.gov Sync
                                    </Button>
                                </div>
                            ) : (
                                <div className="space-y-2">
                                    {opportunities?.items.map((opp) => (
                                        <button
                                            key={opp.id}
                                            onClick={() => setSelectedOpportunityId(opp.id)}
                                            className={`w-full text-left p-4 rounded-xl border transition-all ${selectedOpportunityId === opp.id
                                                    ? 'border-govblue-500 bg-govblue-50 shadow-sm'
                                                    : 'border-border hover:border-govblue-300 hover:bg-accent/30'
                                                }`}
                                        >
                                            <div className="flex items-start justify-between gap-3">
                                                <div className="flex-1 min-w-0">
                                                    <p className="text-sm font-medium text-foreground truncate">{opp.title}</p>
                                                    <p className="text-xs text-muted-foreground mt-0.5">
                                                        {opp.agency} · Due {formatDate(opp.response_deadline)}
                                                    </p>
                                                </div>
                                                <div className="flex items-center gap-2 flex-shrink-0">
                                                    {opp.naics_code && (
                                                        <Badge variant="outline" className="text-xs">{opp.naics_code}</Badge>
                                                    )}
                                                    {selectedOpportunityId === opp.id && (
                                                        <CheckCircle className="w-4 h-4 text-govblue-600" />
                                                    )}
                                                </div>
                                            </div>
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    {step === 'select-profile' && (
                        <div className="space-y-4 animate-fade-in">
                            {!showProfileForm ? (
                                <>
                                    <p className="text-sm text-muted-foreground">
                                        Select a company profile or create a new one to match against this opportunity.
                                    </p>
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        className="w-full border-dashed"
                                        onClick={() => setShowProfileForm(true)}
                                    >
                                        <Plus className="w-4 h-4" />
                                        Create New Company Profile
                                    </Button>
                                </>
                            ) : (
                                <div className="space-y-3 animate-fade-in">
                                    <h3 className="text-sm font-semibold">Company Profile</h3>
                                    <ProfileField label="Company Name *" required>
                                        <input
                                            value={profileForm.company_name}
                                            onChange={(e) => setProfileForm({ ...profileForm, company_name: e.target.value })}
                                            placeholder="Acme Federal Solutions Inc."
                                            className="field-input"
                                        />
                                    </ProfileField>
                                    <ProfileField label="Capabilities Statement">
                                        <textarea
                                            value={profileForm.capabilities_statement}
                                            onChange={(e) => setProfileForm({ ...profileForm, capabilities_statement: e.target.value })}
                                            rows={4}
                                            placeholder="Describe your company's core capabilities, services, and expertise…"
                                            className="field-input"
                                        />
                                    </ProfileField>
                                    <ProfileField label="Past Performance">
                                        <textarea
                                            value={profileForm.past_performance}
                                            onChange={(e) => setProfileForm({ ...profileForm, past_performance: e.target.value })}
                                            rows={3}
                                            placeholder="List relevant government contracts, agencies served, and outcomes…"
                                            className="field-input"
                                        />
                                    </ProfileField>
                                    <ProfileField label="Certifications">
                                        <input
                                            value={profileForm.certifications}
                                            onChange={(e) => setProfileForm({ ...profileForm, certifications: e.target.value })}
                                            placeholder="ISO 9001, CMMI Level 3, ITAR, etc."
                                            className="field-input"
                                        />
                                    </ProfileField>
                                    <div className="grid grid-cols-2 gap-3">
                                        <ProfileField label="NAICS Codes">
                                            <input
                                                value={profileForm.naics_codes}
                                                onChange={(e) => setProfileForm({ ...profileForm, naics_codes: e.target.value })}
                                                placeholder="541512, 541519"
                                                className="field-input"
                                            />
                                        </ProfileField>
                                        <ProfileField label="Set-Asides">
                                            <input
                                                value={profileForm.set_asides}
                                                onChange={(e) => setProfileForm({ ...profileForm, set_asides: e.target.value })}
                                                placeholder="8A, SDVOSB, HUBZone"
                                                className="field-input"
                                            />
                                        </ProfileField>
                                        <ProfileField label="Location">
                                            <input
                                                value={profileForm.location}
                                                onChange={(e) => setProfileForm({ ...profileForm, location: e.target.value })}
                                                placeholder="Washington, DC"
                                                className="field-input"
                                            />
                                        </ProfileField>
                                        <ProfileField label="Years Experience">
                                            <input
                                                type="number"
                                                value={profileForm.years_experience}
                                                onChange={(e) => setProfileForm({ ...profileForm, years_experience: e.target.value })}
                                                placeholder="10"
                                                className="field-input"
                                            />
                                        </ProfileField>
                                    </div>
                                    <Button
                                        className="w-full"
                                        isLoading={createProfileMutation.isPending}
                                        disabled={!profileForm.company_name.trim()}
                                        onClick={() => createProfileMutation.mutate(profileForm)}
                                    >
                                        Save Profile & Continue
                                    </Button>
                                </div>
                            )}
                        </div>
                    )}

                    {step === 'confirm' && (
                        <div className="space-y-5 animate-fade-in">
                            <div className="rounded-xl border border-border p-4 space-y-3 bg-muted/30">
                                <h3 className="text-sm font-semibold">Ready to Generate</h3>
                                {selectedOpp && (
                                    <div className="text-sm text-foreground">
                                        <span className="text-muted-foreground text-xs">Opportunity:</span>
                                        <p className="font-medium mt-0.5 text-sm">{truncate(selectedOpp.title, 80)}</p>
                                    </div>
                                )}
                            </div>

                            <div>
                                <label className="text-xs font-medium text-muted-foreground block mb-2">Tone</label>
                                <div className="grid grid-cols-4 gap-2">
                                    {TONES.map((t) => (
                                        <button
                                            key={t.value}
                                            onClick={() => setSelectedTone(t.value)}
                                            className={`py-2 rounded-lg text-xs font-medium border transition-all ${selectedTone === t.value
                                                    ? 'bg-govblue-600 text-white border-govblue-600'
                                                    : 'border-border text-foreground hover:border-govblue-400'
                                                }`}
                                        >
                                            {t.label}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            <div className="bg-amber-50 border border-amber-200 rounded-xl p-3">
                                <p className="text-xs text-amber-700">
                                    <span className="font-semibold">Processing note:</span> Proposal generation typically takes 1-3 minutes. The AI will analyze the solicitation and match it with your company profile.
                                </p>
                            </div>
                        </div>
                    )}
                </div>

                {/* Modal footer */}
                <div className="px-6 py-4 border-t border-border flex items-center justify-between bg-muted/20">
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                            if (step === 'select-opportunity') onClose();
                            else if (step === 'select-profile') setStep('select-opportunity');
                            else setStep('select-profile');
                        }}
                    >
                        {step === 'select-opportunity' ? 'Cancel' : 'Back'}
                    </Button>

                    {step === 'select-opportunity' && (
                        <Button
                            size="sm"
                            disabled={!selectedOpportunityId}
                            onClick={() => setStep('select-profile')}
                        >
                            Next: Profile
                            <ChevronRight className="w-3.5 h-3.5" />
                        </Button>
                    )}

                    {step === 'select-profile' && !showProfileForm && (
                        <Button
                            size="sm"
                            disabled={!selectedProfileId}
                            onClick={() => setStep('confirm')}
                        >
                            Next: Confirm
                            <ChevronRight className="w-3.5 h-3.5" />
                        </Button>
                    )}

                    {step === 'confirm' && (
                        <Button
                            size="lg"
                            isLoading={generateMutation.isPending}
                            onClick={() => generateMutation.mutate()}
                            className="bg-govblue-600 hover:bg-govblue-700 text-white shadow-lg shadow-govblue-600/20"
                        >
                            <Sparkles className="w-4 h-4" />
                            Generate Proposal
                        </Button>
                    )}
                </div>
            </div>

            <style jsx>{`
        .field-input {
          width: 100%;
          padding: 8px 12px;
          border-radius: 8px;
          border: 1px solid hsl(var(--border));
          background: hsl(var(--background));
          font-size: 13px;
          outline: none;
          transition: box-shadow 0.15s;
        }
        .field-input:focus {
          box-shadow: 0 0 0 2px hsl(var(--ring));
        }
      `}</style>
        </div>
    );
}

function ProfileField({
    label,
    required,
    children,
}: {
    label: string;
    required?: boolean;
    children: React.ReactNode;
}) {
    return (
        <div>
            <label className="text-xs font-medium text-muted-foreground block mb-1">
                {label}
                {required && <span className="text-red-500 ml-0.5">*</span>}
            </label>
            {children}
        </div>
    );
}
