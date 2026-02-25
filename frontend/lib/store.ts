import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { UserProfile, Opportunity, Proposal } from './api';

interface ProposalState {
    // Active profile
    activeProfile: UserProfile | null;
    setActiveProfile: (profile: UserProfile | null) => void;

    // Selected opportunity
    selectedOpportunity: Opportunity | null;
    setSelectedOpportunity: (opp: Opportunity | null) => void;

    // Active proposal
    activeProposal: Proposal | null;
    setActiveProposal: (proposal: Proposal | null) => void;

    // UI state
    activeSection: string;
    setActiveSection: (section: string) => void;

    highlightedSource: string | null;
    setHighlightedSource: (sourceId: string | null) => void;

    isGenerating: boolean;
    setIsGenerating: (v: boolean) => void;

    isRefining: { [section: string]: boolean };
    setIsRefining: (section: string, v: boolean) => void;

    // Tone
    selectedTone: string;
    setSelectedTone: (tone: string) => void;

    // Reset
    reset: () => void;
}

export const useProposalStore = create<ProposalState>()(
    persist(
        (set) => ({
            activeProfile: null,
            setActiveProfile: (profile) => set({ activeProfile: profile }),

            selectedOpportunity: null,
            setSelectedOpportunity: (opp) => set({ selectedOpportunity: opp }),

            activeProposal: null,
            setActiveProposal: (proposal) => set({ activeProposal: proposal }),

            activeSection: 'executive_summary',
            setActiveSection: (section) => set({ activeSection: section }),

            highlightedSource: null,
            setHighlightedSource: (sourceId) => set({ highlightedSource: sourceId }),

            isGenerating: false,
            setIsGenerating: (v) => set({ isGenerating: v }),

            isRefining: {},
            setIsRefining: (section, v) =>
                set((state) => ({
                    isRefining: { ...state.isRefining, [section]: v },
                })),

            selectedTone: 'professional',
            setSelectedTone: (tone) => set({ selectedTone: tone }),

            reset: () =>
                set({
                    activeProposal: null,
                    selectedOpportunity: null,
                    activeSection: 'executive_summary',
                    highlightedSource: null,
                    isGenerating: false,
                    isRefining: {},
                }),
        }),
        {
            name: 'govpreneurs-proposal-store',
            partialize: (state) => ({
                activeProfile: state.activeProfile,
                selectedTone: state.selectedTone,
            }),
        },
    ),
);
