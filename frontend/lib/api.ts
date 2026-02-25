import axios from 'axios';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = axios.create({
    baseURL: `${API_BASE}/api/v1`,
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 60000,
});

// ── Types ─────────────────────────────────────────────────────────────────────

export interface Attachment {
    file_name: string;
    file_url: string;
    file_type: string;
}

export interface Opportunity {
    id: string;
    notice_id: string;
    title: string;
    description?: string;
    agency?: string;
    sub_agency?: string;
    department?: string;
    posted_date?: string;
    response_deadline?: string;
    archive_date?: string;
    last_modified_date?: string;
    notice_type?: string;
    solicitation_number?: string;
    naics_code?: string;
    naics_description?: string;
    set_aside_type?: string;
    place_of_performance?: string;
    contract_type?: string;
    estimated_value?: string;
    attachments?: Attachment[];
    full_text?: string;
    processed: boolean;
    active: boolean;
    created_at: string;
    updated_at: string;
}

export interface OpportunityListResponse {
    total: number;
    page: number;
    page_size: number;
    items: Opportunity[];
}

export interface UserProfile {
    id: string;
    company_name: string;
    capabilities_statement?: string;
    past_performance?: string;
    certifications?: string;
    naics_codes?: string[];
    set_asides?: string[];
    location?: string;
    years_experience?: number;
    created_at: string;
    updated_at: string;
}

export interface ProposalSource {
    chunk_id?: string;
    source_file?: string;
    chunk_index?: number;
    snippet?: string;
    citation: string;
    similarity?: number;
}

export interface ProposalSection {
    content: string;
    sources: ProposalSource[];
}

export interface ProposalSections {
    executive_summary?: ProposalSection;
    technical_approach?: ProposalSection;
    past_performance?: ProposalSection;
    compliance_matrix?: ProposalSection;
    company_overview?: ProposalSection;
    conclusion?: ProposalSection;
}

export interface Proposal {
    id: string;
    opportunity_id: string;
    user_profile_id: string;
    status: 'pending' | 'processing' | 'completed' | 'failed';
    sections?: ProposalSections;
    tone: string;
    version: number;
    task_id?: string;
    error_message?: string;
    created_at: string;
    updated_at: string;
}

export interface GenerateProposalRequest {
    opportunity_id: string;
    user_profile_id: string;
    tone?: string;
}

// ── API Functions ──────────────────────────────────────────────────────────────

// Opportunities
export const opportunitiesApi = {
    list: (params?: {
        page?: number;
        page_size?: number;
        naics_code?: string;
        set_aside_type?: string;
        active?: boolean;
        agency?: string;
        search?: string;
    }) => api.get<OpportunityListResponse>('/opportunities', { params }),

    get: (id: string) => api.get<Opportunity>(`/opportunities/${id}`),

    process: (id: string, force = false) =>
        api.post(`/opportunities/${id}/process`, null, { params: { force } }),
};

// User Profiles
export const profilesApi = {
    create: (data: Partial<UserProfile>) =>
        api.post<UserProfile>('/profiles', data),

    get: (id: string) => api.get<UserProfile>(`/profiles/${id}`),

    update: (id: string, data: Partial<UserProfile>) =>
        api.patch<UserProfile>(`/profiles/${id}`, data),
};

// Proposals
export const proposalsApi = {
    generate: (data: GenerateProposalRequest) =>
        api.post<{ proposal_id: string; status: string; task_id?: string }>(
            '/proposals/generate',
            data,
        ),

    get: (id: string) => api.get<Proposal>(`/proposals/${id}`),

    refine: (data: {
        proposal_id: string;
        section: string;
        instruction: string;
        tone?: string;
    }) => api.post<Proposal>('/proposals/refine', data),

    updateSection: (id: string, section: string, content: string) =>
        api.patch(`/proposals/${id}/section/${section}`, null, {
            params: { content },
        }),
};

// Ingestion
export const ingestionApi = {
    triggerSamgov: (maxPages = 5) =>
        api.post('/ingestion/trigger-samgov', null, { params: { max_pages: maxPages } }),
};
